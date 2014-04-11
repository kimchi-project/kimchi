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
import re
import socket
import string
import urlparse

import libvirt
import lxml.etree as ET
from lxml import etree, objectify
from lxml.builder import E

from kimchi.exception import InvalidOperation, InvalidParameter, NotFoundError
from kimchi.exception import OperationFailed
from kimchi.model.vms import DOM_STATE_MAP, VMModel
from kimchi.utils import check_url_path

DEV_TYPE_SRC_ATTR_MAP = {'file': 'file',
                         'block': 'dev'}


def _get_device_xml(dom, dev_name):
    # Get VM xml and then devices xml
    xml = dom.XMLDesc(0)
    devices = objectify.fromstring(xml).devices
    disk = devices.xpath("./disk/target[@dev='%s']/.." % dev_name)
    if not disk:
        return None
    return disk[0]


def _get_storage_xml(params):
    src_type = params.get('src_type')
    disk = E.disk(type=src_type, device=params.get('type'))
    disk.append(E.driver(name='qemu', type='raw'))
    # Working with url paths
    if src_type == 'network':
        output = urlparse.urlparse(params.get('path'))
        host = E.host(name=output.hostname, port=
                      output.port or socket.getservbyname(output.scheme))
        source = E.source(protocol=output.scheme, name=output.path)
        source.append(host)
        disk.append(source)
    else:
        # Fixing source attribute
        source = E.source()
        source.set(DEV_TYPE_SRC_ATTR_MAP[src_type], params.get('path'))
        disk.append(source)

    disk.append(E.target(dev=params.get('dev'), bus=params.get('bus', 'ide')))
    if params.get('address'):
        # ide disk target id is always '0'
        disk.append(E.address(
            type='drive', controller=params['address']['controller'],
            bus=params['address']['bus'], target='0',
            unit=params['address']['unit']))
    return ET.tostring(disk)


def _check_cdrom_path(path):
    if check_url_path(path):
        src_type = 'network'
    # Check if path is a valid local path
    elif os.path.exists(path):
        if os.path.isfile(path):
            src_type = 'file'
        else:
            # Check if path is a valid cdrom drive
            with open('/proc/sys/dev/cdrom/info') as cdinfo:
                content = cdinfo.read()

            cds = re.findall("drive name:\t\t(.*)", content)
            if not cds:
                raise InvalidParameter("KCHCDROM0003E", {'value': path})

            drives = [os.path.join('/dev', p) for p in cds[0].split('\t')]
            if path not in drives:
                raise InvalidParameter("KCHCDROM0003E", {'value': path})

            src_type = 'block'
    else:
        raise InvalidParameter("KCHCDROM0003E", {'value': path})
    return src_type


class VMStoragesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def _get_available_ide_address(self, vm_name):
        # libvirt limitation of just 1 ide controller
        # each controller have at most 2 buses and each bus 2 units.
        dom = VMModel.get_vm(vm_name, self.conn)
        disks = self.get_list(vm_name)
        valid_id = [('0', '0'), ('0', '1'), ('1', '0'), ('1', '1')]
        controller_id = '0'
        for dev_name in disks:
            disk = _get_device_xml(dom, dev_name)
            if disk.target.attrib['bus'] == 'ide':
                controller_id = disk.address.attrib['controller']
                bus_id = disk.address.attrib['bus']
                unit_id = disk.address.attrib['unit']
                if (bus_id, unit_id) in valid_id:
                    valid_id.remove((bus_id, unit_id))
                    continue
        if not valid_id:
            raise OperationFailed('KCHCDROM0014E', {'type': 'ide', 'limit': 4})
        else:
            address = {'controller': controller_id,
                       'bus': valid_id[0][0], 'unit': valid_id[0][1]}
            return dict(address=address)

    def create(self, vm_name, params):
        dom = VMModel.get_vm(vm_name, self.conn)
        if DOM_STATE_MAP[dom.info()[0]] != 'shutoff':
            raise InvalidOperation('KCHCDROM0011E')

        # Use device name passed or pick next
        dev_name = params.get('dev', None)
        if dev_name is None:
            params['dev'] = self._get_storage_device_name(vm_name)
        else:
            devices = self.get_list(vm_name)
            if dev_name in devices:
                raise OperationFailed('KCHCDROM0004E', {'dev_name': dev_name,
                                                        'vm_name': vm_name})

        # Path will never be blank due to API.json verification.
        # There is no need to cover this case here.
        path = params['path']
        params['src_type'] = _check_cdrom_path(path)

        params.update(self._get_available_ide_address(vm_name))
        # Add device to VM
        dev_xml = _get_storage_xml(params)
        try:
            conn = self.conn.get()
            dom = conn.lookupByName(vm_name)
            dom.attachDeviceFlags(dev_xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
        except Exception as e:
            raise OperationFailed("KCHCDROM0008E", {'error': e.message})
        return params['dev']

    def _get_storage_device_name(self, vm_name):
        dev_list = [dev for dev in self.get_list(vm_name)
                    if dev.startswith('hd')]
        if len(dev_list) == 0:
            return 'hda'
        dev_list.sort()
        last_dev = dev_list.pop()
        # TODO: Improve to device names "greater then" hdz
        next_dev_letter_pos = string.ascii_lowercase.index(last_dev[2]) + 1
        return 'hd' + string.ascii_lowercase[next_dev_letter_pos]

    def get_list(self, vm_name):
        dom = VMModel.get_vm(vm_name, self.conn)
        xml = dom.XMLDesc(0)
        devices = objectify.fromstring(xml).devices
        storages = [disk.target.attrib['dev']
                    for disk in devices.xpath("./disk[@device='disk']")]
        storages += [disk.target.attrib['dev']
                     for disk in devices.xpath("./disk[@device='cdrom']")]
        return storages


class VMStorageModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def lookup(self, vm_name, dev_name):
        # Retrieve disk xml and format return dict
        dom = VMModel.get_vm(vm_name, self.conn)
        disk = _get_device_xml(dom, dev_name)
        if disk is None:
            raise NotFoundError("KCHCDROM0007E", {'dev_name': dev_name,
                                                  'vm_name': vm_name})
        path = ""
        dev_bus = 'ide'
        try:
            source = disk.source
            if source is not None:
                src_type = disk.attrib['type']
                if src_type == 'network':
                    host = source.host
                    path = (source.attrib['protocol'] + '://' +
                            host.attrib['name'] + ':' +
                            host.attrib['port'] + source.attrib['name'])
                else:
                    path = source.attrib[DEV_TYPE_SRC_ATTR_MAP[src_type]]
            # Retrieve storage bus type
            dev_bus = disk.target.attrib['bus']
        except:
            pass
        dev_type = disk.attrib['device']
        return {'dev': dev_name,
                'type': dev_type,
                'path': path,
                'bus': dev_bus}

    def delete(self, vm_name, dev_name):
        # Get storage device xml
        dom = VMModel.get_vm(vm_name, self.conn)
        disk = _get_device_xml(dom, dev_name)
        if disk is None:
            raise NotFoundError("KCHCDROM0007E",
                                {'dev_name': dev_name,
                                 'vm_name': vm_name})

        dom = VMModel.get_vm(vm_name, self.conn)
        if DOM_STATE_MAP[dom.info()[0]] != 'shutoff':
            raise InvalidOperation('KCHCDROM0011E')

        try:
            conn = self.conn.get()
            dom = conn.lookupByName(vm_name)
            dom.detachDeviceFlags(etree.tostring(disk),
                                  libvirt.VIR_DOMAIN_AFFECT_CURRENT)
        except Exception as e:
            raise OperationFailed("KCHCDROM0010E", {'error': e.message})

    def update(self, vm_name, dev_name, params):
        params['src_type'] = _check_cdrom_path(params['path'])
        dom = VMModel.get_vm(vm_name, self.conn)

        dev_info = self.lookup(vm_name, dev_name)
        dev_info.update(params)
        xml = _get_storage_xml(dev_info)

        try:
            dom.updateDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
        except Exception as e:
            raise OperationFailed("KCHCDROM0009E", {'error': e.message})
        return dev_name
