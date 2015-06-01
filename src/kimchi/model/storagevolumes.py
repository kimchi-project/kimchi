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

import contextlib
import lxml.etree as ET
import os
import tempfile
import threading
import time
import urllib2
from lxml.builder import E

import libvirt

from kimchi.config import READONLY_POOL_TYPE
from kimchi.exception import InvalidOperation, InvalidParameter, IsoFormatError
from kimchi.exception import MissingParameter, NotFoundError, OperationFailed
from kimchi.isoinfo import IsoImage
from kimchi.model.diskutils import get_disk_used_by, set_disk_used_by
from kimchi.model.storagepools import StoragePoolModel
from kimchi.model.tasks import TaskModel
from kimchi.utils import add_task, get_next_clone_name, get_unique_file_name
from kimchi.utils import kimchi_log
from kimchi.xmlutils.utils import xpath_get_text


VOLUME_TYPE_MAP = {0: 'file',
                   1: 'block',
                   2: 'directory',
                   3: 'network'}

READ_CHUNK_SIZE = 1048576  # 1 MiB
REQUIRE_NAME_PARAMS = ['capacity']

upload_volumes = dict()


class StorageVolumesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)

    def create(self, pool_name, params):
        vol_source = ['url', 'capacity']

        name = params.get('name')

        index_list = list(i for i in range(len(vol_source))
                          if vol_source[i] in params)
        if len(index_list) != 1:
            raise InvalidParameter("KCHVOL0018E",
                                   {'param': ",".join(vol_source)})

        create_param = vol_source[index_list[0]]

        # Verify if the URL is valid
        if create_param == 'url':
            url = params['url']
            try:
                urllib2.urlopen(url).close()
            except:
                raise InvalidParameter('KCHVOL0022E', {'url': url})

        all_vol_names = self.get_list(pool_name)

        if name is None:
            # the methods listed in 'REQUIRE_NAME_PARAMS' cannot have
            # 'name' == None
            if create_param in REQUIRE_NAME_PARAMS:
                raise InvalidParameter('KCHVOL0016E')

            # if 'name' is omitted - except for the methods listed in
            # 'REQUIRE_NAME_PARAMS' - the default volume name will be the
            # file/URL basename.
            if create_param == 'url':
                name = os.path.basename(params['url'])
            else:
                name = 'upload-%s' % int(time.time())

            name = get_unique_file_name(all_vol_names, name)
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
        if name in all_vol_names:
            raise InvalidParameter('KCHVOL0001E', {'name': name})

        params['pool'] = pool_name
        targeturi = '/storagepools/%s/storagevolumes/%s' % (pool_name, name)
        taskid = add_task(targeturi, create_func, self.objstore, params)
        return self.task.lookup(taskid)

    def _create_volume_with_capacity(self, cb, params):
        pool_name = params.pop('pool')
        vol_xml = """
        <volume>
          <name>%(name)s</name>
          <allocation unit='bytes'>%(allocation)s</allocation>
          <capacity unit='bytes'>%(capacity)s</capacity>
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

        vol_info = StorageVolumeModel(conn=self.conn,
                                      objstore=self.objstore).lookup(pool_name,
                                                                     name)

        vol_path = vol_info['path']
        set_disk_used_by(self.objstore, vol_info['path'], [])

        if params.get('upload', False):
            upload_volumes[vol_path] = {'lock': threading.Lock(),
                                        'offset': 0, 'cb': cb}
            cb('ready for upload')
        else:
            cb('OK', True)

    def _create_volume_with_url(self, cb, params):
        pool_name = params['pool']
        name = params['name']
        url = params['url']

        pool_model = StoragePoolModel(conn=self.conn,
                                      objstore=self.objstore)
        pool = pool_model.lookup(pool_name)

        if pool['type'] in ['dir', 'netfs']:
            file_path = os.path.join(pool['path'], name)
        else:
            file_path = tempfile.mkstemp(prefix=name)[1]

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
                except (IOError, libvirt.libvirtError) as e:
                    if os.path.isfile(file_path):
                        os.remove(file_path)

                    raise OperationFailed('KCHVOL0007E', {'name': name,
                                                          'pool': pool_name,
                                                          'err': e.message})

        if pool['type'] in ['dir', 'netfs']:
            virt_pool = StoragePoolModel.get_storagepool(pool_name, self.conn)
            virt_pool.refresh(0)
        else:
            def _stream_handler(stream, nbytes, fd):
                return fd.read(nbytes)

            virt_stream = virt_vol = None

            try:
                task = self.create(pool_name, {'name': name,
                                               'format': 'raw',
                                               'capacity': downloaded_size,
                                               'allocation': downloaded_size})
                self.task.wait(task['id'])
                virt_vol = StorageVolumeModel.get_storagevolume(pool_name,
                                                                name,
                                                                self.conn)

                virt_stream = self.conn.get().newStream(0)
                virt_vol.upload(virt_stream, 0, downloaded_size, 0)

                with open(file_path) as fd:
                    virt_stream.sendAll(_stream_handler, fd)

                virt_stream.finish()
            except (IOError, libvirt.libvirtError) as e:
                try:
                    if virt_stream:
                        virt_stream.abort()
                    if virt_vol:
                        virt_vol.delete(0)
                except libvirt.libvirtError, virt_e:
                    kimchi_log.error(virt_e.message)
                finally:
                    raise OperationFailed('KCHVOL0007E', {'name': name,
                                                          'pool': pool_name,
                                                          'err': e.message})
            finally:
                os.remove(file_path)

        vol_info = StorageVolumeModel(conn=self.conn,
                                      objstore=self.objstore).lookup(pool_name,
                                                                     name)
        set_disk_used_by(self.objstore, vol_info['path'], [])

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
        self.task = TaskModel(**kargs)
        self.storagevolumes = StorageVolumesModel(**kargs)
        self.storagepool = StoragePoolModel(**kargs)

    @staticmethod
    def get_storagevolume(poolname, name, conn):
        pool = StoragePoolModel.get_storagepool(poolname, conn)
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

    def lookup(self, pool, name):
        vol = StorageVolumeModel.get_storagevolume(pool, name, self.conn)
        path = vol.path()
        info = vol.info()
        xml = vol.XMLDesc(0)
        try:
            fmt = xpath_get_text(xml, "/volume/target/format/@type")[0]
        except IndexError:
            # Not all types of libvirt storage can provide volume format
            # infomation. When there is no format information, we assume
            # it's 'raw'.
            fmt = 'raw'

        iso_img = None

        # 'raw' volumes from 'logical' pools may actually be 'iso';
        # libvirt always reports them as 'raw'
        pool_info = self.storagepool.lookup(pool)
        if pool_info['type'] == 'logical' and fmt == 'raw':
            try:
                iso_img = IsoImage(path)
            except IsoFormatError:
                # not 'iso' afterall
                pass
            else:
                fmt = 'iso'

        used_by = get_disk_used_by(self.objstore, self.conn, path)
        res = dict(type=VOLUME_TYPE_MAP[info[0]],
                   capacity=info[1],
                   allocation=info[2],
                   path=path,
                   used_by=used_by,
                   format=fmt)
        if fmt == 'iso':
            if os.path.islink(path):
                path = os.path.join(os.path.dirname(path), os.readlink(path))
            os_distro = os_version = 'unknown'
            try:
                if iso_img is None:
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
        volume = StorageVolumeModel.get_storagevolume(pool, name, self.conn)
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

        volume = StorageVolumeModel.get_storagevolume(pool, name, self.conn)
        try:
            volume.delete(0)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVOL0010E",
                                  {'name': name, 'err': e.get_error_message()})

    def resize(self, pool, name, size):
        volume = StorageVolumeModel.get_storagevolume(pool, name, self.conn)

        # When decreasing the storage volume capacity, the flag
        # VIR_STORAGE_VOL_RESIZE_SHRINK must be used
        flags = 0
        if volume.info()[1] > size:
            # FIXME: Even using VIR_STORAGE_VOL_RESIZE_SHRINK flag it is not
            # possible to decrease the volume capacity due a libvirt bug
            # For reference:
            # - https://bugzilla.redhat.com/show_bug.cgi?id=1021802
            flags = libvirt.VIR_STORAGE_VOL_RESIZE_SHRINK

        try:
            volume.resize(size, flags)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHVOL0011E",
                                  {'name': name, 'err': e.get_error_message()})

    def clone(self, pool, name, new_pool=None, new_name=None):
        """Clone a storage volume.

        Arguments:
        pool -- The name of the original pool.
        name -- The name of the original volume.
        new_pool -- The name of the destination pool (optional). If omitted,
            the new volume will be created on the same pool as the
            original one.
        new_name -- The name of the new volume (optional). If omitted, a new
            value based on the original volume's name will be used.

        Return:
        A Task running the clone operation.
        """
        # the same pool will be used if no pool is specified
        if new_pool is None:
            new_pool = pool

        # a default name based on the original name will be used if no name
        # is specified
        if new_name is None:
            base, ext = os.path.splitext(name)
            new_name = get_next_clone_name(self.storagevolumes.get_list(pool),
                                           base, ext)

        params = {'pool': pool,
                  'name': name,
                  'new_pool': new_pool,
                  'new_name': new_name}
        taskid = add_task(u'/storagepools/%s/storagevolumes/%s' %
                          (pool, new_name), self._clone_task, self.objstore,
                          params)
        return self.task.lookup(taskid)

    def _clone_task(self, cb, params):
        """Asynchronous function which performs the clone operation.

        This function copies all the data inside the original volume into the
        new one.

        Arguments:
        cb -- A callback function to signal the Task's progress.
        params -- A dict with the following values:
            "pool": The name of the original pool.
            "name": The name of the original volume.
            "new_pool": The name of the destination pool.
            "new_name": The name of the new volume.
        """
        orig_pool_name = params['pool']
        orig_vol_name = params['name']
        new_pool_name = params['new_pool']
        new_vol_name = params['new_name']

        try:
            cb('setting up volume cloning')
            orig_vir_vol = StorageVolumeModel.get_storagevolume(orig_pool_name,
                                                                orig_vol_name,
                                                                self.conn)
            orig_vol = self.lookup(orig_pool_name, orig_vol_name)
            new_vir_pool = StoragePoolModel.get_storagepool(new_pool_name,
                                                            self.conn)

            cb('building volume XML')
            root_elem = E.volume()
            root_elem.append(E.name(new_vol_name))
            root_elem.append(E.capacity(unicode(orig_vol['capacity']),
                                        unit='bytes'))
            target_elem = E.target()
            target_elem.append(E.format(type=orig_vol['format']))
            root_elem.append(target_elem)
            new_vol_xml = ET.tostring(root_elem, encoding='utf-8',
                                      pretty_print=True)

            cb('cloning volume')
            new_vir_pool.createXMLFrom(new_vol_xml, orig_vir_vol, 0)
        except (InvalidOperation, NotFoundError, libvirt.libvirtError), e:
            raise OperationFailed('KCHVOL0023E',
                                  {'name': orig_vol_name,
                                   'pool': orig_pool_name,
                                   'err': e.get_error_message()})

        new_vol = self.lookup(new_pool_name, new_vol_name)
        cb('adding volume to the object store')
        set_disk_used_by(self.objstore, new_vol['path'], [])

        cb('OK', True)

    def doUpload(self, cb, vol, offset, data, data_size):
        try:
            st = self.conn.get().newStream(0)
            vol.upload(st, offset, data_size)
            st.send(data)
            st.finish()
        except Exception as e:
            st and st.abort()
            cb('', False)

            try:
                vol.delete(0)
            except Exception as e:
                pass

            raise OperationFailed("KCHVOL0029E", {"err": e.message})

    def update(self, pool, name, params):
        chunk_data = params['chunk'].fullvalue()
        chunk_size = int(params['chunk_size'])

        if len(chunk_data) != chunk_size:
            raise OperationFailed("KCHVOL0026E")

        vol = StorageVolumeModel.get_storagevolume(pool, name, self.conn)
        vol_path = vol.path()
        vol_capacity = vol.info()[1]

        vol_data = upload_volumes.get(vol_path)
        if vol_data is None:
            raise OperationFailed("KCHVOL0027E", {"vol": vol_path})

        cb = vol_data['cb']
        lock = vol_data['lock']
        with lock:
            offset = vol_data['offset']
            if (offset + chunk_size) > vol_capacity:
                raise OperationFailed("KCHVOL0028E")

            cb('%s/%s' % (offset, vol_capacity))
            self.doUpload(cb, vol, offset, chunk_data, chunk_size)
            cb('%s/%s' % (offset + chunk_size, vol_capacity))

            vol_data['offset'] += chunk_size
            if vol_data['offset'] == vol_capacity:
                del upload_volumes[vol_path]
                cb('OK', True)


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
                if res['format'] == 'iso' and res['bootable']:
                    res['name'] = '%s' % volume
                    iso_volumes.append(res)
        return iso_volumes
