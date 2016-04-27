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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import lxml.etree as ET
from lxml.builder import E


def get_bootorder_xml(boot_order=['hd', 'cdrom', 'network']):
    """
    Returns the XML for boot order. The default return includes the following:

    <boot dev='hd'/>
    <boot dev='cdrom'/>
    <boot dev='network'/>

    To a different boot order, specify the order by a list as argument.
    """
    boot_xml = ''
    for device in boot_order:
        boot = E.boot(dev=device)
        boot_xml += ET.tostring(boot, encoding='utf-8', pretty_print=True)

    return boot_xml
