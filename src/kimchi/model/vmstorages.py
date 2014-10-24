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

import string

from lxml import etree

from kimchi.exception import InvalidOperation, InvalidParameter, NotFoundError
from kimchi.exception import OperationFailed
from kimchi.model.vms import DOM_STATE_MAP, VMModel
from kimchi.model.storagevolumes import StorageVolumeModel
from kimchi.model.utils import get_vm_config_flag
from kimchi.osinfo import lookup
from kimchi.xmlutils.disk import get_device_node, get_disk_xml
from kimchi.xmlutils.disk import get_vm_disk_info, get_vm_disks

HOTPLUG_TYPE = ['scsi', 'virtio']


def _get_device_bus(dev_type, dom):
    try:
        version, distro = VMModel.vm_get_os_metadata(dom)
    except:
        version, distro = ('unknown', 'unknown')
    return lookup(distro, version)[dev_type+'_bus']


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
        # Path will never be blank due to API.json verification.
        # There is no need to cover this case here.
        if not ('vol' in params) ^ ('path' in params):
            raise InvalidParameter("KCHVMSTOR0017E")

        dom = VMModel.get_vm(vm_name, self.conn)
        params['bus'] = _get_device_bus(params['type'], dom)
        params['format'] = 'raw'

        dev_list = [dev for dev, bus in get_vm_disks(dom).iteritems()
                    if bus == params['bus']]
        dev_list.sort()
        if len(dev_list) == 0:
            params['index'] = 0
        else:
            char = dev_list.pop()[2]
            params['index'] = string.ascii_lowercase.index(char) + 1

        if (params['bus'] not in HOTPLUG_TYPE
                and DOM_STATE_MAP[dom.info()[0]] != 'shutoff'):
            raise InvalidOperation('KCHVMSTOR0011E')

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
            if vol_info['format'] not in supported_format[params['type']]:
                raise InvalidParameter("KCHVMSTOR0018E",
                                       {"format": vol_info['format'],
                                        "type": params['type']})

            if params['type'] == 'disk':
                params['format'] = vol_info['format']

            params['path'] = vol_info['path']

        params.update(self._get_available_bus_address(params['bus'], vm_name))
        # Add device to VM
        dev, xml = get_disk_xml(params)
        try:
            conn = self.conn.get()
            dom = conn.lookupByName(vm_name)
            dom.attachDeviceFlags(xml, get_vm_config_flag(dom, 'all'))
        except Exception as e:
            raise OperationFailed("KCHVMSTOR0008E", {'error': e.message})
        return dev

    def get_list(self, vm_name):
        dom = VMModel.get_vm(vm_name, self.conn)
        return get_vm_disks(dom).keys()


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
        dom = VMModel.get_vm(vm_name, self.conn)

        dev_info = self.lookup(vm_name, dev_name)
        if dev_info['type'] != 'cdrom':
            raise InvalidOperation("KCHVMSTOR0006E")

        params['path'] = params.get('path', '')
        dev_info.update(params)

        dev, xml = get_disk_xml(dev_info)
        try:
            dom.updateDeviceFlags(xml, get_vm_config_flag(dom, 'all'))
        except Exception as e:
            raise OperationFailed("KCHVMSTOR0009E", {'error': e.message})
        return dev
