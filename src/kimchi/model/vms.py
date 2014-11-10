#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
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

from lxml.builder import E
import lxml.etree as ET
from lxml import etree, objectify
import os
import random
import string
import time
import uuid
from xml.etree import ElementTree

import libvirt
from cherrypy.process.plugins import BackgroundTask

from kimchi import model, vnc
from kimchi.config import READONLY_POOL_TYPE
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.model.config import CapabilitiesModel
from kimchi.model.tasks import TaskModel
from kimchi.model.templates import TemplateModel
from kimchi.model.utils import get_vm_name
from kimchi.model.utils import get_metadata_node
from kimchi.model.utils import set_metadata_node
from kimchi.rollbackcontext import RollbackContext
from kimchi.screenshot import VMScreenshot
from kimchi.utils import add_task, get_next_clone_name, import_class
from kimchi.utils import kimchi_log, run_setfacl_set_attr
from kimchi.utils import template_name_from_uri
from kimchi.xmlutils.utils import xpath_get_text, xml_item_update


DOM_STATE_MAP = {0: 'nostate',
                 1: 'running',
                 2: 'blocked',
                 3: 'paused',
                 4: 'shutdown',
                 5: 'shutoff',
                 6: 'crashed',
                 7: 'pmsuspended'}

GUESTS_STATS_INTERVAL = 5
VM_STATIC_UPDATE_PARAMS = {'name': './name',
                           'cpus': './vcpu',
                           'memory': './memory'}
VM_LIVE_UPDATE_PARAMS = {}

stats = {}


XPATH_DOMAIN_DISK = "/domain/devices/disk[@device='disk']/source/@file"
XPATH_DOMAIN_DISK_BY_FILE = "./devices/disk[@device='disk']/source[@file='%s']"
XPATH_DOMAIN_NAME = '/domain/name'
XPATH_DOMAIN_MAC = "/domain/devices/interface[@type='network']/mac/@address"
XPATH_DOMAIN_MAC_BY_ADDRESS = "./devices/interface[@type='network']/"\
                              "mac[@address='%s']"
XPATH_DOMAIN_UUID = '/domain/uuid'


class VMsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.caps = CapabilitiesModel()
        self.guests_stats_thread = BackgroundTask(GUESTS_STATS_INTERVAL,
                                                  self._update_guests_stats)
        self.guests_stats_thread.start()

    def _update_guests_stats(self):
        vm_list = self.get_list()

        for name in vm_list:
            try:
                dom = VMModel.get_vm(name, self.conn)

                vm_uuid = dom.UUIDString()
                info = dom.info()
                state = DOM_STATE_MAP[info[0]]

                if state != 'running':
                    stats[vm_uuid] = {}
                    continue

                if stats.get(vm_uuid, None) is None:
                    stats[vm_uuid] = {}

                timestamp = time.time()
                prevStats = stats.get(vm_uuid, {})
                seconds = timestamp - prevStats.get('timestamp', 0)
                stats[vm_uuid].update({'timestamp': timestamp})

                self._get_percentage_cpu_usage(vm_uuid, info, seconds)
                self._get_network_io_rate(vm_uuid, dom, seconds)
                self._get_disk_io_rate(vm_uuid, dom, seconds)
            except Exception as e:
                # VM might be deleted just after we get the list.
                # This is OK, just skip.
                kimchi_log.debug('Error processing VM stats: %s', e.message)
                continue

    def _get_percentage_cpu_usage(self, vm_uuid, info, seconds):
        prevCpuTime = stats[vm_uuid].get('cputime', 0)

        cpus = info[3]
        cpuTime = info[4] - prevCpuTime

        base = (((cpuTime) * 100.0) / (seconds * 1000.0 * 1000.0 * 1000.0))
        percentage = max(0.0, min(100.0, base / cpus))

        stats[vm_uuid].update({'cputime': info[4], 'cpu': percentage})

    def _get_network_io_rate(self, vm_uuid, dom, seconds):
        prevNetRxKB = stats[vm_uuid].get('netRxKB', 0)
        prevNetTxKB = stats[vm_uuid].get('netTxKB', 0)
        currentMaxNetRate = stats[vm_uuid].get('max_net_io', 100)

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

        stats[vm_uuid].update({'net_io': rate, 'max_net_io': max_net_io,
                               'netRxKB': netRxKB, 'netTxKB': netTxKB})

    def _get_disk_io_rate(self, vm_uuid, dom, seconds):
        prevDiskRdKB = stats[vm_uuid].get('diskRdKB', 0)
        prevDiskWrKB = stats[vm_uuid].get('diskWrKB', 0)
        currentMaxDiskRate = stats[vm_uuid].get('max_disk_io', 100)

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

        stats[vm_uuid].update({'disk_io': rate,
                               'max_disk_io': max_disk_io,
                               'diskRdKB': diskRdKB,
                               'diskWrKB': diskWrKB})

    def create(self, params):
        conn = self.conn.get()
        t_name = template_name_from_uri(params['template'])
        vm_uuid = str(uuid.uuid4())
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

        # Store the icon for displaying later
        icon = t.info.get('icon')
        if icon:
            try:
                with self.objstore as session:
                    session.store('vm', vm_uuid, {'icon': icon})
            except Exception as e:
                # It is possible to continue Kimchi executions without store
                # vm icon info
                kimchi_log.error('Error trying to update database with guest '
                                 'icon information due error: %s', e.message)

        # If storagepool is SCSI, volumes will be LUNs and must be passed by
        # the user from UI or manually.
        vol_list = []
        if t._get_storage_type() not in ["iscsi", "scsi"]:
            vol_list = t.fork_vm_storage(vm_uuid)

        graphics = params.get('graphics', {})
        stream_protocols = self.caps.libvirt_stream_protocols
        xml = t.to_vm_xml(name, vm_uuid,
                          libvirt_stream_protocols=stream_protocols,
                          qemu_stream_dns=self.caps.qemu_stream_dns,
                          graphics=graphics,
                          volumes=vol_list)

        try:
            conn.defineXML(xml.encode('utf-8'))
        except libvirt.libvirtError as e:
            if t._get_storage_type() not in READONLY_POOL_TYPE:
                for v in vol_list:
                    vol = conn.storageVolLookupByPath(v['path'])
                    vol.delete(0)
            raise OperationFailed("KCHVM0007E", {'name': name,
                                                 'err': e.get_error_message()})

        VMModel.vm_update_os_metadata(VMModel.get_vm(name, self.conn), t.info)

        return name

    def get_list(self):
        return self.get_vms(self.conn)

    @staticmethod
    def get_vms(conn):
        conn = conn.get()
        names = [dom.name().decode('utf-8') for dom in conn.listAllDomains(0)]
        return sorted(names, key=unicode.lower)


class VMModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.vmscreenshot = VMScreenshotModel(**kargs)
        self.users = import_class('kimchi.model.host.UsersModel')(**kargs)
        self.groups = import_class('kimchi.model.host.GroupsModel')(**kargs)
        self.vms = VMsModel(**kargs)
        self.task = TaskModel(**kargs)
        self.storagepool = model.storagepools.StoragePoolModel(**kargs)
        self.storagevolume = model.storagevolumes.StorageVolumeModel(**kargs)
        self.storagevolumes = model.storagevolumes.StorageVolumesModel(**kargs)

    def update(self, name, params):
        dom = self.get_vm(name, self.conn)
        dom = self._static_vm_update(dom, params)
        self._live_vm_update(dom, params)
        return dom.name().decode('utf-8')

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
        name = name.decode('utf-8')

        # VM must be shutoff in order to clone it
        info = self.lookup(name)
        if info['state'] != u'shutoff':
            raise InvalidParameter('KCHVM0033E', {'name': name})

        # this name will be used as the Task's 'target_uri' so it needs to be
        # defined now.
        new_name = get_next_clone_name(self.vms.get_list(), name)

        # create a task with the actual clone function
        taskid = add_task(u'/vms/%s' % new_name, self._clone_task,
                          self.objstore,
                          {'name': name, 'new_name': new_name})

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
        vir_conn = self.conn.get()

        # fetch base XML
        cb('reading source VM XML')
        try:
            vir_dom = vir_conn.lookupByName(name)
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
            xml = xml_item_update(xml, './name', new_name)

            # create new guest
            cb('defining new VM')
            try:
                vir_conn.defineXML(xml)
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

        for i, path in enumerate(all_paths):
            try:
                vir_orig_vol = vir_conn.storageVolLookupByPath(path)
                vir_pool = vir_orig_vol.storagePoolLookupByVolume()

                orig_pool_name = vir_pool.name().decode('utf-8')
                orig_vol_name = vir_orig_vol.name().decode('utf-8')
            except libvirt.libvirtError, e:
                domain_name = xpath_get_text(xml, XPATH_DOMAIN_NAME)[0]
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
                    kimchi_log.warning('storage pool \'%s\' doesn\'t have '
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
                kimchi_log.warning('cannot create new volume for clone in '
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
                session.store('vm', new_uuid, {'icon': icon})
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

    def _build_access_elem(self, users, groups):
        access = E.access()
        for user in users:
            access.append(E.user(user))

        for group in groups:
            access.append(E.group(group))

        return access

    def _vm_update_access_metadata(self, dom, params):
        users = groups = None
        if "users" in params:
            users = params["users"]
            invalid_users = set(users) - set(self.users.get_list())
            if len(invalid_users) != 0:
                raise InvalidParameter("KCHVM0027E",
                                       {'users': ", ".join(invalid_users)})
        if "groups" in params:
            groups = params["groups"]
            invalid_groups = set(groups) - set(self.groups.get_list())
            if len(invalid_groups) != 0:
                raise InvalidParameter("KCHVM0028E",
                                       {'groups': ", ".join(invalid_groups)})

        if users is None and groups is None:
            return

        access_xml = (get_metadata_node(dom, "access") or
                      """<access></access>""")
        old_users = xpath_get_text(access_xml, "/access/user")
        old_groups = xpath_get_text(access_xml, "/access/group")
        users = old_users if users is None else users
        groups = old_groups if groups is None else groups

        node = self._build_access_elem(users, groups)
        set_metadata_node(dom, node)

    @staticmethod
    def vm_get_os_metadata(dom):
        os_xml = get_metadata_node(dom, "os") or """<os></os>"""
        os_elem = ET.fromstring(os_xml)
        return (os_elem.attrib.get("version"), os_elem.attrib.get("distro"))

    @staticmethod
    def vm_update_os_metadata(dom, params):
        distro = params.get("os_distro")
        version = params.get("os_version")
        if distro is None:
            return
        os_elem = E.os({"distro": distro, "version": version})
        set_metadata_node(dom, os_elem)

    def _update_graphics(self, dom, xml, params):
        root = objectify.fromstring(xml)
        graphics = root.devices.find("graphics")
        if graphics is None:
            return xml

        password = params['graphics'].get("passwd")
        if password is not None and len(password.strip()) == 0:
            password = "".join(random.sample(string.ascii_letters +
                                             string.digits, 8))

        if password is not None:
            graphics.attrib['passwd'] = password

        expire = params['graphics'].get("passwdValidTo")
        to = graphics.attrib.get('passwdValidTo')
        if to is not None:
            if (time.mktime(time.strptime(to, '%Y-%m-%dT%H:%M:%S'))
               - time.time() <= 0):
                expire = expire if expire is not None else 30

        if expire is not None:
            expire_time = time.gmtime(time.time() + float(expire))
            valid_to = time.strftime('%Y-%m-%dT%H:%M:%S', expire_time)
            graphics.attrib['passwdValidTo'] = valid_to

        if not dom.isActive():
            return ET.tostring(root, encoding="utf-8")

        xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        dom.updateDeviceFlags(etree.tostring(graphics),
                              libvirt.VIR_DOMAIN_AFFECT_LIVE)
        return xml

    def _static_vm_update(self, dom, params):
        state = DOM_STATE_MAP[dom.info()[0]]
        old_xml = new_xml = dom.XMLDesc(0)

        for key, val in params.items():
            if key in VM_STATIC_UPDATE_PARAMS:
                if key == 'memory':
                    # Libvirt saves memory in KiB. Retrieved xml has memory
                    # in KiB too, so new valeu must be in KiB here
                    val = val * 1024
                if type(val) == int:
                    val = str(val)
                xpath = VM_STATIC_UPDATE_PARAMS[key]
                new_xml = xml_item_update(new_xml, xpath, val)

        if 'graphics' in params:
            new_xml = self._update_graphics(dom, new_xml, params)

        conn = self.conn.get()
        try:
            if 'name' in params:
                if state == 'running':
                    msg_args = {'name': dom.name(), 'new_name': params['name']}
                    raise InvalidParameter("KCHVM0003E", msg_args)

                # Undefine old vm, only if name is going to change
                dom.undefine()

            root = ET.fromstring(new_xml)
            currentMem = root.find('.currentMemory')
            if currentMem is not None:
                root.remove(currentMem)
            dom = conn.defineXML(ET.tostring(root, encoding="utf-8"))
        except libvirt.libvirtError as e:
            dom = conn.defineXML(old_xml)
            raise OperationFailed("KCHVM0008E", {'name': dom.name(),
                                                 'err': e.get_error_message()})
        return dom

    def _live_vm_update(self, dom, params):
        self._vm_update_access_metadata(dom, params)

    def _has_video(self, dom):
        dom = ElementTree.fromstring(dom.XMLDesc(0))
        return dom.find('devices/video') is not None

    def lookup(self, name):
        dom = self.get_vm(name, self.conn)
        info = dom.info()
        state = DOM_STATE_MAP[info[0]]
        screenshot = None
        # (type, listen, port, passwd, passwdValidTo)
        graphics = self._vm_get_graphics(name)
        graphics_port = graphics[2]
        graphics_port = graphics_port if state == 'running' else None
        try:
            if state == 'running' and self._has_video(dom):
                screenshot = self.vmscreenshot.lookup(name)
            elif state == 'shutoff':
                # reset vm stats when it is powered off to avoid sending
                # incorrect (old) data
                stats[dom.UUIDString()] = {}
        except NotFoundError:
            pass

        with self.objstore as session:
            try:
                extra_info = session.get('vm', dom.UUIDString())
            except NotFoundError:
                extra_info = {}
        icon = extra_info.get('icon')

        vm_stats = stats.get(dom.UUIDString(), {})
        res = {}
        res['cpu_utilization'] = vm_stats.get('cpu', 0)
        res['net_throughput'] = vm_stats.get('net_io', 0)
        res['net_throughput_peak'] = vm_stats.get('max_net_io', 100)
        res['io_throughput'] = vm_stats.get('disk_io', 0)
        res['io_throughput_peak'] = vm_stats.get('max_disk_io', 100)

        access_xml = (get_metadata_node(dom, "access") or
                      """<access></access>""")
        users = xpath_get_text(access_xml, "/access/user")
        groups = xpath_get_text(access_xml, "/access/group")

        return {'name': name,
                'state': state,
                'stats': res,
                'uuid': dom.UUIDString(),
                'memory': info[2] >> 10,
                'cpus': info[3],
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
                'persistent': True if dom.isPersistent() else False
                }

    def _vm_get_disk_paths(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='disk']/source/@file"
        return xpath_get_text(xml, xpath)

    @staticmethod
    def get_vm(name, conn):
        conn = conn.get()
        try:
            # outgoing text to libvirt, encode('utf-8')
            return conn.lookupByName(name.encode("utf-8"))
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
                raise NotFoundError("KCHVM0002E", {'name': name})
            else:
                raise OperationFailed("KCHVM0009E", {'name': name,
                                                     'err': e.message})

    def delete(self, name):
        conn = self.conn.get()
        dom = self.get_vm(name, self.conn)
        self._vmscreenshot_delete(dom.UUIDString())
        paths = self._vm_get_disk_paths(dom)
        info = self.lookup(name)

        if info['state'] == 'running':
            self.poweroff(name)

        try:
            dom.undefine()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0021E",
                                  {'name': name, 'err': e.get_error_message()})

        for path in paths:
            vol = conn.storageVolLookupByPath(path)
            pool = vol.storagePoolLookupByVolume()
            xml = pool.XMLDesc(0)
            pool_type = xpath_get_text(xml, "/pool/@type")[0]
            if pool_type not in READONLY_POOL_TYPE:
                vol.delete(0)
        try:
            with self.objstore as session:
                session.delete('vm', dom.UUIDString(), ignore_missing=True)
        except Exception as e:
            # It is possible to delete vm without delete its database info
            kimchi_log.error('Error deleting vm information from database: '
                             '%s', e.message)

        vnc.remove_proxy_token(name)

    def start(self, name):
        # make sure the ISO file has read permission
        dom = self.get_vm(name, self.conn)
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='cdrom']/source/@file"
        isofiles = xpath_get_text(xml, xpath)
        for iso in isofiles:
            run_setfacl_set_attr(iso)

        dom = self.get_vm(name, self.conn)
        try:
            dom.create()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0019E",
                                  {'name': name, 'err': e.get_error_message()})

    def poweroff(self, name):
        dom = self.get_vm(name, self.conn)
        try:
            dom.destroy()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0020E",
                                  {'name': name, 'err': e.get_error_message()})

    def shutdown(self, name):
        dom = self.get_vm(name, self.conn)
        try:
            dom.shutdown()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0029E",
                                  {'name': name, 'err': e.get_error_message()})

    def reset(self, name):
        dom = self.get_vm(name, self.conn)
        try:
            dom.reset(flags=0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVM0022E",
                                  {'name': name, 'err': e.get_error_message()})

    def _vm_get_graphics(self, name):
        dom = self.get_vm(name, self.conn)
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

    def connect(self, name):
        # (type, listen, port, passwd, passwdValidTo)
        graphics_port = self._vm_get_graphics(name)[2]
        if graphics_port is not None:
            vnc.add_proxy_token(name, graphics_port)
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
            kimchi_log.error('Error trying to delete vm screenshot from '
                             'database due error: %s', e.message)


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
                session.store('screenshot', vm_uuid, screenshot.info)
        except Exception as e:
            # It is possible to continue Kimchi executions without store
            # screenshots
            kimchi_log.error('Error trying to update database with guest '
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
                    session.store('screenshot', vm_uuid, params)
        except Exception as e:
            # The 'except' outside of 'with' is necessary to catch possible
            # exception from '__exit__' when calling 'session.store'
            # It is possible to continue Kimchi vm executions without
            # screenshots
            kimchi_log.error('Error trying to update database with guest '
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
