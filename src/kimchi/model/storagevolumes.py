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

import contextlib
import os
import time
import urllib2

import libvirt

from kimchi import xmlutils
from kimchi.config import READONLY_POOL_TYPE
from kimchi.exception import InvalidOperation, InvalidParameter, IsoFormatError
from kimchi.exception import MissingParameter, NotFoundError, OperationFailed
from kimchi.isoinfo import IsoImage
from kimchi.model.storagepools import StoragePoolModel
from kimchi.model.tasks import TaskModel
from kimchi.model.vms import VMsModel, VMModel
from kimchi.utils import add_task, kimchi_log
from kimchi.vmdisks import get_vm_disk, get_vm_disk_list


VOLUME_TYPE_MAP = {0: 'file',
                   1: 'block',
                   2: 'directory',
                   3: 'network'}


READ_CHUNK_SIZE = 1048576  # 1 MiB


REQUIRE_NAME_PARAMS = ['capacity']


class StorageVolumesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)

    def create(self, pool_name, params):
        vol_source = ['file', 'url', 'capacity']

        name = params.get('name')

        index_list = list(i for i in range(len(vol_source))
                          if vol_source[i] in params)
        if len(index_list) != 1:
            raise InvalidParameter("KCHVOL0018E",
                                   {'param': ",".join(vol_source)})

        create_param = vol_source[index_list[0]]

        if name is None:
            # the methods listed in 'REQUIRE_NAME_PARAMS' cannot have
            # 'name' == None
            if create_param in REQUIRE_NAME_PARAMS:
                raise InvalidParameter('KCHVOL0016E')

            # if 'name' is omitted - except for the methods listed in
            # 'REQUIRE_NAME_PARAMS' - the default volume name will be the
            # file/URL basename.
            if create_param == 'file':
                name = os.path.basename(params['file'].filename)
            elif create_param == 'url':
                name = os.path.basename(params['url'])
            else:
                name = 'upload-%s' % int(time.time())
            params['name'] = name

        try:
            create_func = getattr(self, '_create_volume_with_%s' %
                                        create_param)
        except AttributeError:
            raise InvalidParameter("KCHVOL0019E", {'param': create_param})

        pool_info = StoragePoolModel(conn=self.conn,
                                     objstore=self.objstore).lookup(pool_name)
        if pool_info['type'] in READONLY_POOL_TYPE:
            raise InvalidParameter("KCHVOL0012E", {'type': pool_info['type']})
        if pool_info['state'] == 'inactive':
            raise InvalidParameter('KCHVOL0003E', {'pool': pool_name,
                                                   'volume': name})
        if name in self.get_list(pool_name):
            raise InvalidParameter('KCHVOL0001E', {'name': name})

        params['pool'] = pool_name
        targeturi = '/storagepools/%s/storagevolumes/%s' % (pool_name, name)
        taskid = add_task(targeturi, create_func, self.objstore, params)
        return self.task.lookup(taskid)

    def _create_volume_with_file(self, cb, params):
        pool_name = params.pop('pool')
        dir_path = StoragePoolModel(
            conn=self.conn, objstore=self.objstore).lookup(pool_name)['path']
        file_path = os.path.join(dir_path, params['name'])
        if os.path.exists(file_path):
            raise InvalidParameter('KCHVOL0001E', {'name': params['name']})

        upload_file = params['file']
        f_len = upload_file.fp.length
        try:
            size = 0
            with open(file_path, 'wb') as f:
                while True:
                    data = upload_file.file.read(READ_CHUNK_SIZE)
                    if not data:
                        break
                    size += len(data)
                    f.write(data)
                    cb('%s/%s' % (size, f_len))
        except Exception as e:
            raise OperationFailed('KCHVOL0007E',
                                  {'name': params['name'],
                                   'pool': pool_name,
                                   'err': e.message})

        # Refresh to make sure volume can be found in following lookup
        StoragePoolModel.get_storagepool(pool_name, self.conn).refresh(0)
        cb('OK', True)

    def _create_volume_with_capacity(self, cb, params):
        pool_name = params.pop('pool')
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

        cb('', True)

    def _create_volume_with_url(self, cb, params):
        pool_name = params['pool']
        name = params['name']
        url = params['url']

        pool_model = StoragePoolModel(conn=self.conn,
                                      objstore=self.objstore)
        pool = pool_model.lookup(pool_name)
        file_path = os.path.join(pool['path'], name)

        with contextlib.closing(urllib2.urlopen(url)) as response:
            with open(file_path, 'w') as volume_file:
                remote_size = response.info().getheader('Content-Length', '-')
                downloaded_size = 0

                try:
                    while True:
                        chunk_data = response.read(READ_CHUNK_SIZE)
                        if not chunk_data:
                            break

                        volume_file.write(chunk_data)
                        downloaded_size += len(chunk_data)
                        cb('%s/%s' % (downloaded_size, remote_size))
                except Exception, e:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    raise OperationFailed('KCHVOL0007E', {'name': name,
                                                          'pool': pool_name,
                                                          'err': e.message})

        StoragePoolModel.get_storagepool(pool_name, self.conn).refresh(0)
        cb('OK', True)

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
