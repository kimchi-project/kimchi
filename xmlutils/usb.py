#
# Project Kimchi
#
# Copyright IBM Corp, 2016
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
import lxml.etree as ET
from lxml.builder import E


def get_usb_controller_xml(model):
    """
    Returns a XML string defining USB controller. Example for model='nec-xhci':
    <controller type='usb' index='0' model='nec-xhci'>
        <address type='pci' domain='0x0000'
        bus='0x00' slot='0x0f' function='0x0'/>
    </controller>
    """
    m = E.controller(
        E.address(
            type='pci',
            domain='0x0000',
            bus='0x00',
            slot='0x0f',
            function='0x0'
        ),
        type='usb',
        index='0',
        model=model
    )

    return ET.tostring(m)
