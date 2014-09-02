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

import os

import libvirt

from kimchi import xmlutils
from kimchi.config import READONLY_POOL_TYPE
from kimchi.exception import InvalidOperation, InvalidParameter, IsoFormatError
from kimchi.exception import MissingParameter, NotFoundError, OperationFailed
from kimchi.isoinfo import IsoImage
from kimchi.model.storagepools import StoragePoolModel
from kimchi.utils import kimchi_log
from kimchi.model.vms import VMsModel, VMModel
from kimchi.vmdisks import get_vm_disk, get_vm_disk_list


VOLUME_TYPE_MAP = {0: 'file',
                   1: 'block',
                   2: 'directory',
                   3: 'network'}


class StorageVolumesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']

    def create(self, pool_name, params):
        vol_source = ['file', 'url', 'capacity']

        index_list = list(i for i in range(len(vol_source))
                          if vol_source[i] in params)
        if len(index_list) != 1:
            raise InvalidParameter("KCHVOL0018E",
                                   {'param': ",".join(vol_source)})

        try:
            create_func = getattr(self, "_create_volume_with_" +
                                        vol_source[index_list[0]])
        except AttributeError:
            raise InvalidParameter("KCHVOL0019E",
                                   {'param': vol_source[index_list[0]]})
        return create_func(pool_name, params)

    def _create_volume_with_capacity(self, pool_name, params):
        vol_xml = """
        <volume>
          <name>%(name)s</name>
          <allocation unit="MiB">%(allocation)s</allocation>
          <capacity unit="MiB">%(capacity)s</capacity>
          <source>
          </source>
          <target>
            <format type='%(format)s'/>
          </target>
        </volume>
        """
        params.setdefault('allocation', 0)
        params.setdefault('format', 'qcow2')

        name = params['name']
        vol_id = '%s:%s' % (pool_name, name)
        try:
            pool = StoragePoolModel.get_storagepool(pool_name, self.conn)
            xml = vol_xml % params
        except KeyError, item:
            raise MissingParameter("KCHVOL0004E", {'item': str(item),
                                                   'volume': name})

        pool_info = StoragePoolModel(conn=self.conn,
                                     objstore=self.objstore).lookup(pool_name)
        if pool_info['type'] in READONLY_POOL_TYPE:
            raise InvalidParameter("KCHVOL0012E", {'type': pool_info['type']})
        try:
            pool.createXML(xml, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVOL0007E",
                                  {'name': name, 'pool': pool,
                                   'err': e.get_error_message()})

        try:
            with self.objstore as session:
                session.store('storagevolume', vol_id, {'ref_cnt': 0})
        except Exception as e:
            # If the storage volume was created flawlessly, then lets hide this
            # error to avoid more error in the VM creation process
            kimchi_log.warning('Unable to store storage volume id in '
                               'objectstore due error: %s', e.message)

        return name

    def get_list(self, pool_name):
        pool = StoragePoolModel.get_storagepool(pool_name, self.conn)
        if not pool.isActive():
            raise InvalidOperation("KCHVOL0006E", {'pool': pool_name})
        try:
            pool.refresh(0)
            return sorted(map(lambda x: x.decode('utf-8'), pool.listVolumes()))
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVOL0008E",
                                  {'pool': pool_name,
                                   'err': e.get_error_message()})


class StorageVolumeModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']

    def _get_storagevolume(self, poolname, name):
        pool = StoragePoolModel.get_storagepool(poolname, self.conn)
        if not pool.isActive():
            raise InvalidOperation("KCHVOL0006E", {'name': pool})
        try:
            return pool.storageVolLookupByName(name.encode("utf-8"))
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                raise NotFoundError("KCHVOL0002E", {'name': name,
                                                    'pool': poolname})
            else:
                raise

    def _get_ref_cnt(self, pool, name, path):
        vol_id = '%s:%s' % (pool, name)
        try:
            with self.objstore as session:
                try:
                    ref_cnt = session.get('storagevolume', vol_id)['ref_cnt']
                except NotFoundError:
                    # Fix storage volume created outside kimchi scope
                    ref_cnt = 0
                    # try to find this volume in exsisted vm
                    vms = VMsModel.get_vms(self.conn)
                    for vm in vms:
                        dom = VMModel.get_vm(vm, self.conn)
                        storages = get_vm_disk_list(dom)
                        for disk in storages:
                            d_info = get_vm_disk(dom, disk)
                            if path == d_info['path']:
                                ref_cnt = ref_cnt + 1
                    session.store('storagevolume', vol_id,
                                  {'ref_cnt': ref_cnt})
        except Exception as e:
            # This exception is going to catch errors returned by 'with',
            # specially ones generated by 'session.store'. It is outside
            # to avoid conflict with the __exit__ function of 'with'
            raise OperationFailed('KCHVOL0017E', {'err': e.message})

        return ref_cnt

    def lookup(self, pool, name):
        vol = self._get_storagevolume(pool, name)
        path = vol.path()
        info = vol.info()
        xml = vol.XMLDesc(0)
        try:
            fmt = xmlutils.xpath_get_text(
                xml, "/volume/target/format/@type")[0]
        except IndexError:
            # Not all types of libvirt storage can provide volume format
            # infomation. When there is no format information, we assume
            # it's 'raw'.
            fmt = 'raw'
        ref_cnt = self._get_ref_cnt(pool, name, path)
        res = dict(type=VOLUME_TYPE_MAP[info[0]],
                   capacity=info[1],
                   allocation=info[2],
                   path=path,
                   ref_cnt=ref_cnt,
                   format=fmt)
        if fmt == 'iso':
            if os.path.islink(path):
                path = os.path.join(os.path.dirname(path), os.readlink(path))
            os_distro = os_version = 'unknown'
            try:
                iso_img = IsoImage(path)
                os_distro, os_version = iso_img.probe()
                bootable = True
            except IsoFormatError:
                bootable = False
            res.update(
                dict(os_distro=os_distro, os_version=os_version, path=path,
                     bootable=bootable))

        return res

    def wipe(self, pool, name):
        volume = self._get_storagevolume(pool, name)
        try:
            volume.wipePattern(libvirt.VIR_STORAGE_VOL_WIPE_ALG_ZERO, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVOL0009E",
                                  {'name': name, 'err': e.get_error_message()})

    def delete(self, pool, name):
        pool_info = StoragePoolModel(conn=self.conn,
                                     objstore=self.objstore).lookup(pool)
        if pool_info['type'] in READONLY_POOL_TYPE:
            raise InvalidParameter("KCHVOL0012E", {'type': pool_info['type']})

        volume = self._get_storagevolume(pool, name)
        try:
            volume.delete(0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVOL0010E",
                                  {'name': name, 'err': e.get_error_message()})

    def resize(self, pool, name, size):
        size = size << 20
        volume = self._get_storagevolume(pool, name)
        try:
            volume.resize(size, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVOL0011E",
                                  {'name': name, 'err': e.get_error_message()})


class IsoVolumesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.storagevolume = StorageVolumeModel(**kargs)

    def get_list(self):
        iso_volumes = []
        conn = self.conn.get()
        pools = conn.listStoragePools()
        pools += conn.listDefinedStoragePools()

        for pool_name in pools:
            try:
                pool = StoragePoolModel.get_storagepool(pool_name, self.conn)
                pool.refresh(0)
                volumes = pool.listVolumes()
            except Exception, e:
                # Skip inactive pools
                kimchi_log.debug("Shallow scan: skipping pool %s because of "
                                 "error: %s", (pool_name, e.message))
                continue

            for volume in volumes:
                res = self.storagevolume.lookup(pool_name,
                                                volume.decode("utf-8"))
                if res['format'] == 'iso':
                    res['name'] = '%s' % volume
                    iso_volumes.append(res)
        return iso_volumes
