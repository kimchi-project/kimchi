#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
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
import os
import stat

import libvirt

from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.kvmusertests import UserTests
from kimchi.model.cpuinfo import CPUInfoModel
from kimchi.utils import pool_name_from_uri
from kimchi.utils import probe_file_permission_as_user, run_setfacl_set_attr
from kimchi.vmtemplate import VMTemplate
from kimchi.xmlutils.utils import xpath_get_text


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

        cpu_info = params.get('cpu_info')
        if cpu_info:
            topology = cpu_info.get('topology')
            # Check, even though currently only topology
            #   is supported.
            if topology:
                sockets = topology['sockets']
                cores = topology['cores']
                threads = topology['threads']
                if params.get('cpus') is None:
                    params['cpus'] = sockets * cores * threads
                # check_topoology will raise the appropriate
                # exception if a topology is invalid.
                CPUInfoModel(conn=self.conn).\
                    check_topology(params['cpus'], topology)

        conn = self.conn.get()
        pool_uri = params.get(u'storagepool', '')
        if pool_uri:
            try:
                pool_name = pool_name_from_uri(pool_uri)
                pool = conn.storagePoolLookupByName(pool_name.encode("utf-8"))
            except Exception:
                raise InvalidParameter("KCHTMPL0004E", {'pool': pool_name,
                                                        'template': name})

            tmp_volumes = [disk['volume'] for disk in params.get('disks', [])
                           if 'volume' in disk]
            self.template_volume_validate(tmp_volumes, pool)

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
        name = params['name']
        try:
            with self.objstore as session:
                if name in session.get_list('template'):
                    raise InvalidOperation("KCHTMPL0001E", {'name': name})
                session.store('template', name, t.info)
        except InvalidOperation:
            raise
        except Exception, e:
            raise OperationFailed('KCHTMPL0020E', {'err': e.message})

        return name

    def get_list(self):
        with self.objstore as session:
            return session.get_list('template')

    def template_volume_validate(self, tmp_volumes, pool):
        kwargs = {'conn': self.conn, 'objstore': self.objstore}
        pool_type = xpath_get_text(pool.XMLDesc(0), "/pool/@type")[0]
        pool_name = unicode(pool.name(), 'utf-8')

        # as we discussion, we do not mix disks from 2 different types of
        # storage pools, for instance: we do not create a template with 2
        # disks, where one comes from a SCSI pool and other is a .img in
        # a DIR pool.
        if pool_type in ['iscsi', 'scsi']:
            if not tmp_volumes:
                raise InvalidParameter("KCHTMPL0018E")

            storagevolumes = __import__("kimchi.model.storagevolumes",
                                        fromlist=[''])
            pool_volumes = storagevolumes.StorageVolumesModel(
                **kwargs).get_list(pool_name)
            vols = set(tmp_volumes) - set(pool_volumes)
            if vols:
                raise InvalidParameter("KCHTMPL0019E", {'pool': pool_name,
                                                        'volume': vols})


class TemplateModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']
        self.templates = TemplatesModel(**kargs)

    @staticmethod
    def get_template(name, objstore, conn, overrides=None):
        with objstore as session:
            params = session.get('template', name)
        if overrides:
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
        new_t.update(params)

        if not self._validate_updated_cpu_params(new_t):
            raise InvalidParameter('KCHTMPL0025E')

        ident = name

        conn = self.conn.get()
        pool_uri = new_t.get(u'storagepool', '')

        if pool_uri:
            try:
                pool_name = pool_name_from_uri(pool_uri)
                pool = conn.storagePoolLookupByName(pool_name.encode("utf-8"))
            except Exception:
                raise InvalidParameter("KCHTMPL0004E", {'pool': pool_name,
                                                        'template': name})
            tmp_volumes = [disk['volume'] for disk in new_t.get('disks', [])
                           if 'volume' in disk]
            self.templates.template_volume_validate(tmp_volumes, pool)

        for net_name in params.get(u'networks', []):
            try:
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

    def _validate_updated_cpu_params(self, info):
        # Note: cpu_info is the parent of topology. cpus is vcpus
        vcpus = info['cpus']
        cpu_info = info.get('cpu_info')
        # cpu_info will always be at least an empty dict
        topology = cpu_info.get('topology')
        if topology is None:
            return True
        return vcpus == topology['sockets'] * topology['cores'] * \
            topology['threads']


class LibvirtVMTemplate(VMTemplate):
    def __init__(self, args, scan=False, conn=None):
        self.conn = conn
        VMTemplate.__init__(self, args, scan)

    def _storage_validate(self):
        pool_uri = self.info['storagepool']
        pool_name = pool_name_from_uri(pool_uri)
        try:
            conn = self.conn.get()
            pool = conn.storagePoolLookupByName(pool_name.encode("utf-8"))
        except libvirt.libvirtError:
            raise InvalidParameter("KCHTMPL0004E", {'pool': pool_name,
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

    def _get_storage_path(self):
        pool = self._storage_validate()
        xml = pool.XMLDesc(0)
        return xpath_get_text(xml, "/pool/target/path")[0]

    def _get_storage_type(self):
        pool = self._storage_validate()
        xml = pool.XMLDesc(0)
        return xpath_get_text(xml, "/pool/@type")[0]

    def _get_volume_path(self, pool, vol):
        pool = self._storage_validate()
        try:
            return pool.storageVolLookupByName(vol).path()
        except:
            raise NotFoundError("KCHVOL0002E", {'name': vol,
                                                'pool': pool})

    def fork_vm_storage(self, vm_uuid):
        # Provision storage:
        # TODO: Rebase on the storage API once upstream
        pool = self._storage_validate()
        vol_list = self.to_volume_list(vm_uuid)
        try:
            for v in vol_list:
                # outgoing text to libvirt, encode('utf-8')
                pool.createXML(v['xml'].encode('utf-8'), 0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVMSTOR0008E", {'error': e.message})
        return vol_list
