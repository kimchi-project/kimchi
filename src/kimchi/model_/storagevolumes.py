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

import os

import libvirt

from kimchi import xmlutils
from kimchi.exception import InvalidOperation, IsoFormatError
from kimchi.exception import MissingParameter, NotFoundError, OperationFailed
from kimchi.isoinfo import IsoImage
from kimchi.model_.storagepools import StoragePoolModel


VOLUME_TYPE_MAP = {0: 'file',
                   1: 'block',
                   2: 'directory',
                   3: 'network'}


class StorageVolumesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def create(self, pool, params):
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

        try:
            pool = StoragePoolModel.get_storagepool(pool, self.conn)
            name = params['name']
            xml = vol_xml % params
        except KeyError, key:
            raise MissingParameter(key)

        try:
            pool.createXML(xml, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())
        return name

    def get_list(self, pool):
        pool = StoragePoolModel.get_storagepool(pool, self.conn)
        if not pool.isActive():
            err = "Unable to list volumes in inactive storagepool %s"
            raise InvalidOperation(err % pool.name())
        try:
            pool.refresh(0)
            return pool.listVolumes()
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())


class StorageVolumeModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def _get_storagevolume(self, pool, name):
        pool = StoragePoolModel.get_storagepool(pool, self.conn)
        if not pool.isActive():
            err = "Unable to list volumes in inactive storagepool %s"
            raise InvalidOperation(err % pool.name())
        try:
            return pool.storageVolLookupByName(name)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                raise NotFoundError("Storage Volume '%s' not found" % name)
            else:
                raise

    def lookup(self, pool, name):
        vol = self._get_storagevolume(pool, name)
        path = vol.path()
        info = vol.info()
        xml = vol.XMLDesc(0)
        fmt = xmlutils.xpath_get_text(xml, "/volume/target/format/@type")[0]
        res = dict(type=VOLUME_TYPE_MAP[info[0]],
                   capacity=info[1],
                   allocation=info[2],
                   path=path,
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
            raise OperationFailed(e.get_error_message())

    def delete(self, pool, name):
        volume = self._get_storagevolume(pool, name)
        try:
            volume.delete(0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def resize(self, pool, name, size):
        size = size << 20
        volume = self._get_storagevolume(pool, name)
        try:
            volume.resize(size, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())


class IsoVolumesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.storagevolume = StorageVolumeModel(**kargs)

    def get_list(self):
        iso_volumes = []
        conn = self.conn.get()
        pools = conn.listStoragePools()
        pools += conn.listDefinedStoragePools()

        for pool in pools:
            try:
                pool.refresh(0)
                volumes = pool.listVolumes()
            except InvalidOperation:
                # Skip inactive pools
                continue

            for volume in volumes:
                res = self.storagevolume.lookup(pool, volume)
                if res['format'] == 'iso':
                    res['name'] = '%s' % volume
                    iso_volumes.append(res)
        return iso_volumes
