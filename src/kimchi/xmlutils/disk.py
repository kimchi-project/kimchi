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
import os
import socket
import stat
import string
import urlparse

from lxml import objectify
from lxml.builder import E

from kimchi.exception import InvalidParameter, NotFoundError
from kimchi.utils import check_url_path

BUS_TO_DEV_MAP = {'ide': 'hd', 'virtio': 'vd', 'scsi': 'sd'}
DEV_TYPE_SRC_ATTR_MAP = {'file': 'file', 'block': 'dev'}


def get_disk_xml(params):
    """
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>

      [source XML according to src_type]

      <target dev='%(dev)s' bus='%(bus)s'/>
      <readonly/>
    </disk>
    """
    path = params['path']
    disk_type = params.get('disk', None)
    if disk_type is None:
        disk_type = _get_disk_type(path) if len(path) > 0 else 'file'
    disk = E.disk(type=disk_type, device=params['type'])
    driver = E.driver(name='qemu', type=params['format'])
    if params['type'] != 'cdrom':
        driver.set('cache', 'none')

    disk.append(driver)

    # Get device name according to bus and index values
    dev = params.get('dev', (BUS_TO_DEV_MAP[params['bus']] +
                             string.lowercase[params.get('index', 0)]))
    disk.append(E.target(dev=dev, bus=params['bus']))

    if params.get('address'):
        # ide disk target id is always '0'
        disk.append(E.address(
            type='drive', controller=params['address']['controller'],
            bus=params['address']['bus'], target='0',
            unit=params['address']['unit']))

    if len(params['path']) == 0:
        return (dev, ET.tostring(disk, encoding='utf-8', pretty_print=True))

    if disk_type == 'network':
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
        source.set(DEV_TYPE_SRC_ATTR_MAP[disk_type], params['path'])

    disk.append(source)
    return (dev, ET.tostring(disk, encoding='utf-8', pretty_print=True))


def _get_disk_type(path):
    if check_url_path(path):
        return 'network'

    if not os.path.exists(path):
        raise InvalidParameter("KCHVMSTOR0003E", {'value': path})

    # Check if path is a valid local path
    if os.path.isfile(path):
        return 'file'

    r_path = os.path.realpath(path)
    if stat.S_ISBLK(os.stat(r_path).st_mode):
        return 'block'

    raise InvalidParameter("KCHVMSTOR0003E", {'value': path})


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


def get_vm_disks(dom):
    xml = dom.XMLDesc(0)
    devices = objectify.fromstring(xml).devices

    storages = {}
    all_disks = devices.xpath("./disk[@device='disk']")
    all_disks.extend(devices.xpath("./disk[@device='cdrom']"))
    for disk in all_disks:
        storages[disk.target.attrib['dev']] = disk.target.attrib['bus']

    return storages
