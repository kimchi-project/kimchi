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

from lxml import objectify

from kimchi.exception import NotFoundError

DEV_TYPE_SRC_ATTR_MAP = {'file': 'file',
                         'block': 'dev'}


def get_device_xml(dom, dev_name):
    # Get VM xml and then devices xml
    xml = dom.XMLDesc(0)
    devices = objectify.fromstring(xml).devices
    disk = devices.xpath("./disk/target[@dev='%s']/.." % dev_name)
    if not disk:
        return None
    return disk[0]


def get_vm_disk(dom, dev_name):
    # Retrieve disk xml and format return dict
    disk = get_device_xml(dom, dev_name)
    if disk is None:
        raise NotFoundError("KCHVMSTOR0007E",
                            {'dev_name': dev_name,
                             'vm_name': dom.name()})
    path = ""
    dev_bus = disk.target.attrib['bus']
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
    except:
        pass
    dev_type = disk.attrib['device']
    return {'dev': dev_name,
            'type': dev_type,
            'path': path,
            'format': disk.driver.attrib['type'],
            'bus': dev_bus}


def get_vm_disk_list(dom):
    xml = dom.XMLDesc(0)
    devices = objectify.fromstring(xml).devices
    storages = [disk.target.attrib['dev']
                for disk in devices.xpath("./disk[@device='disk']")]
    storages += [disk.target.attrib['dev']
                 for disk in devices.xpath("./disk[@device='cdrom']")]
    return storages
