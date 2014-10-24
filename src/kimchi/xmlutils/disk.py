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

import lxml.etree as ET
import socket
import urlparse

from lxml import objectify
from lxml.builder import E

from kimchi.exception import NotFoundError

DEV_TYPE_SRC_ATTR_MAP = {'file': 'file', 'block': 'dev'}


def get_disk_xml(src_type, params, ignore_src=False):
    """
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>

      [source XML according to src_type]

      <target dev='%(dev)s' bus='%(bus)s'/>
      <readonly/>
    </disk>
    """
    disk = E.disk(type=src_type, device=params['type'])
    disk.append(E.driver(name='qemu', type=params['format']))
    disk.append(E.target(dev=params['dev'], bus=params['bus']))

    if params.get('address'):
        # ide disk target id is always '0'
        disk.append(E.address(
            type='drive', controller=params['address']['controller'],
            bus=params['address']['bus'], target='0',
            unit=params['address']['unit']))

    if ignore_src:
        return ET.tostring(disk, encoding='utf-8', pretty_print=True)

    if src_type == 'network':
        """
        <source protocol='%(protocol)s' name='%(url_path)s'>
          <host name='%(hostname)s' port='%(port)s'/>
        </source>
        """
        output = urlparse.urlparse(params['path'])
        port = str(output.port or socket.getservbyname(output.scheme))

        source = E.source(protocol=output.scheme, name=output.path)
        source.append(E.host(name=output.hostname, port=port))
    else:
        """
        <source file='%(src)s' />
        """
        source = E.source()
        source.set(DEV_TYPE_SRC_ATTR_MAP[src_type], params['path'])

    disk.append(source)
    return ET.tostring(disk, encoding='utf-8', pretty_print=True)


def get_device_node(dom, dev_name):
    xml = dom.XMLDesc(0)
    devices = objectify.fromstring(xml).devices
    disk = devices.xpath("./disk/target[@dev='%s']/.." % dev_name)

    if not disk:
        raise NotFoundError("KCHVMSTOR0007E",
                            {'dev_name': dev_name,
                             'vm_name': dom.name()})

    return disk[0]


def get_vm_disk_info(dom, dev_name):
    # Retrieve disk xml and format return dict
    disk = get_device_node(dom, dev_name)
    if disk is None:
        return None

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
        path = ""

    return {'dev': dev_name,
            'path': path,
            'type': disk.attrib['device'],
            'format': disk.driver.attrib['type'],
            'bus': disk.target.attrib['bus']}


def get_vm_disk_list(dom):
    xml = dom.XMLDesc(0)
    devices = objectify.fromstring(xml).devices
    storages = [disk.target.attrib['dev']
                for disk in devices.xpath("./disk[@device='disk']")]
    storages += [disk.target.attrib['dev']
                 for disk in devices.xpath("./disk[@device='cdrom']")]
    return storages
