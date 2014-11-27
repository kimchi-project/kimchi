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

from lxml.builder import E


def get_graphics_xml(params):
    """
    <graphics type='%(type)s' autoport='yes' listen='%(listen)s'/>

    - For spice graphics:

    <channel type='spicevmc'>
      <target type='virtio' name='com.redhat.spice.0'/>
    </channel>
    """
    graphics = E.graphics(type=params['type'], autoport='yes',
                          listen=params['listen'])
    graphics_xml = ET.tostring(graphics, encoding='utf-8', pretty_print=True)

    if params['type'] == 'vnc':
        return graphics_xml

    # For spice graphics, a channel also must be configured
    channel = E.channel(type='spicevmc')
    channel.append(E.target(type='virtio', name='com.redhat.spice.0'))
    channel_xml = ET.tostring(channel, encoding='utf-8', pretty_print=True)
    return graphics_xml + channel_xml
