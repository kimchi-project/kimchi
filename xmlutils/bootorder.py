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


def get_bootorder_node(boot_order=None):
    if boot_order is None:
        boot_order = ['hd', 'cdrom', 'network']

    boot_nodes = []
    for device in boot_order:
        boot_nodes.append(E.boot(dev=device))

    return boot_nodes


def get_bootorder_xml(boot_order=None):
    """
    Returns the XML for boot order. The default return includes the following:

    <boot dev='hd'/>
    <boot dev='cdrom'/>
    <boot dev='network'/>

    To a different boot order, specify the order by a list as argument.
    """
    boot_xml = ''
    for device in get_bootorder_node(boot_order):
        boot_xml += ET.tostring(device, encoding='utf-8', pretty_print=True)

    return boot_xml

def get_bootmenu_node():
    return E.bootmenu(enable="yes", timeout="5000")
