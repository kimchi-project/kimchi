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

import libvirt
import lxml.etree as ET
from lxml import objectify
from lxml.builder import E

from kimchi.model.config import CapabilitiesModel
from kimchi.model.storageservers import STORAGE_SERVERS
from kimchi.utils import kimchi_log, patch_find_nfs_target


class StorageTargetsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.caps = CapabilitiesModel(**kargs)

    def get_list(self, storage_server, _target_type=None, _server_port=None):
        target_list = list()
        if not _target_type:
            target_types = STORAGE_SERVERS
        else:
            target_types = [_target_type]

        for target_type in target_types:
            if not self.caps.nfs_target_probe and target_type == 'netfs':
                targets = patch_find_nfs_target(storage_server)
            else:
                xml = self._get_storage_server_spec(server=storage_server,
                                                    target_type=target_type,
                                                    server_port=_server_port)
                conn = self.conn.get()
                try:
                    ret = conn.findStoragePoolSources(target_type, xml, 0)
                except libvirt.libvirtError as e:
                    err = "Query storage pool source fails because of %s"
                    kimchi_log.warning(err, e.get_error_message())
                    continue

                targets = self._parse_target_source_result(target_type, ret)

            target_list.extend(targets)

        # Get all netfs and iscsi paths in use
        used_paths = []
        try:
            conn = self.conn.get()
            # Get all existing ISCSI and NFS pools
            pools = conn.listAllStoragePools(
                libvirt.VIR_CONNECT_LIST_STORAGE_POOLS_ISCSI |
                libvirt.VIR_CONNECT_LIST_STORAGE_POOLS_NETFS)
            for pool in pools:
                pool_xml = pool.XMLDesc(0)
                root = objectify.fromstring(pool_xml)
                if root.get('type') == 'netfs' and \
                        root.source.dir is not None:
                    used_paths.append(root.source.dir.get('path'))
                elif root.get('type') == 'iscsi' and \
                        root.source.device is not None:
                    used_paths.append(root.source.device.get('path'))

        except libvirt.libvirtError as e:
            err = "Query storage pool source fails because of %s"
            kimchi_log.warning(err, e.get_error_message())

        # Filter target_list to not not show the used paths
        target_list = [elem for elem in target_list
                       if elem.get('target') not in used_paths]
        return [dict(t) for t in set(tuple(t.items()) for t in target_list)]

    def _get_storage_server_spec(self, **kwargs):
        # Required parameters:
        # server:
        # target_type:
        extra_args = []
        server_type = kwargs['target_type']
        if server_type == 'netfs':
            extra_args.append(E.format(type='nfs'))
        else:
            extra_args.append(E.format(type=server_type))

        host_attr = {"name": kwargs['server']}
        server_port = kwargs.get("server_port")
        if server_port is not None:
            host_attr['port'] = server_port

        obj = E.source(E.host(host_attr), *extra_args)
        xml = ET.tostring(obj)
        return xml

    def _parse_target_source_result(self, target_type, xml_str):
        root = objectify.fromstring(xml_str)
        ret = []
        for source in root.getchildren():
            if target_type == 'netfs':
                target_path = source.dir.get('path')
                type = source.format.get('type')
            if target_type == 'iscsi':
                target_path = source.device.get('path')
                type = target_type
            host_name = source.host.get('name')
            ret.append(dict(host=host_name, target_type=type,
                            target=target_path))
        return ret
