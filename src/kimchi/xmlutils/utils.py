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
from lxml import objectify


def xpath_get_text(xml, expr):
    doc = ET.fromstring(xml)

    res = []
    for x in doc.xpath(expr):
        if isinstance(x, unicode):
            x = x.encode('utf-8')
        elif not isinstance(x, str):
            x = x.text
        res.append(x)
    return res


def xml_item_update(xml, xpath, value, attr=None):
    root = ET.fromstring(xml)
    item = root.find(xpath)
    if attr is None:
        item.text = value
    else:
        item.set(attr, value)
    return ET.tostring(root, encoding="utf-8")


def dictize(xmlstr):
    root = objectify.fromstring(xmlstr)
    return {root.tag: _dictize(root)}


def _dictize(e):
    d = {}
    if e.text is not None:
        if not e.attrib and e.countchildren() == 0:
            return e.pyval
        d['pyval'] = e.pyval
    d.update(e.attrib)
    for child in e.iterchildren():
        if child.tag in d:
            continue
        if len(child) > 1:
            d[child.tag] = [
                _dictize(same_tag_child) for same_tag_child in child]
        else:
            d[child.tag] = _dictize(child)
    return d
