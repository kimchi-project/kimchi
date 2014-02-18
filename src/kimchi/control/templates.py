#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

from kimchi.control.base import Collection, Resource
from kimchi.control.utils import UrlSubNode


@UrlSubNode("templates", True, ['PUT', 'DELETE'])
class Templates(Collection):
    def __init__(self, model):
        super(Templates, self).__init__(model)
        self.resource = Template


class Template(Resource):
    def __init__(self, model, ident):
        super(Template, self).__init__(model, ident)
        self.update_params = ["name", "folder", "icon", "os_distro",
                              "storagepool", "os_version", "cpus",
                              "memory", "cdrom", "disks", "networks",
                              "graphics"]
        self.uri_fmt = "/templates/%s"
        self.clone = self.generate_action_handler('clone')

    @property
    def data(self):
        return {'name': self.ident,
                'icon': self.info['icon'],
                'os_distro': self.info['os_distro'],
                'os_version': self.info['os_version'],
                'cpus': self.info['cpus'],
                'memory': self.info['memory'],
                'cdrom': self.info['cdrom'],
                'disks': self.info['disks'],
                'storagepool': self.info['storagepool'],
                'networks': self.info['networks'],
                'folder': self.info.get('folder', []),
                'graphics': self.info['graphics']}
