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
import lxml.etree as ET
from lxml import objectify
from lxml.builder import E

from kimchi.model.config import CapabilitiesModel
from kimchi.model.storagepools import STORAGE_SOURCES
from kimchi.utils import kimchi_log, patch_find_nfs_target


class StorageTargetsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.caps = CapabilitiesModel()

    def get_list(self, storage_server, _target_type=None):
        target_list = list()

        if not _target_type:
            target_types = STORAGE_SOURCES.keys()
        else:
            target_types = [_target_type]

        for target_type in target_types:
            if not self.caps.nfs_target_probe and target_type == 'netfs':
                targets = patch_find_nfs_target(storage_server)
            else:
                xml = self._get_storage_server_spec(server=storage_server,
                                                    target_type=target_type)
                conn = self.conn.get()
                try:
                    ret = conn.findStoragePoolSources(target_type, xml, 0)
                except libvirt.libvirtError as e:
                    err = "Query storage pool source fails because of %s"
                    kimchi_log.warning(err, e.get_error_message())
                    continue

                targets = self._parse_target_source_result(target_type, ret)

            target_list.extend(targets)
        return target_list

    def _get_storage_server_spec(**kwargs):
        # Required parameters:
        # server:
        # target_type:
        extra_args = []
        if kwargs['target_type'] == 'netfs':
            extra_args.append(E.format(type='nfs'))
        obj = E.source(E.host(name=kwargs['server']), *extra_args)
        xml = ET.tostring(obj)
        return xml

    def _parse_target_source_result(target_type, xml_str):
        root = objectify.fromstring(xml_str)
        ret = []
        for source in root.getchildren():
            if target_type == 'netfs':
                host_name = source.host.get('name')
                target_path = source.dir.get('path')
                type = source.format.get('type')
                ret.append(dict(host=host_name, target_type=type,
                                target=target_path))
        return ret
