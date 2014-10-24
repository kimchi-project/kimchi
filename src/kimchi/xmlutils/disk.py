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

from lxml.builder import E

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
