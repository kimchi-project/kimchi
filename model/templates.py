#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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
import magic
import os
import platform
import psutil
import stat
import urlparse

from wok.exception import InvalidOperation, InvalidParameter
from wok.exception import NotFoundError, OperationFailed
from wok.utils import probe_file_permission_as_user, run_setfacl_set_attr
from wok.xmlutils.utils import xpath_get_text

from wok.plugins.kimchi.config import get_kimchi_version
from wok.plugins.kimchi.kvmusertests import UserTests
from wok.plugins.kimchi.model.cpuinfo import CPUInfoModel
from wok.plugins.kimchi.utils import is_libvirtd_up, pool_name_from_uri
from wok.plugins.kimchi.vmtemplate import VMTemplate

ISO_TYPE = "ISO 9660 CD-ROM"
# In PowerPC, memories must be aligned to 256 MiB
PPC_MEM_ALIGN = 256
# Max memory 16TB for PPC and 4TiB for X (according to Red Hat), in KiB
MAX_MEM_LIM = 4294967296    # 4 TiB
if os.uname()[4] in ['ppc', 'ppc64', 'ppc64le']:
    MAX_MEM_LIM *= 4     # 16TiB


class TemplatesModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']

    def create(self, params):
        name = params.get('name', '').strip()

        conn = self.conn.get()
        for net_name in params.get(u'networks', []):
            try:
                conn.networkLookupByName(net_name.encode('utf-8'))
            except Exception:
                raise InvalidParameter("KCHTMPL0003E", {'network': net_name,
                                                        'template': name})
        # Valid interfaces
        interfaces = params.get('interfaces', [])
        validate_interfaces(interfaces)

        # get source_media
        source_media = params.pop("source_media")

        if source_media['type'] == 'netboot':
            params['netboot'] = True
            return self.save_template(params)

        # Get path of source media if it's based on disk type.
        path = source_media.get('path', None)
        if path is None:
            raise InvalidParameter("KCHTMPL0016E")

        # not local image: set as remote ISO
        path = path.encode('utf-8')
        if urlparse.urlparse(path).scheme in ["http", "https", "tftp", "ftp",
                                              "ftps"]:
            params["cdrom"] = path
            return self.save_template(params)

        # Local file (ISO/Img) does not exist: raise error
        if not os.path.exists(path):
            raise InvalidParameter("KCHTMPL0002E", {'path': path})

        # create magic object to discover file type
        file_type = magic.open(magic.MAGIC_NONE)
        file_type.load()
        ftype = file_type.file(path)

        # cdrom
        if ISO_TYPE in ftype:
            params["cdrom"] = path

            # check search permission
            st_mode = os.stat(path).st_mode
            if stat.S_ISREG(st_mode) or stat.S_ISBLK(st_mode):
                user = UserTests().probe_user()
                run_setfacl_set_attr(path, user=user)
                ret, excp = probe_file_permission_as_user(path, user)
                if ret is False:
                    raise InvalidParameter('KCHISO0008E',
                                           {'filename': path, 'user': user,
                                            'err': excp})
        # disk
        else:
            params["disks"] = params.get('disks', [])
            params["disks"].append({"base": path})

        return self.save_template(params)

    def save_template(self, params):

        # Creates the template class with necessary information
        t = LibvirtVMTemplate(params, scan=True, conn=self.conn)

        # Validate cpu info
        t.cpuinfo_validate()

        # Validate memory
        t._validate_memory()

        # Validate volumes
        for disk in t.info.get('disks'):
            volume = disk.get('volume')
            # volume can be None
            if 'volume' in disk.keys():
                self.template_volume_validate(volume, disk['pool'])

        # template with the same name already exists: raise exception
        name = params['name']
        with self.objstore as session:
            if name in session.get_list('template'):
                raise InvalidOperation("KCHTMPL0001E", {'name': name})

        # Store template on objectstore
        try:
            with self.objstore as session:
                session.store('template', name, t.info,
                              get_kimchi_version())
        except InvalidOperation:
            raise
        except Exception, e:
            raise OperationFailed('KCHTMPL0020E', {'err': e.message})

        return name

    def get_list(self):
        if not is_libvirtd_up():
            return []

        with self.objstore as session:
            return session.get_list('template')

    def template_volume_validate(self, volume, pool):
        kwargs = {'conn': self.conn, 'objstore': self.objstore}
        pool_name = pool_name_from_uri(pool['name'])
        if pool['type'] in ['iscsi', 'scsi']:
            if not volume:
                raise InvalidParameter("KCHTMPL0018E")

            storagevolumes = __import__(
                "wok.plugins.kimchi.model.storagevolumes", fromlist=[''])
            pool_volumes = storagevolumes.StorageVolumesModel(
                **kwargs).get_list(pool_name)
            if volume not in pool_volumes:
                raise InvalidParameter("KCHTMPL0019E", {'pool': pool_name,
                                                        'volume': volume})


class TemplateModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']
        self.templates = TemplatesModel(**kargs)

    @staticmethod
    def get_template(name, objstore, conn, overrides=None):
        if overrides is None:
            overrides = {}

        with objstore as session:
            params = session.get('template', name)
        if overrides and 'storagepool' in overrides:
            for i, disk in enumerate(params['disks']):
                params['disks'][i]['pool']['name'] = overrides['storagepool']
            del overrides['storagepool']
        params.update(overrides)
        return LibvirtVMTemplate(params, False, conn)

    def lookup(self, name):
        t = self.get_template(name, self.objstore, self.conn)
        return t.validate_integrity()

    def clone(self, name):
        # set default name
        subfixs = [v[len(name):] for v in self.templates.get_list()
                   if v.startswith(name)]
        indexs = [int(v.lstrip("-clone")) for v in subfixs
                  if v.startswith("-clone") and
                  v.lstrip("-clone").isdigit()]
        indexs.sort()
        index = "1" if not indexs else str(indexs[-1] + 1)
        clone_name = name + "-clone" + index

        temp = self.lookup(name)
        temp['name'] = clone_name
        ident = self.templates.save_template(temp)
        return ident

    def delete(self, name):
        try:
            with self.objstore as session:
                session.delete('template', name)
        except NotFoundError:
            raise
        except Exception as e:
            raise OperationFailed('KCHTMPL0021E', {'err': e.message})

    def update(self, name, params):
        edit_template = self.lookup(name)

        # Valid interfaces
        interfaces = params.get('interfaces', [])
        validate_interfaces(interfaces)

        # Merge graphics settings
        graph_args = params.get('graphics')
        if graph_args:
            graphics = dict(edit_template['graphics'])
            graphics.update(graph_args)
            params['graphics'] = graphics

        # Merge cpu_info settings
        new_cpu_info = params.get('cpu_info')
        if new_cpu_info:
            cpu_info = dict(edit_template['cpu_info'])
            cpu_info.update(new_cpu_info)
            params['cpu_info'] = cpu_info

        # Fix memory values, because method update does not work recursively
        new_mem = params.get('memory')
        if new_mem is not None:
            params['memory'] = copy.copy(edit_template.get('memory'))
            params['memory'].update(new_mem)
            validate_memory(params['memory'])

        edit_template.update(params)

        for net_name in params.get(u'networks', []):
            try:
                conn = self.conn.get()
                conn.networkLookupByName(net_name.encode('utf-8'))
            except Exception:
                raise InvalidParameter("KCHTMPL0003E", {'network': net_name,
                                                        'template': name})

        try:
            # make sure the new template will be created
            t = LibvirtVMTemplate(edit_template, scan=True, conn=self.conn)
            t.cpuinfo_validate()
            t._validate_memory()

            # remove the current one
            self.delete(name)

            # save the template
            return self.templates.save_template(edit_template)

        except InvalidOperation:
            raise
        except Exception, e:
            raise OperationFailed('KCHTMPL0032E', {'err': e.message})

        return params['name']


def validate_interfaces(interfaces):
    #
    # Interfaces only supported on s390x or s390 architecture.
    # Otherwise FIXME to valid interfaces exist on system.
    #
    if os.uname()[4] not in ['s390x', 's390'] and interfaces:
        raise InvalidParameter("KCHTMPL0039E")
    # FIXME to valid interfaces on system.


def validate_memory(memory):
    #
    # All checking are made in Mib, so, expects memory values in Mib
    #
    current = memory.get('current')
    maxmem = memory.get('maxmemory')

    # Check Host Memory
    if hasattr(psutil, 'virtual_memory'):
        host_memory = psutil.virtual_memory().total >> 10 >> 10
    else:
        host_memory = psutil.TOTAL_PHYMEM >> 10 >> 10

    # Memories must be lesser than 16TiB (PPC) or 4TiB (x86) and the Host
    # memory limit
    if (current > (MAX_MEM_LIM >> 10)) or (maxmem > (MAX_MEM_LIM >> 10)):
        raise InvalidParameter("KCHVM0079E",
                               {'value': str(MAX_MEM_LIM / (1024**3))})
    if (current > host_memory) or (maxmem > host_memory):
        raise InvalidParameter("KCHVM0078E", {'memHost': host_memory})

    # Current memory cannot be greater than maxMemory
    if current > maxmem:
        raise InvalidParameter("KCHTMPL0031E",
                               {'mem': str(current),
                                'maxmem': str(maxmem)})

    # make sure memory and Maxmemory are alingned in 256MiB in PowerPC
    distro, _, _ = platform.linux_distribution()
    if distro == "IBM_PowerKVM":
        if current % PPC_MEM_ALIGN != 0:
            raise InvalidParameter('KCHVM0071E',
                                   {'param': "Memory",
                                    'mem': str(current),
                                    'alignment': str(PPC_MEM_ALIGN)})
        elif maxmem % PPC_MEM_ALIGN != 0:
            raise InvalidParameter('KCHVM0071E',
                                   {'param': "Maximum Memory",
                                    'mem': str(maxmem),
                                    'alignment': str(PPC_MEM_ALIGN)})


class LibvirtVMTemplate(VMTemplate):
    def __init__(self, args, scan=False, conn=None):
        self.conn = conn
        netboot = True if 'netboot' in args.keys() else False
        VMTemplate.__init__(self, args, scan, netboot)
        self.set_cpu_info()

    def _validate_memory(self):
        validate_memory(self.info['memory'])

    def cpuinfo_validate(self):
        cpu_model = CPUInfoModel(conn=self.conn)

        # validate CPU info values - will raise appropriate exceptions
        cpu_model.check_cpu_info(self.info['cpu_info'])

    def _get_storage_pool(self, pool_uri):
        pool_name = pool_name_from_uri(pool_uri)
        try:
            conn = self.conn.get()
            pool = conn.storagePoolLookupByName(pool_name.encode("utf-8"))

        except libvirt.libvirtError:
            raise InvalidParameter("KCHTMPL0004E", {'pool': pool_uri,
                                                    'template': self.name})

        return pool

    def _get_all_networks_name(self):
        conn = self.conn.get()
        return sorted(conn.listNetworks() + conn.listDefinedNetworks())

    def _get_all_storagepools_name(self):
        conn = self.conn.get()
        names = conn.listStoragePools() + conn.listDefinedStoragePools()
        return sorted(map(lambda x: x.decode('utf-8'), names))

    def _get_active_storagepools_name(self):
        conn = self.conn.get()
        names = conn.listStoragePools()
        return sorted(map(lambda x: x.decode('utf-8'), names))

    def _network_validate(self):
        names = self.info.get('networks', [])
        for name in names:
            try:
                conn = self.conn.get()
                network = conn.networkLookupByName(name.encode('utf-8'))
            except libvirt.libvirtError:
                raise InvalidParameter("KCHTMPL0003E", {'network': name,
                                                        'template': self.name})

            if not network.isActive():
                raise InvalidParameter("KCHTMPL0007E", {'network': name,
                                                        'template': self.name})

    def _get_storage_path(self, pool_uri=None):
        try:
            pool = self._get_storage_pool(pool_uri)

        except:
            return ''

        xml = pool.XMLDesc(0)
        return xpath_get_text(xml, "/pool/target/path")[0]

    def _get_storage_type(self, pool_uri=None):
        try:
            pool = self._get_storage_pool(pool_uri)

        except:
            return ''
        xml = pool.XMLDesc(0)
        return xpath_get_text(xml, "/pool/@type")[0]

    def _get_volume_path(self, pool, vol):
        pool = self._get_storage_pool(pool)
        try:
            return pool.storageVolLookupByName(vol).path()
        except:
            raise NotFoundError("KCHVOL0002E", {'name': vol,
                                                'pool': pool})

    def fork_vm_storage(self, vm_uuid):
        # Provision storages:
        vol_list = self.to_volume_list(vm_uuid)
        try:
            for v in vol_list:
                pool = self._get_storage_pool(v['pool'])
                # outgoing text to libvirt, encode('utf-8')
                pool.createXML(v['xml'].encode('utf-8'), 0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVMSTOR0008E", {'error': e.message})
        return vol_list

    def set_cpu_info(self):
        # undefined topology: consider these values to calculate maxvcpus
        sockets = 1
        cores = 1
        threads = 1

        # get topology values
        cpu_info = self.info.get('cpu_info', {})
        topology = cpu_info.get('topology', {})
        if topology:
            sockets = topology['sockets']
            cores = topology['cores']
            threads = topology['threads']

        # maxvcpus not specified: use defaults
        if 'maxvcpus' not in cpu_info:
            vcpus = cpu_info.get('vcpus')
            if vcpus and not topology:
                cpu_info['maxvcpus'] = vcpus
            else:
                cpu_info['maxvcpus'] = sockets * cores * threads

        # current vcpus not specified: defaults is maxvcpus
        if 'vcpus' not in cpu_info:
            cpu_info['vcpus'] = cpu_info['maxvcpus']

        # update cpu_info
        self.info['cpu_info'] = cpu_info
