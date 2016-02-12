#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2016
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
import os
import stat

from wok.exception import InvalidOperation, InvalidParameter
from wok.exception import NotFoundError, OperationFailed
from wok.utils import probe_file_permission_as_user, run_setfacl_set_attr
from wok.xmlutils.utils import xpath_get_text

from wok.plugins.kimchi.config import get_kimchi_version
from wok.plugins.kimchi.kvmusertests import UserTests
from wok.plugins.kimchi.model.cpuinfo import CPUInfoModel
from wok.plugins.kimchi.utils import pool_name_from_uri
from wok.plugins.kimchi.vmtemplate import VMTemplate


class TemplatesModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']

    def create(self, params):
        name = params.get('name', '').strip()
        iso = params.get('cdrom')
        # check search permission
        if iso and iso.startswith('/') and os.path.exists(iso):
            st_mode = os.stat(iso).st_mode
            if stat.S_ISREG(st_mode) or stat.S_ISBLK(st_mode):
                user = UserTests().probe_user()
                run_setfacl_set_attr(iso, user=user)
                ret, excp = probe_file_permission_as_user(iso, user)
                if ret is False:
                    raise InvalidParameter('KCHISO0008E',
                                           {'filename': iso, 'user': user,
                                            'err': excp})

        conn = self.conn.get()
        for net_name in params.get(u'networks', []):
            try:
                conn.networkLookupByName(net_name.encode('utf-8'))
            except Exception:
                raise InvalidParameter("KCHTMPL0003E", {'network': net_name,
                                                        'template': name})
        # Creates the template class with necessary information
        # Checkings will be done while creating this class, so any exception
        # will be raised here
        t = LibvirtVMTemplate(params, scan=True, conn=self.conn)

        # Validate cpu info
        t.cpuinfo_validate()

        # Validate max memory
        maxMem = (t._get_max_memory(t.info.get('memory')) >> 10)
        if t.info.get('memory') > maxMem:
            raise OperationFailed("KCHVM0041E", {'maxmem': str(maxMem)})

        # Validate volumes
        for disk in t.info.get('disks'):
            volume = disk.get('volume')
            # volume can be None
            if 'volume' in disk.keys():
                self.template_volume_validate(volume, disk['pool'])

        # Store template on objectstore
        name = params['name']
        try:
            with self.objstore as session:
                if name in session.get_list('template'):
                    raise InvalidOperation("KCHTMPL0001E", {'name': name})
                session.store('template', name, t.info,
                              get_kimchi_version())
        except InvalidOperation:
            raise
        except Exception, e:
            raise OperationFailed('KCHTMPL0020E', {'err': e.message})

        return name

    def get_list(self):
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
    def get_template(name, objstore, conn, overrides={}):
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
        ident = self.templates.create(temp)
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
        old_t = self.lookup(name)
        new_t = copy.copy(old_t)

        # Merge graphics settings
        graph_args = params.get('graphics')
        if graph_args:
            graphics = dict(new_t['graphics'])
            graphics.update(graph_args)
            params['graphics'] = graphics

        # Merge cpu_info settings
        new_cpu_info = params.get('cpu_info')
        if new_cpu_info:
            cpu_info = dict(new_t['cpu_info'])
            cpu_info.update(new_cpu_info)
            params['cpu_info'] = cpu_info

        new_t.update(params)

        for net_name in params.get(u'networks', []):
            try:
                conn = self.conn.get()
                conn.networkLookupByName(net_name.encode('utf-8'))
            except Exception:
                raise InvalidParameter("KCHTMPL0003E", {'network': net_name,
                                                        'template': name})

        self.delete(name)
        try:
            ident = self.templates.create(new_t)
        except:
            ident = self.templates.create(old_t)
            raise
        return ident


class LibvirtVMTemplate(VMTemplate):
    def __init__(self, args, scan=False, conn=None):
        self.conn = conn
        VMTemplate.__init__(self, args, scan)
        self.set_cpu_info()

    def cpuinfo_validate(self):
        cpu_model = CPUInfoModel(conn=self.conn)

        # validate CPU info values - will raise appropriate exceptions
        cpu_model.check_cpu_info(self.info['cpu_info'])

    def _storage_validate(self, pool_uri):
        pool_name = pool_name_from_uri(pool_uri)
        try:
            conn = self.conn.get()
            pool = conn.storagePoolLookupByName(pool_name.encode("utf-8"))
        except libvirt.libvirtError:
            raise InvalidParameter("KCHTMPL0004E", {'pool': pool_uri,
                                                    'template': self.name})

        if not pool.isActive():
            raise InvalidParameter("KCHTMPL0005E", {'pool': pool_name,
                                                    'template': self.name})

        return pool

    def _get_all_networks_name(self):
        conn = self.conn.get()
        return sorted(conn.listNetworks() + conn.listDefinedNetworks())

    def _get_all_storagepools_name(self):
        conn = self.conn.get()
        names = conn.listStoragePools() + conn.listDefinedStoragePools()
        return sorted(map(lambda x: x.decode('utf-8'), names))

    def _network_validate(self):
        names = self.info['networks']
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
        pool = self._storage_validate(pool_uri)
        xml = pool.XMLDesc(0)
        return xpath_get_text(xml, "/pool/target/path")[0]

    def _get_storage_type(self, pool_uri=None):
        pool = self._storage_validate(pool_uri)
        xml = pool.XMLDesc(0)
        return xpath_get_text(xml, "/pool/@type")[0]

    def _get_volume_path(self, pool, vol):
        pool = self._storage_validate(pool)
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
                pool = self._storage_validate(v['pool'])
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
