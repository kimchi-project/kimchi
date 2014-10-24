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
import stat
import string

from lxml import etree

from kimchi.exception import InvalidOperation, InvalidParameter, NotFoundError
from kimchi.exception import OperationFailed
from kimchi.model.vms import DOM_STATE_MAP, VMModel
from kimchi.model.storagevolumes import StorageVolumeModel
from kimchi.model.utils import get_vm_config_flag
from kimchi.utils import check_url_path
from kimchi.osinfo import lookup
from kimchi.xmlutils.disk import get_device_node, get_disk_xml
from kimchi.xmlutils.disk import get_vm_disk_info, get_vm_disk_list

HOTPLUG_TYPE = ['scsi', 'virtio']
PREFIX_MAP = {'ide': 'hd', 'virtio': 'vd', 'scsi': 'sd'}


def _get_device_bus(dev_type, dom):
    try:
        version, distro = VMModel.vm_get_os_metadata(dom)
    except:
        version, distro = ('unknown', 'unknown')
    return lookup(distro, version)[dev_type+'_bus']


def _check_path(path):
    if check_url_path(path):
        src_type = 'network'
    # Check if path is a valid local path
    elif os.path.exists(path):
        if os.path.isfile(path):
            src_type = 'file'
        else:
            r_path = os.path.realpath(path)
            if not stat.S_ISBLK(os.stat(r_path).st_mode):
                raise InvalidParameter("KCHVMSTOR0003E", {'value': path})

            src_type = 'block'
    else:
        raise InvalidParameter("KCHVMSTOR0003E", {'value': path})
    return src_type


class VMStoragesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']

    def _get_available_bus_address(self, bus_type, vm_name):
        if bus_type not in ['ide']:
            return dict()
        # libvirt limitation of just 1 ide controller
        # each controller have at most 2 buses and each bus 2 units.
        dom = VMModel.get_vm(vm_name, self.conn)
        disks = self.get_list(vm_name)
        valid_id = [('0', '0'), ('0', '1'), ('1', '0'), ('1', '1')]
        controller_id = '0'
        for dev_name in disks:
            disk = get_device_node(dom, dev_name)
            if disk.target.attrib['bus'] == 'ide':
                controller_id = disk.address.attrib['controller']
                bus_id = disk.address.attrib['bus']
                unit_id = disk.address.attrib['unit']
                if (bus_id, unit_id) in valid_id:
                    valid_id.remove((bus_id, unit_id))
                    continue
        if not valid_id:
            raise OperationFailed('KCHVMSTOR0014E',
                                  {'type': 'ide', 'limit': 4})
        else:
            address = {'controller': controller_id,
                       'bus': valid_id[0][0], 'unit': valid_id[0][1]}
            return dict(address=address)

    def create(self, vm_name, params):
        dom = VMModel.get_vm(vm_name, self.conn)
        params['bus'] = _get_device_bus(params['type'], dom)
        self._get_storage_device_name(vm_name, params)
        # Path will never be blank due to API.json verification.
        # There is no need to cover this case here.
        params['format'] = 'raw'
        if not ('vol' in params) ^ ('path' in params):
            raise InvalidParameter("KCHVMSTOR0017E")
        if params.get('vol'):
            try:
                pool = params['pool']
                vol_info = StorageVolumeModel(
                    conn=self.conn,
                    objstore=self.objstore).lookup(pool, params['vol'])
            except KeyError:
                raise InvalidParameter("KCHVMSTOR0012E")
            except Exception as e:
                raise InvalidParameter("KCHVMSTOR0015E", {'error': e})
            if vol_info['ref_cnt'] != 0:
                raise InvalidParameter("KCHVMSTOR0016E")

            supported_format = {
                "disk": ["raw", "bochs", "qcow", "qcow2", "qed", "vmdk"],
                "cdrom": "iso"}
            if vol_info['format'] in supported_format[params['type']]:
                if params['type'] == 'disk':
                    params['format'] = vol_info['format']
            else:
                raise InvalidParameter("KCHVMSTOR0018E",
                                       {"format": vol_info['format'],
                                        "type": params['type']})
            params['path'] = vol_info['path']

        if (params['bus'] not in HOTPLUG_TYPE
                and DOM_STATE_MAP[dom.info()[0]] != 'shutoff'):
            raise InvalidOperation('KCHVMSTOR0011E')

        params.update(self._get_available_bus_address(params['bus'], vm_name))
        # Add device to VM
        dev_xml = get_disk_xml(_check_path(params['path']), params)
        try:
            conn = self.conn.get()
            dom = conn.lookupByName(vm_name)
            dom.attachDeviceFlags(dev_xml, get_vm_config_flag(dom, 'all'))
        except Exception as e:
            raise OperationFailed("KCHVMSTOR0008E", {'error': e.message})
        return params['dev']

    def _get_storage_device_name(self, vm_name, params):
        bus_prefix = PREFIX_MAP[params['bus']]
        dev_list = [dev for dev in self.get_list(vm_name)
                    if dev.startswith(bus_prefix)]
        if len(dev_list) == 0:
            params['dev'] = bus_prefix + 'a'
        else:
            dev_list.sort()
            last_dev = dev_list.pop()
            # TODO: Improve to device names "greater then" hdz
            next_dev_letter_pos =\
                string.ascii_lowercase.index(last_dev[2]) + 1
            params['dev'] =\
                bus_prefix + string.ascii_lowercase[next_dev_letter_pos]

    def get_list(self, vm_name):
        dom = VMModel.get_vm(vm_name, self.conn)
        return get_vm_disk_list(dom)


class VMStorageModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def lookup(self, vm_name, dev_name):
        # Retrieve disk xml and format return dict
        dom = VMModel.get_vm(vm_name, self.conn)
        return get_vm_disk_info(dom, dev_name)

    def delete(self, vm_name, dev_name):
        # Get storage device xml
        dom = VMModel.get_vm(vm_name, self.conn)
        try:
            bus_type = self.lookup(vm_name, dev_name)['bus']
        except NotFoundError:
            raise

        dom = VMModel.get_vm(vm_name, self.conn)
        if (bus_type not in HOTPLUG_TYPE and
                DOM_STATE_MAP[dom.info()[0]] != 'shutoff'):
            raise InvalidOperation('KCHVMSTOR0011E')

        try:
            conn = self.conn.get()
            dom = conn.lookupByName(vm_name)
            disk = get_device_node(dom, dev_name)
            dom.detachDeviceFlags(etree.tostring(disk),
                                  get_vm_config_flag(dom, 'all'))
        except Exception as e:
            raise OperationFailed("KCHVMSTOR0010E", {'error': e.message})

    def update(self, vm_name, dev_name, params):
        path = params.get('path')
        if path and len(path) != 0:
            src_type = _check_path(path)
            ignore_source = False
        else:
            src_type = 'file'
            ignore_source = True
        dom = VMModel.get_vm(vm_name, self.conn)

        dev_info = self.lookup(vm_name, dev_name)
        if dev_info['type'] != 'cdrom':
            raise InvalidOperation("KCHVMSTOR0006E")
        dev_info.update(params)

        xml = get_disk_xml(src_type, dev_info, ignore_source)
        try:
            dom.updateDeviceFlags(xml, get_vm_config_flag(dom, 'all'))
        except Exception as e:
            raise OperationFailed("KCHVMSTOR0009E", {'error': e.message})
        return dev_name
