#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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


@UrlSubNode('networks', True)
class Networks(Collection):
    def __init__(self, model):
        super(Networks, self).__init__(model)
        self.role_key = 'network'
        self.admin_methods = ['POST']
        self.resource = Network


class Network(Resource):
    def __init__(self, model, ident):
        super(Network, self).__init__(model, ident)
        self.role_key = 'network'
        self.admin_methods = ['PUT', 'POST', 'DELETE']
        self.uri_fmt = "/networks/%s"
        self.activate = self.generate_action_handler('activate')
        self.deactivate = self.generate_action_handler('deactivate',
                                                       destructive=True)

    @property
    def data(self):
        return {'name': self.ident,
                'vms': self.info['vms'],
                'in_use': self.info['in_use'],
                'autostart': self.info['autostart'],
                'connection': self.info['connection'],
                'interface': self.info['interface'],
                'subnet': self.info['subnet'],
                'dhcp': self.info['dhcp'],
                'state': self.info['state'],
                'persistent': self.info['persistent']}
