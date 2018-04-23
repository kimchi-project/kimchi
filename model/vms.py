#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2017
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import copy
import libvirt
import lxml.etree as ET
import os
import paramiko
import platform
import pwd
import random
import signal
import socket
import subprocess
import string
import threading
import time
import uuid
from lxml import etree, objectify
from lxml.builder import E
from xml.etree import ElementTree

from wok import websocket
from wok.asynctask import AsyncTask
from wok.config import config
from wok.exception import InvalidOperation, InvalidParameter
from wok.exception import NotFoundError, OperationFailed
from wok.model.tasks import TaskModel
from wok.rollbackcontext import RollbackContext
from wok.utils import convert_data_size
from wok.utils import import_class, run_setfacl_set_attr, run_command, wok_log
from wok.xmlutils.utils import dictize, xpath_get_text, xml_item_insert
from wok.xmlutils.utils import xml_item_remove, xml_item_update

from wok.plugins.kimchi import model
from wok.plugins.kimchi import serialconsole
from wok.plugins.kimchi.config import READONLY_POOL_TYPE, get_kimchi_version
from wok.plugins.kimchi.kvmusertests import UserTests
from wok.plugins.kimchi.model.config import CapabilitiesModel
from wok.plugins.kimchi.model.cpuinfo import CPUInfoModel
from wok.plugins.kimchi.model.featuretests import FeatureTests
from wok.plugins.kimchi.model.templates import PPC_MEM_ALIGN
from wok.plugins.kimchi.model.templates import TemplateModel, validate_memory
from wok.plugins.kimchi.model.utils import get_ascii_nonascii_name, get_vm_name
from wok.plugins.kimchi.model.utils import get_metadata_node
from wok.plugins.kimchi.model.utils import remove_metadata_node
from wok.plugins.kimchi.model.utils import set_metadata_node
from wok.plugins.kimchi.osinfo import defaults, MEM_DEV_SLOTS
from wok.plugins.kimchi.screenshot import VMScreenshot
from wok.plugins.kimchi.utils import get_next_clone_name, is_s390x
from wok.plugins.kimchi.utils import template_name_from_uri
from wok.plugins.kimchi.xmlutils.bootorder import get_bootorder_node
from wok.plugins.kimchi.xmlutils.bootorder import get_bootmenu_node
from wok.plugins.kimchi.xmlutils.cpu import get_topology_xml
from wok.plugins.kimchi.xmlutils.disk import get_vm_disk_info, get_vm_disks
from utils import has_cpu_numa, set_numa_memory


DOM_STATE_MAP = {0: 'nostate',
                 1: 'running',
                 2: 'blocked',
                 3: 'paused',
                 4: 'shutdown',
                 5: 'shutoff',
                 6: 'crashed',
                 7: 'pmsuspended'}

# update parameters which are updatable when the VM is online
VM_ONLINE_UPDATE_PARAMS = ['cpu_info', 'graphics', 'groups',
                           'memory', 'users', 'autostart']

# update parameters which are updatable when the VM is offline
VM_OFFLINE_UPDATE_PARAMS = ['cpu_info', 'graphics', 'groups', 'memory',
                            'name', 'users', 'bootorder', 'bootmenu',
                            'description', 'title', 'console', 'autostart']

XPATH_DOMAIN_DISK = "/domain/devices/disk[@device='disk']/source/@file"
XPATH_DOMAIN_DISK_BY_FILE = "./devices/disk[@device='disk']/source[@file='%s']"
XPATH_DOMAIN_NAME = '/domain/name'
XPATH_DOMAIN_MAC = "/domain/devices/interface/mac/@address"
XPATH_DOMAIN_MAC_BY_ADDRESS = "./devices/interface/mac[@address='%s']"
XPATH_DOMAIN_MEMORY = '/domain/memory'
XPATH_DOMAIN_MEMORY_UNIT = '/domain/memory/@unit'
XPATH_DOMAIN_UUID = '/domain/uuid'
XPATH_DOMAIN_DEV_CPU_ID = '/domain/devices/spapr-cpu-socket/@id'
XPATH_DOMAIN_CONSOLE_TARGET = "/domain/devices/console/target/@type"

XPATH_BOOT = 'os/boot/@dev'
XPATH_BOOTMENU = 'os/bootmenu/@enable'
XPATH_CPU = './cpu'
XPATH_DESCRIPTION = './description'
XPATH_MEMORY = './memory'
XPATH_NAME = './name'
XPATH_NUMA_CELL = './cpu/numa/cell'
XPATH_SNAP_VM_NAME = './domain/name'
XPATH_SNAP_VM_UUID = './domain/uuid'
XPATH_TITLE = './title'
XPATH_TOPOLOGY = './cpu/topology'
XPATH_VCPU = './vcpu'
XPATH_MAX_MEMORY = './maxMemory'
XPATH_CONSOLE_TARGET = "./devices/console/target"

# key: VM name; value: lock object
vm_locks = {}


class VMsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.caps = CapabilitiesModel(**kargs)
        self.task = TaskModel(**kargs)

    def create(self, params):
        t_name = template_name_from_uri(params['template'])
        vm_list = self.get_list()
        name = get_vm_name(params.get('name'), t_name, vm_list)
        # incoming text, from js json, is unicode, do not need decode
        if name in vm_list:
            raise InvalidOperation("KCHVM0001E", {'name': name})

        vm_overrides = dict()
        pool_uri = params.get('storagepool')
        if pool_uri:
            vm_overrides['storagepool'] = pool_uri
            vm_overrides['fc_host_support'] = self.caps.fc_host_support
        t = TemplateModel.get_template(t_name, self.objstore, self.conn,
                                       vm_overrides)

        if not self.caps.qemu_stream and t.info.get('iso_stream', False):
            raise InvalidOperation("KCHVM0005E")

        t.validate()
        data = {'name': name, 'template': t,
                'graphics': params.get('graphics', {}),
                "title": params.get("title", ""),
                "description": params.get("description", "")}
        taskid = AsyncTask(u'/plugins/kimchi/vms/%s' % name, self._create_task,
                           data).id

        return self.task.lookup(taskid)

    def _create_task(self, cb, params):
        """
        params: A dict with the following values:
            - vm_uuid: The UUID of the VM being created
            - template: The template being used to create the VM
            - name: The name for the new VM
        """
        vm_uuid = str(uuid.uuid4())
        title = params.get('title', '')
        description = params.get('description', '')
        t = params['template']
        name, nonascii_name = get_ascii_nonascii_name(params['name'])
        conn = self.conn.get()

        cb('Storing VM icon')
        # Store the icon for displaying later
        icon = t.info.get('icon')
        if icon:
            try:
                with self.objstore as session:
                    session.store('vm', vm_uuid, {'icon': icon},
                                  get_kimchi_version())
            except Exception as e:
                # It is possible to continue Kimchi executions without store
                # vm icon info
                wok_log.error('Error trying to update database with guest '
                              'icon information due error: %s', e.message)

        cb('Provisioning storages for new VM')
        vol_list = t.fork_vm_storage(vm_uuid)

        graphics = params.get('graphics', {})
        stream_protocols = self.caps.libvirt_stream_protocols
        xml = t.to_vm_xml(name, vm_uuid,
                          libvirt_stream_protocols=stream_protocols,
                          graphics=graphics,
                          mem_hotplug_support=self.caps.mem_hotplug_support,
                          title=title, description=description)

        cb('Defining new VM')
        try:
            conn.defineXML(xml.encode('utf-8'))
        except libvirt.libvirtError as e:
            for v in vol_list:
                vol = conn.storageVolLookupByPath(v['path'])
                vol.delete(0)
            raise OperationFailed("KCHVM0007E", {'name': name,
                                                 'err': e.get_error_message()})

        cb('Updating VM metadata')
        meta_elements = []

        distro = t.info.get("os_distro")
        version = t.info.get("os_version")
        if distro is not None:
            meta_elements.append(E.os({"distro": distro, "version": version}))

        if nonascii_name is not None:
            meta_elements.append(E.name(nonascii_name))

        set_metadata_node(VMModel.get_vm(name, self.conn), meta_elements)
        cb('OK', True)

    def get_list(self):
        return VMsModel.get_vms(self.conn)

    @staticmethod
    def get_vms(conn):
        conn_ = conn.get()
        names = []
        for dom in conn_.listAllDomains(0):
            nonascii_xml = get_metadata_node(dom, 'name')
            if nonascii_xml:
                nonascii_node = ET.fromstring(nonascii_xml)
                names.append(nonascii_node.text)
            else:
                names.append(dom.name().decode('utf-8'))
        names = sorted(names, key=unicode.lower)
        return names


class VMModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.caps = CapabilitiesModel(**kargs)
        self.vmscreenshot = VMScreenshotModel(**kargs)
        self.users = import_class(
            'plugins.kimchi.model.users.UsersModel'
        )(**kargs)
        self.groups = import_class(
            'plugins.kimchi.model.groups.GroupsModel'
        )(**kargs)
        self.vms = VMsModel(**kargs)
        self.task = TaskModel(**kargs)
        self.storagepool = model.storagepools.StoragePoolModel(**kargs)
        self.storagevolume = model.storagevolumes.StorageVolumeModel(**kargs)
        self.storagevolumes = model.storagevolumes.StorageVolumesModel(**kargs)
        cls = import_class('plugins.kimchi.model.vmsnapshots.VMSnapshotModel')
        self.vmsnapshot = cls(**kargs)
        cls = import_class('plugins.kimchi.model.vmsnapshots.VMSnapshotsModel')
        self.vmsnapshots = cls(**kargs)
        self.stats = {}
        self._serial_procs = []

    def has_topology(self, dom):
        xml = dom.XMLDesc(0)
        sockets = xpath_get_text(xml, XPATH_TOPOLOGY + '/@sockets')
        cores = xpath_get_text(xml, XPATH_TOPOLOGY + '/@cores')
        threads = xpath_get_text(xml, XPATH_TOPOLOGY + '/@threads')
        return sockets and cores and threads

    def update(self, name, params):
        if platform.machine() not in ['s390x', 's390'] and\
           'console' in params:
            raise InvalidParameter('KCHVM0087E')
        lock = vm_locks.get(name)
        if lock is None:
            lock = threading.Lock()
            vm_locks[name] = lock

        with lock:
            dom = self.get_vm(name, self.conn)
            if "autostart" in params:
                dom.setAutostart(1 if params['autostart'] is True else 0)

            # You can only change <maxMemory> offline, updating guest XML
            if ("memory" in params) and ('maxmemory' in params['memory']) and\
               (DOM_STATE_MAP[dom.info()[0]] != 'shutoff'):
                raise InvalidParameter("KCHVM0080E")

            if DOM_STATE_MAP[dom.info()[0]] == 'shutoff':
                ext_params = set(params.keys()) - set(VM_OFFLINE_UPDATE_PARAMS)
                if len(ext_params) > 0:
                    raise InvalidParameter('KCHVM0073E',
                                           {'params': ', '.join(ext_params)})
            else:
                ext_params = set(params.keys()) - set(VM_ONLINE_UPDATE_PARAMS)
                if len(ext_params) > 0:
                    raise InvalidParameter('KCHVM0074E',
                                           {'params': ', '.join(ext_params)})

            # METADATA can be updated offline or online
            self._vm_update_access_metadata(dom, params)

            # GRAPHICS can be updated offline or online
            if 'graphics' in params:

                # some parameters cannot change while vm is running
                if DOM_STATE_MAP[dom.info()[0]] != 'shutoff':
                    if 'type' in params['graphics']:
                        raise InvalidParameter('KCHVM0074E',
                                               {'params': 'graphics type'})
                dom = self._update_graphics(dom, params)

            # Live updates
            if dom.isActive():
                self._live_vm_update(dom, params)

            vm_name = name
            if (DOM_STATE_MAP[dom.info()[0]] == 'shutoff'):
                vm_name, dom = self._static_vm_update(name, dom, params)
            return vm_name

    def clone(self, name):
        """Clone a virtual machine based on an existing one.

        The new virtual machine will have the exact same configuration as the
        original VM, except for the name, UUID, MAC addresses and disks. The
        name will have the form "<name>-clone-<number>", with <number> starting
        at 1; the UUID will be generated randomly; the MAC addresses will be
        generated randomly with no conflicts within the original and the new
        VM; and the disks will be new volumes [mostly] on the same storage
        pool, with the same content as the original disks. The storage pool
        'default' will always be used when cloning SCSI and iSCSI disks and
        when the original storage pool cannot hold the new volume.

        An exception will be raised if the virtual machine <name> is not
        shutoff, if there is no available space to copy a new volume to the
        storage pool 'default' (when there was also no space to copy it to the
        original storage pool) and if one of the virtual machine's disks belong
        to a storage pool not supported by Kimchi.

        Parameters:
        name -- The name of the existing virtual machine to be cloned.

        Return:
        A Task running the clone operation.
        """
        # VM must be shutoff in order to clone it
        info = self.lookup(name)
        if info['state'] != u'shutoff':
            raise InvalidParameter('KCHVM0033E', {'name': name})

        # the new VM's name will be used as the Task's 'target_uri' so it needs
        # to be defined now.

        vms_being_created = []

        # lookup names of VMs being created right now
        with self.objstore as session:
            task_names = session.get_list('task')
            for tn in task_names:
                t = session.get('task', tn)
                if t['target_uri'].startswith('/plugins/kimchi/vms/'):
                    uri_name = t['target_uri'].lstrip('/plugins/kimchi/vms/')
                    vms_being_created.append(uri_name)

        current_vm_names = self.vms.get_list() + vms_being_created
        new_name = get_next_clone_name(current_vm_names, name, ts=True)

        # create a task with the actual clone function
        taskid = AsyncTask(u'/plugins/kimchi/vms/%s/clone' % new_name,
                           self._clone_task, {'name': name,
                                              'new_name': new_name}).id

        return self.task.lookup(taskid)

    def _clone_task(self, cb, params):
        """Asynchronous function which performs the clone operation.

        Parameters:
        cb -- A callback function to signal the Task's progress.
        params -- A dict with the following values:
            "name": the name of the original VM.
            "new_name": the name of the new VM.
        """
        name = params['name']
        new_name = params['new_name']

        # fetch base XML
        cb('reading source VM XML')
        try:
            vir_dom = self.get_vm(name, self.conn)
            flags = libvirt.VIR_DOMAIN_XML_SECURE
            xml = vir_dom.XMLDesc(flags).decode('utf-8')
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHVM0035E', {'name': name,
                                                 'err': e.message})

        # update UUID
        cb('updating VM UUID')
        old_uuid = xpath_get_text(xml, XPATH_DOMAIN_UUID)[0]
        new_uuid = unicode(uuid.uuid4())
        xml = xml_item_update(xml, './uuid', new_uuid)

        # update MAC addresses
        cb('updating VM MAC addresses')
        xml = self._clone_update_mac_addresses(xml)

        with RollbackContext() as rollback:
            # copy disks
            cb('copying VM disks')
            xml = self._clone_update_disks(xml, rollback)

            # update objstore entry
            cb('updating object store')
            self._clone_update_objstore(old_uuid, new_uuid, rollback)

            # update name
            cb('updating VM name')
            new_name, nonascii_name = get_ascii_nonascii_name(new_name)
            xml = xml_item_update(xml, './name', new_name)

            # create new guest
            cb('defining new VM')
            try:
                vir_conn = self.conn.get()
                dom = vir_conn.defineXML(xml)
                self._update_metadata_name(dom, nonascii_name)
            except libvirt.libvirtError, e:
                raise OperationFailed('KCHVM0035E', {'name': name,
                                                     'err': e.message})

            rollback.commitAll()

        cb('OK', True)

    @staticmethod
    def _clone_update_mac_addresses(xml):
        """Update the MAC addresses with new values in the XML descriptor of a
        cloning domain.

        The new MAC addresses will be generated randomly, and their values are
        guaranteed to be distinct from the ones in the original VM.

        Arguments:
        xml -- The XML descriptor of the original domain.

        Return:
        The XML descriptor <xml> with the new MAC addresses instead of the
        old ones.
        """
        old_macs = xpath_get_text(xml, XPATH_DOMAIN_MAC)
        new_macs = []

        for mac in old_macs:
            while True:
                new_mac = model.vmifaces.VMIfacesModel.random_mac()
                # make sure the new MAC doesn't conflict with the original VM
                # and with the new values on the new VM.
                if new_mac not in (old_macs + new_macs):
                    new_macs.append(new_mac)
                    break

            xml = xml_item_update(xml, XPATH_DOMAIN_MAC_BY_ADDRESS % mac,
                                  new_mac, 'address')

        return xml

    def _clone_update_disks(self, xml, rollback):
        """Clone disks from a virtual machine. The disks are copied as new
        volumes and the new VM's XML is updated accordingly.

        Arguments:
        xml -- The XML descriptor of the original VM + new value for
            "/domain/uuid".
        rollback -- A rollback context so the new volumes can be removed if an
            error occurs during the cloning operation.

        Return:
        The XML descriptor <xml> with the new disk paths instead of the
        old ones.
        """
        # the UUID will be used to create the disk paths
        uuid = xpath_get_text(xml, XPATH_DOMAIN_UUID)[0]
        all_paths = xpath_get_text(xml, XPATH_DOMAIN_DISK)

        vir_conn = self.conn.get()
        domain_name = xpath_get_text(xml, XPATH_DOMAIN_NAME)[0]

        for i, path in enumerate(all_paths):
            try:
                vir_orig_vol = vir_conn.storageVolLookupByPath(path)
                vir_pool = vir_orig_vol.storagePoolLookupByVolume()

                orig_pool_name = vir_pool.name().decode('utf-8')
                orig_vol_name = vir_orig_vol.name().decode('utf-8')
            except libvirt.libvirtError, e:
                raise OperationFailed('KCHVM0035E', {'name': domain_name,
                                                     'err': e.message})

            orig_pool = self.storagepool.lookup(orig_pool_name)
            orig_vol = self.storagevolume.lookup(orig_pool_name, orig_vol_name)

            new_pool_name = orig_pool_name
            new_pool = orig_pool

            if orig_pool['type'] in ['dir', 'netfs', 'logical']:
                # if a volume in a pool 'dir', 'netfs' or 'logical' cannot hold
                # a new volume with the same size, the pool 'default' should
                # be used
                if orig_vol['capacity'] > orig_pool['available']:
                    wok_log.warning('storage pool \'%s\' doesn\'t have '
                                    'enough free space to store image '
                                    '\'%s\'; falling back to \'default\'',
                                    orig_pool_name, path)
                    new_pool_name = u'default'
                    new_pool = self.storagepool.lookup(u'default')

                    # ...and if even the pool 'default' cannot hold a new
                    # volume, raise an exception
                    if orig_vol['capacity'] > new_pool['available']:
                        domain_name = xpath_get_text(xml, XPATH_DOMAIN_NAME)[0]
                        raise InvalidOperation('KCHVM0034E',
                                               {'name': domain_name})

            elif orig_pool['type'] in ['scsi', 'iscsi']:
                # SCSI and iSCSI always fall back to the storage pool 'default'
                wok_log.warning('cannot create new volume for clone in '
                                'storage pool \'%s\'; falling back to '
                                '\'default\'', orig_pool_name)
                new_pool_name = u'default'
                new_pool = self.storagepool.lookup(u'default')

                # if the pool 'default' cannot hold a new volume, raise
                # an exception
                if orig_vol['capacity'] > new_pool['available']:
                    domain_name = xpath_get_text(xml, XPATH_DOMAIN_NAME)[0]
                    raise InvalidOperation('KCHVM0034E', {'name': domain_name})

            else:
                # unexpected storage pool type
                raise InvalidOperation('KCHPOOL0014E',
                                       {'type': orig_pool['type']})

            # new volume name: <UUID>-<loop-index>.<original extension>
            # e.g. 1234-5678-9012-3456-0.img
            ext = os.path.splitext(path)[1]
            new_vol_name = u'%s-%d%s' % (uuid, i, ext)
            task = self.storagevolume.clone(orig_pool_name, orig_vol_name,
                                            new_name=new_vol_name)
            self.task.wait(task['id'], 3600)  # 1 h

            # get the new volume path and update the XML descriptor
            new_vol = self.storagevolume.lookup(new_pool_name, new_vol_name)
            xml = xml_item_update(xml, XPATH_DOMAIN_DISK_BY_FILE % path,
                                  new_vol['path'], 'file')

            # remove the new volume should an error occur later
            rollback.prependDefer(self.storagevolume.delete, new_pool_name,
                                  new_vol_name)

        return xml

    def _clone_update_objstore(self, old_uuid, new_uuid, rollback):
        """Update Kimchi's object store with the cloning VM.

        Arguments:
        old_uuid -- The UUID of the original VM.
        new_uuid -- The UUID of the new, clonning VM.
        rollback -- A rollback context so the object store entry can be removed
            if an error occurs during the cloning operation.
        """
        with self.objstore as session:
            try:
                vm = session.get('vm', old_uuid)
                icon = vm['icon']
                session.store('vm', new_uuid, {'icon': icon},
                              get_kimchi_version())
            except NotFoundError:
                # if we cannot find an object store entry for the original VM,
                # don't store one with an empty value.
                pass
            else:
                # we need to define a custom function to prepend to the
                # rollback context because the object store session needs to be
                # opened and closed correctly (i.e. "prependDefer" only
                # accepts one command at a time but we need more than one to
                # handle an object store).
                def _rollback_objstore():
                    with self.objstore as session_rb:
                        session_rb.delete('vm', new_uuid, ignore_missing=True)

                # remove the new object store entry should an error occur later
                rollback.prependDefer(_rollback_objstore)

    def _build_access_elem(self, dom, users, groups):
        auth = config.get("authentication", "method")
        access_xml = get_metadata_node(dom, "access")

        auth_elem = None

        if not access_xml:
            # there is no metadata element 'access'
            access_elem = E.access()
        else:
            access_elem = ET.fromstring(access_xml)

            same_auth = access_elem.xpath('./auth[@type="%s"]' % auth)
            if len(same_auth) > 0:
                # there is already a sub-element 'auth' with the same type;
                # update it.
                auth_elem = same_auth[0]

                if users is not None:
                    for u in auth_elem.findall('user'):
                        auth_elem.remove(u)

                if groups is not None:
                    for g in auth_elem.findall('group'):
                        auth_elem.remove(g)

        if auth_elem is None:
            # there is no sub-element 'auth' with the same type
            # (or no 'auth' at all); create it.
            auth_elem = E.auth(type=auth)
            access_elem.append(auth_elem)

        if users is not None:
            for u in users:
                auth_elem.append(E.user(u))

        if groups is not None:
            for g in groups:
                auth_elem.append(E.group(g))

        return access_elem

    def _vm_update_access_metadata(self, dom, params):
        users = groups = None
        if "users" in params:
            users = params["users"]
            for user in users:
                if not self.users.validate(user):
                    raise InvalidParameter("KCHVM0027E",
                                           {'users': user})
        if "groups" in params:
            groups = params["groups"]
            for group in groups:
                if not self.groups.validate(group):
                    raise InvalidParameter("KCHVM0028E",
                                           {'groups': group})

        if users is None and groups is None:
            return

        node = self._build_access_elem(dom, users, groups)
        set_metadata_node(dom, [node])

    def _get_access_info(self, dom):
        users = groups = list()
        access_xml = (get_metadata_node(dom, "access") or
                      """<access></access>""")
        access_info = dictize(access_xml)
        auth = config.get("authentication", "method")
        if ('auth' in access_info['access'] and
                ('type' in access_info['access']['auth'] or
                 len(access_info['access']['auth']) > 1)):
            users = xpath_get_text(access_xml,
                                   "/access/auth[@type='%s']/user" % auth)
            groups = xpath_get_text(access_xml,
                                    "/access/auth[@type='%s']/group" % auth)
        elif auth == 'pam':
            # Compatible to old permission tagging
            users = xpath_get_text(access_xml, "/access/user")
            groups = xpath_get_text(access_xml, "/access/group")
        return users, groups

    @staticmethod
    def vm_get_os_metadata(dom):
        os_xml = (get_metadata_node(dom, "os") or
                  """<os></os>""")
        os_elem = ET.fromstring(os_xml)
        return (os_elem.attrib.get("version"), os_elem.attrib.get("distro"))

    def _update_graphics(self, dom, params):
        root = objectify.fromstring(dom.XMLDesc(0))
        graphics = root.devices.find("graphics")
        if graphics is None:
            return dom

        password = params['graphics'].get("passwd")
        if password is not None and len(password.strip()) == 0:
            password = "".join(random.sample(string.ascii_letters +
                                             string.digits, 8))

        if password is not None:
            graphics.attrib['passwd'] = password

        expire = params['graphics'].get("passwdValidTo")
        to = graphics.attrib.get('passwdValidTo')
        if to is not None:
            if (time.mktime(time.strptime(to, '%Y-%m-%dT%H:%M:%S')) -
               time.time() <= 0):
                expire = expire if expire is not None else 30

        if expire is not None:
            expire_time = time.gmtime(time.time() + float(expire))
            valid_to = time.strftime('%Y-%m-%dT%H:%M:%S', expire_time)
            graphics.attrib['passwdValidTo'] = valid_to

        gtype = params['graphics'].get('type')
        if gtype is not None:
            graphics.attrib['type'] = gtype

        conn = self.conn.get()
        if not dom.isActive():
            return conn.defineXML(ET.tostring(root, encoding="utf-8"))

        xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        dom.updateDeviceFlags(etree.tostring(graphics),
                              libvirt.VIR_DOMAIN_AFFECT_LIVE)
        return conn.defineXML(xml)

    def _backup_snapshots(self, snap, all_info):
        """ Append "snap" and the children of "snap" to the list "all_info".

        The list *must* always contain the parent snapshots before their
        children so the function "_redefine_snapshots" can work correctly.

        Arguments:
        snap -- a native domain snapshot.
        all_info -- a list of dict keys:
                "{'xml': <snap XML>, 'current': <is snap current?>'}"
        """
        all_info.append({'xml': snap.getXMLDesc(0),
                         'current': snap.isCurrent(0)})

        for child in snap.listAllChildren(0):
            self._backup_snapshots(child, all_info)

    def _redefine_snapshots(self, dom, all_info):
        """ Restore the snapshots stored in "all_info" to the domain "dom".

        Arguments:
        dom -- the domain which will have its snapshots restored.
        all_info -- a list of dict keys, as described in "_backup_snapshots",
            containing the original snapshot information.
        """
        for info in all_info:
            flags = libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_REDEFINE

            if info['current']:
                flags |= libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_CURRENT

            # Snapshot XML contains the VM xml from the time it was created.
            # Thus VM name and uuid must be updated to current ones. Otherwise,
            # when reverted, the vm name will be inconsistent.
            name = dom.name().decode('utf-8')
            uuid = dom.UUIDString().decode('utf-8')
            xml = xml_item_update(info['xml'], XPATH_SNAP_VM_NAME, name, None)
            xml = xml_item_update(xml, XPATH_SNAP_VM_UUID, uuid, None)

            dom.snapshotCreateXML(xml, flags)

    def _update_metadata_name(self, dom, nonascii_name):
        if nonascii_name is not None:
            set_metadata_node(dom, [E.name(nonascii_name)])
        else:
            remove_metadata_node(dom, 'name')

    def _update_bootorder(self, xml, params):
        # get element tree from xml
        et = ET.fromstring(xml)

        # get machine type
        os = et.find("os")

        # add new bootorder
        if "bootorder" in params:

            # remove old order
            [os.remove(device) for device in os.findall("boot")]

            for device in get_bootorder_node(params["bootorder"]):
                os.append(device)

        # update bootmenu
        if params.get("bootmenu") is False:
            [os.remove(bm) for bm in os.findall("bootmenu")]
        elif params.get("bootmenu") is True:
            os.append(get_bootmenu_node())

        # update <os>
        return ET.tostring(et)

    def _update_s390x_console(self, xml, params):
        if xpath_get_text(xml, XPATH_DOMAIN_CONSOLE_TARGET):
            # if console is defined, update console
            return xml_item_update(xml, XPATH_CONSOLE_TARGET,
                                   params.get('console'), 'type')
        # if console is not defined earlier, add console
        console = E.console(type="pty")
        console.append(E.target(type=params.get('console'), port='0'))
        et = ET.fromstring(xml)
        devices = et.find('devices')
        devices.append(console)
        return ET.tostring(et)

    def _static_vm_update(self, vm_name, dom, params):
        old_xml = new_xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        params = copy.deepcopy(params)

        # Update name
        name = params.get('name')
        nonascii_name = None

        if name is not None:
            name, nonascii_name = get_ascii_nonascii_name(name)
            new_xml = xml_item_update(new_xml, XPATH_NAME, name, None)

        if 'title' in params:
            if len(xpath_get_text(new_xml, XPATH_TITLE)) > 0:
                new_xml = xml_item_update(new_xml, XPATH_TITLE,
                                          params['title'], None)
            else:
                et = ET.fromstring(new_xml)
                et.append(E.title(params["title"]))
                new_xml = ET.tostring(et)

        if 'description' in params:
            if len(xpath_get_text(new_xml, XPATH_DESCRIPTION)) > 0:
                new_xml = xml_item_update(new_xml, XPATH_DESCRIPTION,
                                          params['description'], None)
            else:
                et = ET.fromstring(new_xml)
                et.append(E.description(params["description"]))
                new_xml = ET.tostring(et)

        # Update CPU info
        cpu_info = params.get('cpu_info', {})
        cpu_info = self._update_cpu_info(new_xml, dom, cpu_info)

        vcpus = str(cpu_info['vcpus'])
        new_xml = xml_item_update(new_xml, XPATH_VCPU, vcpus, 'current')

        maxvcpus = str(cpu_info['maxvcpus'])
        new_xml = xml_item_update(new_xml, XPATH_VCPU, maxvcpus, None)

        topology = cpu_info['topology']
        if topology:
            sockets = str(topology['sockets'])
            cores = str(topology['cores'])
            threads = str(topology['threads'])

            if self.has_topology(dom):
                # topology is being updated
                xpath = XPATH_TOPOLOGY
                new_xml = xml_item_update(new_xml, xpath, sockets, 'sockets')
                new_xml = xml_item_update(new_xml, xpath, cores, 'cores')
                new_xml = xml_item_update(new_xml, xpath, threads, 'threads')
            else:
                # topology is being added
                new_xml = xml_item_insert(new_xml, XPATH_CPU,
                                          get_topology_xml(topology))
        elif self.has_topology(dom):
            # topology is being undefined: remove it
            new_xml = xml_item_remove(new_xml, XPATH_TOPOLOGY)

        # Updating memory
        if ('memory' in params and params['memory'] != {}):
            new_xml = self._update_memory_config(new_xml, params, dom)

        # update bootorder or bootmenu
        if "bootorder" in params or "bootmenu" in params:
            new_xml = self._update_bootorder(new_xml, params)

        if platform.machine() in ['s390', 's390x'] and params.get('console'):
            new_xml = self._update_s390x_console(new_xml, params)

        snapshots_info = []
        conn = self.conn.get()
        try:
            if 'name' in params:
                lflags = libvirt.VIR_DOMAIN_SNAPSHOT_LIST_ROOTS
                dflags = (libvirt.VIR_DOMAIN_SNAPSHOT_DELETE_CHILDREN |
                          libvirt.VIR_DOMAIN_SNAPSHOT_DELETE_METADATA_ONLY)

                for virt_snap in dom.listAllSnapshots(lflags):
                    snapshots_info.append({'xml': virt_snap.getXMLDesc(0),
                                           'current': virt_snap.isCurrent(0)})
                    self._backup_snapshots(virt_snap, snapshots_info)

                    virt_snap.delete(dflags)

                # Undefine old vm, only if name is going to change
                dom.undefine()

            dom = conn.defineXML(new_xml)
            self._update_metadata_name(dom, nonascii_name)
            if 'name' in params:
                self._redefine_snapshots(dom, snapshots_info)
        except libvirt.libvirtError as e:
            dom = conn.defineXML(old_xml)
            if 'name' in params:
                self._redefine_snapshots(dom, snapshots_info)

            raise OperationFailed("KCHVM0008E", {'name': vm_name,
                                                 'err': e.get_error_message()})
        if name is not None:
            vm_name = name
        return (nonascii_name if nonascii_name is not None else vm_name, dom)

    def _update_memory_config(self, xml, params, dom):
        # Cannot pass max memory if there is not support to memory hotplug
        # Then set max memory as memory, just to continue with the update
        if not self.caps.mem_hotplug_support:
            if 'maxmemory' in params['memory']:
                raise InvalidOperation("KCHVM0046E")
            else:
                params['memory']['maxmemory'] = params['memory']['current']

        root = ET.fromstring(xml)
        # MiB to KiB
        hasMem = 'current' in params['memory']
        hasMaxMem = 'maxmemory' in params['memory']
        oldMem = int(xpath_get_text(xml, XPATH_DOMAIN_MEMORY)[0]) >> 10
        maxMemTag = root.find(XPATH_MAX_MEMORY)
        if maxMemTag is not None:
            oldMaxMem = int(xpath_get_text(xml, XPATH_MAX_MEMORY)[0]) >> 10
        else:
            oldMaxMem = oldMem
        newMem = (params['memory'].get('current', oldMem)) << 10
        newMaxMem = (params['memory'].get('maxmemory', oldMaxMem)) << 10

        validate_memory({'current': newMem >> 10,
                         'maxmemory': newMaxMem >> 10})

        # Adjust memory devices to new memory, if necessary
        memDevs = root.findall('./devices/memory')
        memDevsAmount = self._get_mem_dev_total_size(ET.tostring(root))

        if len(memDevs) != 0 and hasMem:
            if newMem > (oldMem << 10):
                newMem = newMem - memDevsAmount
            elif newMem < (oldMem << 10):
                memDevs.reverse()
                totRemoved = 0
                for dev in memDevs:
                    size = dev.find('./target/size')
                    totRemoved += int(convert_data_size(size.text,
                                                        size.get('unit'),
                                                        'KiB'))
                    root.find('./devices').remove(dev)
                    if ((oldMem << 10) - totRemoved) <= newMem:
                        newMem = newMem - self._get_mem_dev_total_size(
                            ET.tostring(root))
                        break
            elif newMem == (oldMem << 10):
                newMem = newMem - memDevsAmount

        # There is an issue in Libvirt/Qemu, where Guest does not start if
        # memory and max memory are the same. So we decided to remove max
        # memory and only add it if user explicitly provides it, willing to
        # do memory hotplug
        if hasMaxMem:
            # Conditions:
            if (maxMemTag is None) and (newMem != newMaxMem):
                # Creates the maxMemory tag
                max_mem_xml = E.maxMemory(
                    str(newMaxMem),
                    unit='Kib',
                    slots=str(defaults['mem_dev_slots']))
                root.insert(0, max_mem_xml)
            elif (maxMemTag is None) and (newMem == newMaxMem):
                # Nothing to do
                pass
            elif (maxMemTag is not None) and (newMem != newMaxMem):
                # Just update value in max memory tag
                maxMemTag.text = str(newMaxMem)
            elif (maxMemTag is not None) and (newMem == newMaxMem):
                if self._get_mem_dev_total_size(ET.tostring(root)) == 0:
                    # Remove the tag
                    root.remove(maxMemTag)
                else:
                    maxMemTag.text = str(newMaxMem)

        # Update memory, if necessary
        if hasMem:
            # Remove currentMemory, automatically set later by libvirt, with
            # memory value
            currentMem = root.find('.currentMemory')
            if currentMem is not None:
                root.remove(currentMem)

            memory = root.find('.memory')
            # Set NUMA parameterers if necessary. NUMA is not required for CPU
            # and Memory hotplug anymore on PowerPC systems
            if has_cpu_numa(dom):
                if memory is not None:
                    # Libvirt is going to set the value automatically with
                    # the value configured in NUMA tag
                    root.remove(memory)
                root = set_numa_memory(newMem, root)
            else:
                # update the memory tag directly
                if memory is not None:
                    memory.text = str(newMem)

            if (maxMemTag is not None) and (not hasMaxMem):
                if (newMem == newMaxMem and
                   (self._get_mem_dev_total_size(ET.tostring(root)) == 0)):
                    root.remove(maxMemTag)

        # Setting memory hard limit to max_memory + 1GiB
        memtune = root.find('memtune')
        if memtune is not None:
            hl = memtune.find('hard_limit')
            if hl is not None:
                memtune.remove(hl)
                memtune.insert(0, E.hard_limit(str(newMaxMem + 1048576),
                                               unit='Kib'))
        return ET.tostring(root, encoding="utf-8")

    def get_vm_cpu_cores(self, vm_xml):
        return xpath_get_text(vm_xml, XPATH_TOPOLOGY + '/@cores')[0]

    def get_vm_cpu_sockets(self, vm_xml):
        return xpath_get_text(vm_xml, XPATH_TOPOLOGY + '/@sockets')[0]

    def get_vm_cpu_threads(self, vm_xml):
        return xpath_get_text(vm_xml, XPATH_TOPOLOGY + '/@threads')[0]

    def get_vm_cpu_topology(self, dom):
        topology = {}
        if self.has_topology(dom):
            sockets = int(self.get_vm_cpu_sockets(dom.XMLDesc(0)))
            cores = int(self.get_vm_cpu_cores(dom.XMLDesc(0)))
            threads = int(self.get_vm_cpu_threads(dom.XMLDesc(0)))

            topology = {
                'sockets': sockets,
                'cores': cores,
                'threads': threads,
            }

        return topology

    def _update_cpu_info(self, new_xml, dom, new_info):
        topology = self.get_vm_cpu_topology(dom)

        # if current is not defined in vcpu, vcpus is equal to maxvcpus
        xml_maxvcpus = xpath_get_text(new_xml, 'vcpu')
        maxvcpus = int(xml_maxvcpus[0])
        xml_vcpus = xpath_get_text(new_xml, './vcpu/@current')
        vcpus = int(xml_vcpus[0]) if xml_vcpus else maxvcpus

        cpu_info = {
            'maxvcpus': maxvcpus,
            'vcpus': vcpus,
            'topology': topology,
        }
        cpu_info.update(new_info)

        # Revalidate cpu info - may raise CPUInfo exceptions
        cpu_model = CPUInfoModel(conn=self.conn)
        cpu_model.check_cpu_info(cpu_info)

        return cpu_info

    def _live_vm_update(self, dom, params):
        # Memory Hotplug/Unplug
        if (('memory' in params) and ('current' in params['memory'])):
            self._update_memory_live(dom, params)

        if 'vcpus' in params.get('cpu_info', {}):
            self.cpu_hotplug_precheck(dom, params)
            vcpus = params['cpu_info'].get('vcpus')
            self.update_cpu_live(dom, vcpus)

    def cpu_hotplug_precheck(self, dom, params):

        if (('maxvcpus' in params['cpu_info']) or
                ('topology' in params['cpu_info'])):
            raise InvalidParameter('KCHCPUHOTP0001E')

        topology = self.get_vm_cpu_topology(dom)

        xml_maxvcpus = xpath_get_text(dom.XMLDesc(0), 'vcpu')
        maxvcpus = int(xml_maxvcpus[0])
        vcpus = params['cpu_info'].get('vcpus')

        cpu_info = {
            'maxvcpus': maxvcpus,
            'vcpus': vcpus,
            'topology': topology,
        }

        cpu_model = CPUInfoModel(conn=self.conn)
        cpu_model.check_cpu_info(cpu_info)

    def update_cpu_live(self, dom, vcpus):
        flags = libvirt.VIR_DOMAIN_AFFECT_LIVE | \
            libvirt.VIR_DOMAIN_AFFECT_CONFIG
        try:
            dom.setVcpusFlags(vcpus, flags)
        except libvirt.libvirtError as e:
            raise OperationFailed('KCHCPUHOTP0002E', {'err': e.message})

    def _get_mem_dev_total_size(self, xml):
        root = ET.fromstring(xml)
        totMemDevs = 0
        for size in root.findall('./devices/memory/target/size'):
            totMemDevs += convert_data_size(size.text,
                                            size.get('unit'),
                                            'KiB')
        return int(totMemDevs)

    def _update_memory_live(self, dom, params):
        # Check if host supports memory device
        if not self.caps.mem_hotplug_support:
            raise InvalidOperation("KCHVM0046E")

        xml = dom.XMLDesc(0)
        max_mem = xpath_get_text(xml, './maxMemory')
        if max_mem == []:
            raise InvalidOperation('KCHVM0042E', {'name': dom.name()})

        new_mem = params['memory']['current']
        old_mem = int(xpath_get_text(xml, XPATH_DOMAIN_MEMORY)[0]) >> 10
        memory = new_mem - old_mem
        flags = libvirt.VIR_DOMAIN_MEM_CONFIG | libvirt.VIR_DOMAIN_MEM_LIVE

        if platform.machine().startswith('ppc'):
            # make sure memory is alingned in 256MiB in PowerPC
            if (new_mem % PPC_MEM_ALIGN != 0):
                raise InvalidParameter('KCHVM0071E',
                                       {'param': "Memory",
                                        'mem': str(new_mem),
                                        'alignment': str(PPC_MEM_ALIGN)})
            # Check number of slots supported
            if len(xpath_get_text(xml, './devices/memory')) == \
               MEM_DEV_SLOTS[os.uname()[4]]:
                raise InvalidOperation('KCHVM0045E')

        if memory == 0:
            # Nothing to do
            return
        if memory < 0:
            raise InvalidOperation('KCHVM0043E')

        # Finally HotPlug operation ( memory > 0 )
        try:
            # Create memory device xml
            tmp_xml = E.memory(E.target(E.size(str(memory),
                                        unit='MiB')), model='dimm')
            if has_cpu_numa(dom):
                tmp_xml.find('target').append(E.node('0'))
            dom.attachDeviceFlags(etree.tostring(tmp_xml), flags)
        except Exception as e:
            raise OperationFailed("KCHVM0047E", {'error': e.message})

    def _has_video(self, dom):
        dom = ElementTree.fromstring(dom.XMLDesc(0))
        return dom.find('devices/video') is not None

    def _update_guest_stats(self, name):
        try:
            dom = VMModel.get_vm(name, self.conn)

            vm_uuid = dom.UUIDString()
            info = dom.info()
            state = DOM_STATE_MAP[info[0]]

            if state != 'running':
                self.stats[vm_uuid] = {}
                return

            if self.stats.get(vm_uuid, None) is None:
                self.stats[vm_uuid] = {}

            timestamp = time.time()
            prevStats = self.stats.get(vm_uuid, {})
            seconds = timestamp - prevStats.get('timestamp', 0)
            self.stats[vm_uuid].update({'timestamp': timestamp})

            self._get_percentage_cpu_usage(vm_uuid, info, seconds)
            self._get_percentage_mem_usage(vm_uuid, dom, seconds)
            self._get_network_io_rate(vm_uuid, dom, seconds)
            self._get_disk_io_rate(vm_uuid, dom, seconds)
        except Exception as e:
            # VM might be deleted just after we get the list.
            # This is OK, just skip.
            wok_log.debug('Error processing VM stats: %s', e.message)

    def _get_percentage_cpu_usage(self, vm_uuid, info, seconds):
        prevCpuTime = self.stats[vm_uuid].get('cputime', 0)

        cpus = info[3]
        cpuTime = info[4] - prevCpuTime

        base = (((cpuTime) * 100.0) / (seconds * 1000.0 * 1000.0 * 1000.0))
        percentage = max(0.0, min(100.0, base / cpus))

        self.stats[vm_uuid].update({'cputime': info[4], 'cpu': percentage})

    def _get_percentage_mem_usage(self, vm_uuid, dom, seconds):
        # Get the guest's memory stats
        memStats = dom.memoryStats()
        if ('available' in memStats) and ('unused' in memStats):
            memUsed = memStats.get('available') - memStats.get('unused')
            percentage = ((memUsed * 100.0) / memStats.get('available'))
        elif ('rss' in memStats) and ('actual' in memStats):
            percentage = memStats.get('rss') * 100.0 / memStats.get('actual')
        else:
            wok_log.error('Failed to measure memory usage of the guest.')

        percentage = max(0.0, min(100.0, percentage))

        self.stats[vm_uuid].update({'mem_usage': percentage})

    def _get_network_io_rate(self, vm_uuid, dom, seconds):
        prevNetRxKB = self.stats[vm_uuid].get('netRxKB', 0)
        prevNetTxKB = self.stats[vm_uuid].get('netTxKB', 0)
        currentMaxNetRate = self.stats[vm_uuid].get('max_net_io', 100)

        rx_bytes = 0
        tx_bytes = 0

        tree = ElementTree.fromstring(dom.XMLDesc(0))
        for target in tree.findall('devices/interface/target'):
            dev = target.get('dev')
            io = dom.interfaceStats(dev)
            rx_bytes += io[0]
            tx_bytes += io[4]

        netRxKB = float(rx_bytes) / 1000
        netTxKB = float(tx_bytes) / 1000

        rx_stats = (netRxKB - prevNetRxKB) / seconds
        tx_stats = (netTxKB - prevNetTxKB) / seconds

        rate = rx_stats + tx_stats
        max_net_io = round(max(currentMaxNetRate, int(rate)), 1)

        self.stats[vm_uuid].update({'net_io': rate, 'max_net_io': max_net_io,
                                    'netRxKB': netRxKB, 'netTxKB': netTxKB})

    def _get_disk_io_rate(self, vm_uuid, dom, seconds):
        prevDiskRdKB = self.stats[vm_uuid].get('diskRdKB', 0)
        prevDiskWrKB = self.stats[vm_uuid].get('diskWrKB', 0)
        currentMaxDiskRate = self.stats[vm_uuid].get('max_disk_io', 100)

        rd_bytes = 0
        wr_bytes = 0

        tree = ElementTree.fromstring(dom.XMLDesc(0))
        for target in tree.findall("devices/disk/target"):
            dev = target.get("dev")
            io = dom.blockStats(dev)
            rd_bytes += io[1]
            wr_bytes += io[3]

        diskRdKB = float(rd_bytes) / 1024
        diskWrKB = float(wr_bytes) / 1024

        rd_stats = (diskRdKB - prevDiskRdKB) / seconds
        wr_stats = (diskWrKB - prevDiskWrKB) / seconds

        rate = rd_stats + wr_stats
        max_disk_io = round(max(currentMaxDiskRate, int(rate)), 1)

        self.stats[vm_uuid].update({'disk_io': rate,
                                    'max_disk_io': max_disk_io,
                                    'diskRdKB': diskRdKB,
                                    'diskWrKB': diskWrKB})

    def lookup(self, name):
        dom = self.get_vm(name, self.conn)
        try:
            # Avoid race condition, where guests may be deleted before below
            # command.
            info = dom.info()
        except libvirt.libvirtError as e:
            wok_log.error('Operation error while retrieving virtual machine '
                          '"%s" information: %s', name, e.message)
            raise OperationFailed('KCHVM0009E', {'name': name,
                                                 'err': e.message})
        state = DOM_STATE_MAP[info[0]]
        screenshot = None
        # (type, listen, port, passwd, passwdValidTo)
        graphics = self.get_graphics(name, self.conn)
        graphics_port = graphics[2]
        graphics_port = graphics_port if state == 'running' else None
        try:
            if state == 'running' and self._has_video(dom):
                screenshot = self.vmscreenshot.lookup(name)
            elif state == 'shutoff':
                # reset vm stats when it is powered off to avoid sending
                # incorrect (old) data
                self.stats[dom.UUIDString()] = {}
        except NotFoundError:
            pass

        with self.objstore as session:
            try:
                extra_info = session.get('vm', dom.UUIDString(), True)
            except NotFoundError:
                extra_info = {}
        icon = extra_info.get('icon')

        self._update_guest_stats(name)
        vm_stats = self.stats.get(dom.UUIDString(), {})
        res = {}
        res['cpu_utilization'] = vm_stats.get('cpu', 0)
        res['mem_utilization'] = vm_stats.get('mem_usage', 0)
        res['net_throughput'] = vm_stats.get('net_io', 0)
        res['net_throughput_peak'] = vm_stats.get('max_net_io', 100)
        res['io_throughput'] = vm_stats.get('disk_io', 0)
        res['io_throughput_peak'] = vm_stats.get('max_disk_io', 100)
        users, groups = self._get_access_info(dom)

        xml = dom.XMLDesc(0)
        maxvcpus = int(xpath_get_text(xml, XPATH_VCPU)[0])

        cpu_info = {
            'vcpus': info[3],
            'maxvcpus': maxvcpus,
            'topology': {},
        }

        if self.has_topology(dom):
            sockets = int(xpath_get_text(xml, XPATH_TOPOLOGY + '/@sockets')[0])
            cores = int(xpath_get_text(xml, XPATH_TOPOLOGY + '/@cores')[0])
            threads = int(xpath_get_text(xml, XPATH_TOPOLOGY + '/@threads')[0])

            cpu_info['topology'] = {
                'sockets': sockets,
                'cores': cores,
                'threads': threads,
            }

        # Kimchi does not make use of 'currentMemory' tag, it only updates
        # NUMA memory config or 'memory' tag directly. In memory hotplug,
        # Libvirt always updates 'memory', so we can use this tag retrieving
        # from Libvirt API maxMemory() function, regardeless of the VM state
        # Case VM changed currentMemory outside Kimchi, sum mem devs
        memory = dom.maxMemory() >> 10
        curr_mem = (info[2] >> 10)

        # On CentOS, dom.info does not retrieve memory. So, if machine does
        # not have memory hotplug, parse memory from xml
        if curr_mem == 0:
            curr_mem = int(xpath_get_text(xml, XPATH_MEMORY)[0]) >> 10

        if memory != curr_mem:
            memory = curr_mem + (self._get_mem_dev_total_size(xml) >> 10)

        # assure there is no zombie process left
        for proc in self._serial_procs[:]:
            if not proc.is_alive():
                proc.join(1)
                self._serial_procs.remove(proc)

        # Get max memory, or return "memory" if not set
        maxmemory = xpath_get_text(xml, XPATH_MAX_MEMORY)
        if len(maxmemory) > 0:
            maxmemory = convert_data_size(maxmemory[0], 'KiB', 'MiB')
        else:
            maxmemory = memory

        # get boot order and bootmenu
        boot = xpath_get_text(xml, XPATH_BOOT)
        bootmenu = "yes" if "yes" in xpath_get_text(xml, XPATH_BOOTMENU) \
            else "no"

        vm_info = {'name': name,
                   'title': "".join(xpath_get_text(xml, XPATH_TITLE)),
                   'description':
                       "".join(xpath_get_text(xml, XPATH_DESCRIPTION)),
                   'state': state,
                   'stats': res,
                   'uuid': dom.UUIDString(),
                   'memory': {'current': memory, 'maxmemory': maxmemory},
                   'cpu_info': cpu_info,
                   'screenshot': screenshot,
                   'icon': icon,
                   # (type, listen, port, passwd, passwdValidTo)
                   'graphics': {"type": graphics[0],
                                "listen": graphics[1],
                                "port": graphics_port,
                                "passwd": graphics[3],
                                "passwdValidTo": graphics[4]},
                   'users': users,
                   'groups': groups,
                   'access': 'full',
                   'persistent': True if dom.isPersistent() else False,
                   'bootorder': boot,
                   'bootmenu': bootmenu,
                   'autostart': dom.autostart()
                   }
        if platform.machine() in ['s390', 's390x']:
            vm_console = xpath_get_text(xml, XPATH_DOMAIN_CONSOLE_TARGET)
            vm_info['console'] = vm_console[0] if vm_console else ''

        return vm_info

    def _vm_get_disk_paths(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='disk']/source/@file"
        return xpath_get_text(xml, xpath)

    @staticmethod
    def get_vm(name, conn):
        def raise_exception(error_code):
            if error_code == libvirt.VIR_ERR_NO_DOMAIN:
                raise NotFoundError("KCHVM0002E", {'name': name})
            else:
                raise OperationFailed("KCHVM0009E", {'name': name,
                                                     'err': e.message})
        conn = conn.get()
        FeatureTests.disable_libvirt_error_logging()
        try:
            # outgoing text to libvirt, encode('utf-8')
            return conn.lookupByName(name.encode("utf-8"))
        except libvirt.libvirtError as e:
            name, nonascii_name = get_ascii_nonascii_name(name)
            if nonascii_name is None:
                raise_exception(e.get_error_code())

            try:
                return conn.lookupByName(name)
            except libvirt.libvirtError as e:
                raise_exception(e.get_error_code())

        FeatureTests.enable_libvirt_error_logging()

    def delete(self, name):
        conn = self.conn.get()
        dom = self.get_vm(name, self.conn)
        if not dom.isPersistent():
            raise InvalidOperation("KCHVM0036E", {'name': name})

        self._vmscreenshot_delete(dom.UUIDString())
        paths = self._vm_get_disk_paths(dom)
        info = self.lookup(name)

        if info['state'] != 'shutoff':
            self.poweroff(name)

        # delete existing snapshots before deleting VM

        # libvirt's Test driver does not support the function
        # "virDomainListAllSnapshots", so "VMSnapshots.get_list" will raise
        # "OperationFailed" in that case.
        try:
            snapshot_names = self.vmsnapshots.get_list(name)
        except OperationFailed, e:
            wok_log.error('cannot list snapshots: %s; '
                          'skipping snapshot deleting...' % e.message)
        else:
            for s in snapshot_names:
                self.vmsnapshot.delete(name, s)

        try:
            dom.undefine()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0021E",
                                  {'name': name, 'err': e.get_error_message()})

        for path in paths:
            try:
                vol = conn.storageVolLookupByPath(path)
                pool = vol.storagePoolLookupByVolume()
                xml = pool.XMLDesc(0)
                pool_type = xpath_get_text(xml, "/pool/@type")[0]
                if pool_type not in READONLY_POOL_TYPE:
                    vol.delete(0)
            except libvirt.libvirtError as e:
                wok_log.error('Unable to get storage volume by path: %s' %
                              e.message)
                try:
                    if is_s390x() and os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    wok_log.error('Unable to delete storage path: %s' %
                                  e.message)

            except Exception as e:
                raise OperationFailed('KCHVOL0017E', {'err': e.message})

        try:
            with self.objstore as session:
                session.delete('vm', dom.UUIDString(), ignore_missing=True)
        except Exception as e:
            # It is possible to delete vm without delete its database info
            wok_log.error('Error deleting vm information from database: '
                          '%s', e.message)

        websocket.remove_proxy_token(name)

    def start(self, name):
        # make sure the ISO file has read permission
        dom = self.get_vm(name, self.conn)
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='cdrom']/source/@file"
        isofiles = xpath_get_text(xml, xpath)

        user = UserTests.probe_user()
        for iso in isofiles:
            run_setfacl_set_attr(iso, user=user)

        dom = self.get_vm(name, self.conn)

        # vm already running: return error 400
        if DOM_STATE_MAP[dom.info()[0]] == "running":
            raise InvalidOperation("KCHVM0048E", {'name': name})

        try:
            dom.create()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0019E",
                                  {'name': name, 'err': e.get_error_message()})

    def poweroff(self, name):
        dom = self.get_vm(name, self.conn)

        # vm already powered off: return error 400
        if DOM_STATE_MAP[dom.info()[0]] == "shutoff":
            raise InvalidOperation("KCHVM0049E", {'name': name})

        try:
            dom.destroy()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0020E",
                                  {'name': name, 'err': e.get_error_message()})

    def shutdown(self, name):
        dom = self.get_vm(name, self.conn)

        # vm already powered off: return error 400
        if DOM_STATE_MAP[dom.info()[0]] == "shutoff":
            raise InvalidOperation("KCHVM0050E", {'name': name})

        try:
            dom.shutdown()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0029E",
                                  {'name': name, 'err': e.get_error_message()})

    def reset(self, name):
        dom = self.get_vm(name, self.conn)

        # vm already powered off: return error 400
        if DOM_STATE_MAP[dom.info()[0]] == "shutoff":
            raise InvalidOperation("KCHVM0051E", {'name': name})

        try:
            dom.reset(flags=0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0022E",
                                  {'name': name, 'err': e.get_error_message()})

    def _vm_check_serial(self, name):
        dom = self.get_vm(name, self.conn)
        xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)

        expr = "/domain/devices/serial/@type"
        # on s390x serial is not supported
        if platform.machine() != 's390x' and not xpath_get_text(xml, expr):
            return False

        expr = "/domain/devices/console/@type"
        if not xpath_get_text(xml, expr):
            return False

        return True

    @staticmethod
    def get_graphics(name, conn):
        dom = VMModel.get_vm(name, conn)
        xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)

        expr = "/domain/devices/graphics/@type"
        res = xpath_get_text(xml, expr)
        graphics_type = res[0] if res else None

        expr = "/domain/devices/graphics/@listen"
        res = xpath_get_text(xml, expr)
        graphics_listen = res[0] if res else None

        graphics_port = graphics_passwd = graphics_passwdValidTo = None
        if graphics_type:
            expr = "/domain/devices/graphics[@type='%s']/@port"
            res = xpath_get_text(xml, expr % graphics_type)
            graphics_port = int(res[0]) if res else None

            expr = "/domain/devices/graphics[@type='%s']/@passwd"
            res = xpath_get_text(xml, expr % graphics_type)
            graphics_passwd = res[0] if res else None

            expr = "/domain/devices/graphics[@type='%s']/@passwdValidTo"
            res = xpath_get_text(xml, expr % graphics_type)
            if res:
                to = time.mktime(time.strptime(res[0], '%Y-%m-%dT%H:%M:%S'))
                graphics_passwdValidTo = to - time.mktime(time.gmtime())

        return (graphics_type, graphics_listen, graphics_port,
                graphics_passwd, graphics_passwdValidTo)

    def serial(self, name):
        if not self._vm_check_serial(name):
            raise OperationFailed("KCHVM0076E", {'name': name})

        if not os.path.isdir(serialconsole.BASE_DIRECTORY):
            try:
                os.mkdir(serialconsole.BASE_DIRECTORY)

            except OSError as e:
                raise OperationFailed("KCHVM0081E",
                                      {'dir': serialconsole.BASE_DIRECTORY})

        websocket.add_proxy_token(name.encode('utf-8')+'-console',
                                  os.path.join(serialconsole.BASE_DIRECTORY,
                                               name.encode('utf-8')), True)

        try:
            proc = serialconsole.main(name.encode('utf-8'),
                                      self.conn.get().getURI())

            proc.join(2)
            if not proc.is_alive():
                raise OperationFailed("KCHVM0082E", {'name': name})

            self._serial_procs.append(proc)

        except OperationFailed:
            raise

        except Exception as e:
            wok_log.error(e.message)
            raise OperationFailed("KCHVM0077E", {'name': name})

    def connect(self, name):
        # (type, listen, port, passwd, passwdValidTo)
        graphics_port = self.get_graphics(name, self.conn)[2]
        if graphics_port is not None:
            websocket.add_proxy_token(name.encode('utf-8'), graphics_port)
        else:
            raise OperationFailed("KCHVM0010E", {'name': name})

    def _vmscreenshot_delete(self, vm_uuid):
        screenshot = VMScreenshotModel.get_screenshot(vm_uuid, self.objstore,
                                                      self.conn)
        screenshot.delete()
        try:
            with self.objstore as session:
                session.delete('screenshot', vm_uuid)
        except Exception as e:
            # It is possible to continue Kimchi executions without delete
            # screenshots
            wok_log.error('Error trying to delete vm screenshot from '
                          'database due error: %s', e.message)

    def suspend(self, name):
        """Suspend the virtual machine's execution and puts it in the
        state 'paused'. Use the function "resume" to restore its state.
        If the VM is not running, an exception will be raised.

        Parameters:
        name -- the name of the VM to be suspended.
        """
        vm = self.lookup(name)
        if vm['state'] != 'running':
            raise InvalidOperation('KCHVM0037E', {'name': name})

        vir_dom = self.get_vm(name, self.conn)

        try:
            vir_dom.suspend()
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHVM0038E', {'name': name,
                                                 'err': e.message})

    def resume(self, name):
        """Resume the virtual machine's execution and puts it in the
        state 'running'. The VM should have been suspended previously by the
        function "suspend" and be in the state 'paused', otherwise an exception
        will be raised.

        Parameters:
        name -- the name of the VM to be resumed.
        """
        vm = self.lookup(name)
        if vm['state'] != 'paused':
            raise InvalidOperation('KCHVM0039E', {'name': name})

        vir_dom = self.get_vm(name, self.conn)

        try:
            vir_dom.resume()
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHVM0040E', {'name': name,
                                                 'err': e.message})

    def _check_if_host_not_localhost(self, remote_host):
        hostname = socket.gethostname()

        if remote_host in ['localhost', '127.0.0.1', hostname]:
            raise OperationFailed("KCHVM0055E", {'host': remote_host})

    def _check_if_migrating_same_arch_hypervisor(self, remote_host,
                                                 user='root'):
        remote_conn = None
        try:
            remote_conn = self._get_remote_libvirt_conn(
                remote_host,
                user
            )
            source_hyp = self.conn.get().getType()
            dest_hyp = remote_conn.getType()
            if source_hyp != dest_hyp:
                raise OperationFailed(
                    "KCHVM0065E",
                    {
                        'host': remote_host,
                        'srchyp': source_hyp,
                        'desthyp': dest_hyp
                    }
                )
            source_arch = self.conn.get().getInfo()[0]
            dest_arch = remote_conn.getInfo()[0]
            if source_arch != dest_arch:
                raise OperationFailed(
                    "KCHVM0064E",
                    {
                        'host': remote_host,
                        'srcarch': source_arch,
                        'destarch': dest_arch
                    }
                )
        except Exception, e:
            raise OperationFailed("KCHVM0066E", {'error': e.message})

        finally:
            if remote_conn:
                remote_conn.close()

    def _check_ppc64_subcores_per_core(self, remote_host, user):
        """
        Output expected from command-line:

        $ ppc64_cpu --subcores-per-core
        Subcores per core: N
        """

        def _get_local_ppc64_subpercore():
            local_cmd = ['ppc64_cpu', '--subcores-per-core']
            out, err, returncode = run_command(local_cmd, 5, silent=True)
            if returncode != 0:
                return None
            local_sub_per_core = out.strip()[-1]
            return local_sub_per_core

        def _get_remote_ppc64_subpercore(remote_host, user):
            username_host = "%s@%s" % (user, remote_host)
            ssh_cmd = ['ssh', '-oNumberOfPasswordPrompts=0',
                       '-oStrictHostKeyChecking=no', username_host,
                       'ppc64_cpu', '--subcores-per-core']
            out, err, returncode = run_command(ssh_cmd, 5, silent=True)
            if returncode != 0:
                return None
            remote_sub_per_core = out.strip()[-1]
            return remote_sub_per_core

        local_sub_per_core = _get_local_ppc64_subpercore()
        if local_sub_per_core is None:
            return

        remote_sub_per_core = _get_remote_ppc64_subpercore(remote_host, user)

        if local_sub_per_core != remote_sub_per_core:
            raise OperationFailed("KCHVM0067E", {'host': remote_host})

    def _check_if_password_less_login_enabled(self, remote_host,
                                              user, password):
        username_host = "%s@%s" % (user, remote_host)
        ssh_cmd = ['ssh', '-oNumberOfPasswordPrompts=0',
                   '-oStrictHostKeyChecking=no', username_host,
                   'echo', 'hello']
        stdout, stderr, returncode = run_command(ssh_cmd, 5, silent=True)
        if returncode != 0:
            if password is None:
                raise OperationFailed("KCHVM0056E",
                                      {'host': remote_host, 'user': user})
            else:
                self._set_password_less_login(remote_host, user, password)

    def _set_password_less_login(self, remote_host, user, passwd):
        home_dir = '/root' if user is 'root' else '/home/%s' % user

        id_rsa_file = "%s/.ssh/id_rsa" % home_dir
        id_rsa_pub_file = id_rsa_file + '.pub'
        ssh_port = 22
        ssh_client = None

        def read_id_rsa_pub_file():
            data = None
            with open(id_rsa_pub_file, "r") as id_file:
                data = id_file.read()
            return data

        def create_root_ssh_key_if_required():
            if os.path.isfile(id_rsa_pub_file):
                return

            with open("/dev/zero") as zero_input:
                cmd = ['ssh-keygen', '-q', '-N', '', '-f', id_rsa_file]
                proc = subprocess.Popen(
                    cmd,
                    stdin=zero_input,
                    stdout=open(os.devnull, 'wb')
                )
                out, err = proc.communicate()

                if not os.path.isfile(id_rsa_pub_file):
                    raise OperationFailed("KCHVM0070E")

                if user is not 'root':
                    id_rsa_content = read_id_rsa_pub_file()
                    updated_content = id_rsa_content.replace(
                        ' root@', ' %s@' % user
                    )
                    with open(id_rsa_pub_file, 'w+') as f:
                        f.write(updated_content)

                    user_uid = pwd.getpwnam(user).pw_uid
                    user_gid = pwd.getpwnam(user).pw_gid
                    os.chown(id_rsa_pub_file, user_uid, user_gid)
                    os.chown(id_rsa_file, user_uid, user_gid)

        def get_ssh_client(remote_host, user, passwd):
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(remote_host, ssh_port, username=user,
                               password=passwd, timeout=4)
            return ssh_client

        def append_id_rsa_to_remote_authorized_keys(ssh_client, id_rsa_data):
            sftp_client = ssh_client.open_sftp()
            ssh_dir = '%s/.ssh' % home_dir

            try:
                sftp_client.chdir(ssh_dir)
            except IOError:
                raise OperationFailed(
                    "KCHVM0089E",
                    {'host': remote_host, 'user': user, 'sshdir': ssh_dir}
                )

            file_handler = sftp_client.file(
                '%s/.ssh/authorized_keys' % home_dir,
                mode='a',
                bufsize=1
            )
            file_handler.write(id_rsa_data)
            file_handler.flush()
            file_handler.close()

            sftp_client.close()

        try:
            create_root_ssh_key_if_required()
            id_rsa_data = read_id_rsa_pub_file()
            ssh_client = get_ssh_client(remote_host, user, passwd)
            append_id_rsa_to_remote_authorized_keys(
                ssh_client,
                id_rsa_data
            )
        except Exception, e:
            raise OperationFailed(
                "KCHVM0068E",
                {'host': remote_host, 'user': user, 'error': e.message}
            )

        finally:
            if ssh_client:
                ssh_client.close()

    def _check_remote_libvirt_conn(self, remote_host,
                                   user='root', transport='ssh'):

        dest_uri = 'qemu+%s://%s@%s/system' % (transport, user, remote_host)
        cmd = ['virsh', '-c', dest_uri, 'list']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                shell=True, preexec_fn=os.setsid)
        timeout = 0
        while proc.poll() is None:
            time.sleep(1)
            timeout += 1
            if timeout == 5:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                raise OperationFailed("KCHVM0090E",
                                      {'host': remote_host, 'user': user})

    def _get_remote_libvirt_conn(self, remote_host,
                                 user='root', transport='ssh'):
        dest_uri = 'qemu+%s://%s@%s/system' % (transport, user, remote_host)
        # TODO: verify why LibvirtConnection(dest_uri) does not work here
        return libvirt.open(dest_uri)

    def migration_pre_check(self, remote_host, user, password):
        self._check_if_host_not_localhost(remote_host)
        self._check_if_password_less_login_enabled(
            remote_host,
            user,
            password
        )
        self._check_remote_libvirt_conn(remote_host, user)
        self._check_if_migrating_same_arch_hypervisor(remote_host, user)

        if platform.machine() in ['ppc64', 'ppc64le']:
            self._check_ppc64_subcores_per_core(remote_host, user)

    def _check_if_path_exists_in_remote_host(self, path, remote_host, user):
        username_host = "%s@%s" % (user, remote_host)
        cmd = ['ssh', '-oStrictHostKeyChecking=no', username_host,
               'test', '-e', path]
        _, _, returncode = run_command(cmd, 5, silent=True)
        return returncode == 0

    def _get_vm_devices_infos(self, vm_name):
        dom = VMModel.get_vm(vm_name, self.conn)
        infos = [get_vm_disk_info(dom, dev_name)
                 for dev_name in get_vm_disks(dom).keys()]
        return infos

    def _check_if_nonshared_migration(self, vm_name, remote_host, user):
        for dev_info in self._get_vm_devices_infos(vm_name):
            dev_path = dev_info.get('path')
            if not self._check_if_path_exists_in_remote_host(
                    dev_path, remote_host, user):
                return True
        return False

    def _create_remote_path(self, path, remote_host, user):
        username_host = "%s@%s" % (user, remote_host)
        cmd = ['ssh', '-oStrictHostKeyChecking=no', username_host,
               'touch', path]
        _, _, returncode = run_command(cmd, 5, silent=True)
        if returncode != 0:
            raise OperationFailed(
                "KCHVM0061E",
                {'path': path, 'host': remote_host, 'user': user}
            )

    def _get_img_size(self, disk_path):
        try:
            conn = self.conn.get()
            vol_obj = conn.storageVolLookupByPath(disk_path)
            return vol_obj.info()[1]
        except Exception, e:
            raise OperationFailed(
                "KCHVM0062E",
                {'path': disk_path, 'error': e.message}
            )

    def _create_remote_disk(self, disk_info, remote_host, user):
        username_host = "%s@%s" % (user, remote_host)
        disk_fmt = disk_info.get('format')
        disk_path = disk_info.get('path')
        disk_size = self._get_img_size(disk_path)
        cmd = ['ssh', '-oStrictHostKeyChecking=no', username_host,
               'qemu-img', 'create', '-f', disk_fmt,
               disk_path, str(disk_size)]
        out, err, returncode = run_command(cmd, silent=True)
        if returncode != 0:
            raise OperationFailed(
                "KCHVM0063E",
                {
                    'error': err,
                    'path': disk_path,
                    'host': remote_host,
                    'user': user
                }
            )

    def _create_vm_remote_paths(self, vm_name, remote_host, user):
        for dev_info in self._get_vm_devices_infos(vm_name):
            dev_path = dev_info.get('path')
            if not self._check_if_path_exists_in_remote_host(
                    dev_path, remote_host, user):
                if dev_info.get('type') == 'cdrom':
                    self._create_remote_path(
                        dev_path,
                        remote_host,
                        user
                    )
                else:
                    self._create_remote_disk(
                        dev_info,
                        remote_host,
                        user
                    )

    def migrate(self, name, remote_host, user=None, password=None,
                enable_rdma=None):
        name = name.decode('utf-8')
        remote_host = remote_host.decode('utf-8')

        if user is None:
            user = 'root'

        if enable_rdma is None:
            enable_rdma = False

        self.migration_pre_check(remote_host, user, password)
        dest_conn = self._get_remote_libvirt_conn(remote_host, user)

        non_shared = self._check_if_nonshared_migration(
            name,
            remote_host,
            user
        )

        params = {'name': name,
                  'dest_conn': dest_conn,
                  'non_shared': non_shared,
                  'remote_host': remote_host,
                  'user': user,
                  'enable_rdma': enable_rdma}
        task_id = AsyncTask('/plugins/kimchi/vms/%s/migrate' % name,
                            self._migrate_task, params).id

        return self.task.lookup(task_id)

    def _migrate_task(self, cb, params):
        name = params['name'].decode('utf-8')
        dest_conn = params['dest_conn']
        non_shared = params['non_shared']
        remote_host = params['remote_host']
        user = params['user']
        enable_rdma = params['enable_rdma']

        cb('starting a migration')

        dom = self.get_vm(name, self.conn)
        state = DOM_STATE_MAP[dom.info()[0]]

        flags = libvirt.VIR_MIGRATE_PEER2PEER
        if state == 'shutoff':
            flags |= (libvirt.VIR_MIGRATE_OFFLINE |
                      libvirt.VIR_MIGRATE_PERSIST_DEST)
        elif state in ['running', 'paused']:
            flags |= libvirt.VIR_MIGRATE_LIVE | libvirt.VIR_MIGRATE_TUNNELLED
            if dom.isPersistent():
                flags |= libvirt.VIR_MIGRATE_PERSIST_DEST
        else:
            dest_conn.close()
            raise OperationFailed("KCHVM0057E", {'name': name,
                                                 'state': state})
        if non_shared:
            flags |= libvirt.VIR_MIGRATE_NON_SHARED_DISK
            self._create_vm_remote_paths(
                name,
                remote_host,
                user
            )

        try:
            if enable_rdma:
                param_uri = 'rdma://' + remote_host
                dom.migrate(dest_conn, flags, uri=param_uri)
            else:
                dom.migrate(dest_conn, flags)
        except libvirt.libvirtError as e:
            cb('Migrate failed', False)
            raise OperationFailed('KCHVM0058E', {'err': e.message,
                                                 'name': name})
        finally:
            dest_conn.close()

        cb('Migrate finished', True)


class VMScreenshotModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']

    def lookup(self, name):
        dom = VMModel.get_vm(name, self.conn)
        d_info = dom.info()
        vm_uuid = dom.UUIDString()
        if DOM_STATE_MAP[d_info[0]] != 'running':
            raise NotFoundError("KCHVM0004E", {'name': name})

        screenshot = self.get_screenshot(vm_uuid, self.objstore, self.conn)
        img_path = screenshot.lookup()
        # screenshot info changed after scratch generation
        try:
            with self.objstore as session:
                session.store('screenshot', vm_uuid, screenshot.info,
                              get_kimchi_version())
        except Exception as e:
            # It is possible to continue Kimchi executions without store
            # screenshots
            wok_log.error('Error trying to update database with guest '
                          'screenshot information due error: %s', e.message)
        return img_path

    @staticmethod
    def get_screenshot(vm_uuid, objstore, conn):
        try:
            with objstore as session:
                try:
                    params = session.get('screenshot', vm_uuid)
                except NotFoundError:
                    params = {'uuid': vm_uuid}
                    session.store('screenshot', vm_uuid, params,
                                  get_kimchi_version())
        except Exception as e:
            # The 'except' outside of 'with' is necessary to catch possible
            # exception from '__exit__' when calling 'session.store'
            # It is possible to continue Kimchi vm executions without
            # screenshots
            wok_log.error('Error trying to update database with guest '
                          'screenshot information due error: %s', e.message)
        return LibvirtVMScreenshot(params, conn)


class LibvirtVMScreenshot(VMScreenshot):
    def __init__(self, vm_uuid, conn):
        VMScreenshot.__init__(self, vm_uuid)
        self.conn = conn

    def _generate_scratch(self, thumbnail):
        def handler(stream, buf, opaque):
            fd = opaque
            os.write(fd, buf)

        fd = os.open(thumbnail, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0644)
        try:
            conn = self.conn.get()
            dom = conn.lookupByUUIDString(self.vm_uuid)
            vm_name = dom.name()
            stream = conn.newStream(0)
            dom.screenshot(stream, 0, 0)
            stream.recvAll(handler, fd)
        except libvirt.libvirtError:
            try:
                stream.abort()
            except:
                pass
            raise NotFoundError("KCHVM0006E", {'name': vm_name})
        else:
            stream.finish()
        finally:
            os.close(fd)
