#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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
from lxml.builder import E


def get_serial_xml(params):
    """
     For X
     <serial type='pty'>
       <target port='0'/>
     </serial>
     <console type='pty'>
       <target type='serial' port='0'/>
     </console>

     For ppc
     <console type='pty'>
         <target type='serial' port='1'/>
         <address type='spapr-vio' reg='0x30001000'/>
     </console>

    For s390x
    target type can be sclp/virtio
    <console type='pty'>
      <target type='sclp' port='0'/>
    </console>
    """
    # pcc serial console
    if params['arch'] in ['ppc', 'ppc64']:
        console = E.console(type='pty')
        console.append(E.target(type='serial', port='1'))
        console.append(E.address(type='spapr-vio', reg='0x30001000'))
        return ET.tostring(console, encoding='unicode', pretty_print=True)
    # for s390x
    elif params['arch'] in ['s390x']:
        # if params doesn't have console parameter, use virtio as default
        console_type = params.get('console', 'virtio')
        console = E.console(type='pty')
        console.append(E.target(type=console_type, port='0'))
        return ET.tostring(console, encoding='unicode', pretty_print=True)
    # for x
    else:
        serial = E.serial(type='pty')
        serial.append(E.target(port='0'))
        console = E.console(type='pty')
        console.append(E.target(type='serial', port='0'))
        return ET.tostring(serial, encoding='unicode', pretty_print=True) + \
            ET.tostring(console, encoding='unicode', pretty_print=True)
