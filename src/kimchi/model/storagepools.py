#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

import libvirt

from kimchi import xmlutils
from kimchi.scan import Scanner
from kimchi.exception import InvalidOperation, MissingParameter
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.model.config import CapabilitiesModel
from kimchi.model.host import DeviceModel
from kimchi.model.libvirtstoragepool import StoragePoolDef
from kimchi.utils import add_task, kimchi_log
from kimchi.utils import run_command


ISO_POOL_NAME = u'kimchi_isos'
POOL_STATE_MAP = {0: 'inactive',
                  1: 'initializing',
                  2: 'active',
                  3: 'degraded',
                  4: 'inaccessible'}

STORAGE_SOURCES = {'netfs': {'addr': '/pool/source/host/@name',
                             'path': '/pool/source/dir/@path'},
                   'scsi': {'adapter_type': '/pool/source/adapter/@type',
                            'adapter_name': '/pool/source/adapter/@name',
                            'wwnn': '/pool/source/adapter/@wwnn',
                            'wwpn': '/pool/source/adapter/@wwpn'}}


class StoragePoolsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.scanner = Scanner(self._clean_scan)
        self.scanner.delete()
        self.caps = CapabilitiesModel()
        self.device = DeviceModel(**kargs)

    def get_list(self):
        try:
            conn = self.conn.get()
            names = conn.listStoragePools()
            names += conn.listDefinedStoragePools()
            return sorted(map(lambda x: x.decode('utf-8'), names))
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHPOOL0006E",
                                  {'err': e.get_error_message()})

    def create(self, params):
        task_id = None
        conn = self.conn.get()
        try:
            name = params['name']
            if name in (ISO_POOL_NAME, ):
                raise InvalidOperation("KCHPOOL0001E", {'name': name})

            if params['type'] == 'kimchi-iso':
                task_id = self._do_deep_scan(params)

            if params['type'] == 'scsi':
                adapter_name = params['source']['adapter_name']
                extra_params = self.device.lookup(adapter_name)
                # Adds name, adapter_type, wwpn and wwnn to source information
                params['source'].update(extra_params)
                params['fc_host_support'] = self.caps.fc_host_support

            poolDef = StoragePoolDef.create(params)
            poolDef.prepare(conn)
            xml = poolDef.xml.encode("utf-8")
        except KeyError, item:
            raise MissingParameter("KCHPOOL0004E",
                                   {'item': item, 'name': name})

        if name in self.get_list():
            raise InvalidOperation("KCHPOOL0001E", {'name': name})

        try:
            if task_id:
                # Create transient pool for deep scan
                conn.storagePoolCreateXML(xml, 0)
                return name

            pool = conn.storagePoolDefineXML(xml, 0)
            if params['type'] in ['logical', 'dir', 'netfs', 'scsi']:
                pool.build(libvirt.VIR_STORAGE_POOL_BUILD_NEW)
                # autostart dir, logical, netfs and scsi storage pools created
                # from kimchi
                pool.setAutostart(1)
            else:
                # disable autostart for others
                pool.setAutostart(0)
        except libvirt.libvirtError as e:
            kimchi_log.error("Problem creating Storage Pool: %s", e)
            raise OperationFailed("KCHPOOL0007E",
                                  {'name': name, 'err': e.get_error_message()})
        return name

    def _clean_scan(self, pool_name):
        try:
            conn = self.conn.get()
            pool = conn.storagePoolLookupByName(pool_name.encode("utf-8"))
            pool.destroy()
            with self.objstore as session:
                session.delete('scanning', pool_name)
        except Exception, e:
            err = "Exception %s occured when cleaning scan result"
            kimchi_log.debug(err % e.message)

    def _do_deep_scan(self, params):
        scan_params = dict(ignore_list=[])
        scan_params['scan_path'] = params['path']
        params['type'] = 'dir'

        for pool in self.get_list():
            try:
                res = self.storagepool_lookup(pool)
                if res['state'] == 'active':
                    scan_params['ignore_list'].append(res['path'])
            except Exception, e:
                err = "Exception %s occured when get ignore path"
                kimchi_log.debug(err % e.message)

        params['path'] = self.scanner.scan_dir_prepare(params['name'])
        scan_params['pool_path'] = params['path']
        task_id = add_task('', self.scanner.start_scan, self.objstore,
                           scan_params)
        # Record scanning-task/storagepool mapping for future querying
        with self.objstore as session:
                session.store('scanning', params['name'], task_id)
        return task_id


class StoragePoolModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']

    @staticmethod
    def get_storagepool(name, conn):
        conn = conn.get()
        try:
            return conn.storagePoolLookupByName(name.encode("utf-8"))
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_POOL:
                raise NotFoundError("KCHTMPL0002E", {'name': name})
            else:
                raise

    def _get_storagepool_vols_num(self, pool):
        try:
            if pool.isActive():
                pool.refresh(0)
                return pool.numOfVolumes()
            else:
                return 0
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHPOOL0008E",
                                  {'name': pool, 'err': e.get_error_message()})

    def _get_storage_source(self, pool_type, pool_xml):
        source = {}
        if pool_type not in STORAGE_SOURCES:
            return source

        for key, val in STORAGE_SOURCES[pool_type].items():
            res = xmlutils.xpath_get_text(pool_xml, val)
            if len(res) == 1:
                source[key] = res[0]
            elif len(res) == 0:
                source[key] = ""
            else:
                souce[key] = res

        return source

    def lookup(self, name):
        pool = self.get_storagepool(name, self.conn)
        info = pool.info()
        nr_volumes = self._get_storagepool_vols_num(pool)
        autostart = True if pool.autostart() else False
        xml = pool.XMLDesc(0)
        path = xmlutils.xpath_get_text(xml, "/pool/target/path")[0]
        pool_type = xmlutils.xpath_get_text(xml, "/pool/@type")[0]
        source = self._get_storage_source(pool_type, xml)
        res = {'state': POOL_STATE_MAP[info[0]],
               'path': path,
               'source': source,
               'type': pool_type,
               'autostart': autostart,
               'capacity': info[1],
               'allocated': info[2],
               'available': info[3],
               'nr_volumes': nr_volumes}

        if not pool.isPersistent():
            # Deal with deep scan generated pool
            try:
                with self.objstore as session:
                    task_id = session.get('scanning', name)
                res['task_id'] = str(task_id)
                res['type'] = 'kimchi-iso'
            except NotFoundError:
                # User created normal pool
                pass
        return res

    def _update_lvm_disks(self, pool_name, disks):
        # check if all the disks/partitions exists in the host
        for disk in disks:
            blkid_cmd = ['blkid', disk]
            output, error, returncode = run_command(blkid_cmd)
            if returncode != 0:
                kimchi_log.error('%s is not a valid disk/partition. Could not '
                                 'add it to the pool %s.', disk, pool_name)
                raise OperationFailed('KCHPOOL0027E', {'disk': disk,
                                                       'pool': pool_name})
        # add disks to the lvm pool using vgextend + virsh refresh
        vgextend_cmd = ["vgextend", pool_name]
        vgextend_cmd += disks
        output, error, returncode = run_command(vgextend_cmd)
        if returncode != 0:
            msg = "Could not add disks to pool %s, error: %s"
            kimchi_log.error(msg, pool_name, error)
            raise OperationFailed('KCHPOOL0028E', {'pool': pool_name,
                                                   'err': error})
        # refreshing pool state
        pool = self.get_storagepool(pool_name, self.conn)
        pool.refresh(0)

    def update(self, name, params):
        pool = self.get_storagepool(name, self.conn)
        if 'autostart' in params:
            if params['autostart']:
                pool.setAutostart(1)
            else:
                pool.setAutostart(0)
        if 'disks' in params:
            # check if pool is type 'logical'
            xml = pool.XMLDesc(0)
            pool_type = xmlutils.xpath_get_text(xml, "/pool/@type")[0]
            if pool_type != 'logical':
                raise InvalidOperation('KCHPOOL0029E')
            self._update_lvm_disks(name, params['disks'])
        ident = pool.name()
        return ident

    def activate(self, name):
        pool = self.get_storagepool(name, self.conn)
        try:
            pool.create(0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHPOOL0009E",
                                  {'name': name, 'err': e.get_error_message()})

    def deactivate(self, name):
        pool = self.get_storagepool(name, self.conn)
        try:
            pool.destroy()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHPOOL0010E",
                                  {'name': name, 'err': e.get_error_message()})

    def delete(self, name):
        pool = self.get_storagepool(name, self.conn)
        if pool.isActive():
            raise InvalidOperation("KCHPOOL0005E", {'name': name})
        try:
            pool.undefine()
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHPOOL0011E",
                                  {'name': name, 'err': e.get_error_message()})


class IsoPoolModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        return {'state': 'active',
                'type': 'kimchi-iso'}
