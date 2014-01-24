#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#  Aline Manera <alinefm@linux.vnet.ibm.com>
#  Royce Lv <lvroyce@linux.vnet.ibm.com>
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
from kimchi.control.utils import internal_redirect, UrlSubNode


@UrlSubNode("vms", True)
class VMs(Collection):
    def __init__(self, model):
        super(VMs, self).__init__(model)
        self.resource = VM


class VM(Resource):
    def __init__(self, model, ident):
        super(VM, self).__init__(model, ident)
        self.update_params = ["name"]
        self.screenshot = VMScreenShot(model, ident)
        self.uri_fmt = '/vms/%s'
        self.start = self.generate_action_handler('start')
        self.stop = self.generate_action_handler('stop')
        self.connect = self.generate_action_handler('connect')

    @property
    def data(self):
        return {'name': self.ident,
                'uuid': self.info['uuid'],
                'stats': self.info['stats'],
                'memory': self.info['memory'],
                'cpus': self.info['cpus'],
                'state': self.info['state'],
                'screenshot': self.info['screenshot'],
                'icon': self.info['icon'],
                'graphics': {'type': self.info['graphics']['type'],
                             'listen': self.info['graphics']['listen'],
                             'port': self.info['graphics']['port']}
                }


class VMScreenShot(Resource):
    def __init__(self, model, ident):
        super(VMScreenShot, self).__init__(model, ident)

    def get(self):
        self.lookup()
        raise internal_redirect(self.info)
