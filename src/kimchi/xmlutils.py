#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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

import libxml2


from xml.etree import ElementTree


def xpath_get_text(xml, expr):
    doc = libxml2.parseDoc(xml)
    res = doc.xpathEval(expr)
    ret = [None if x.children is None else x.children.content for x in res]

    doc.freeDoc()
    return ret


def xml_item_update(xml, xpath, value):
    root = ElementTree.fromstring(xml)
    item = root.find(xpath)
    item.text = value
    return ElementTree.tostring(root, encoding="utf-8")
