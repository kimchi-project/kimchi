#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2017
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
from wok.control.base import Collection
from wok.control.base import Resource
from wok.control.utils import UrlSubNode


NETWORKS_REQUESTS = {
    'POST': {'default': 'KCHNET0001L'},
}

NETWORK_REQUESTS = {
    'DELETE': {'default': 'KCHNET0002L'},
    'PUT': {'default': 'KCHNET0003L'},
    'POST': {
        'activate': 'KCHNET0004L',
        'deactivate': 'KCHNET0005L',
    },
}


@UrlSubNode('networks', True)
class Networks(Collection):
    def __init__(self, model):
        super(Networks, self).__init__(model)
        self.admin_methods = ['POST']
        self.resource = Network

        # set user log messages and make sure all parameters are present
        self.log_map = NETWORKS_REQUESTS
        self.log_args.update({'connection': '', 'name': ''})


class Network(Resource):
    def __init__(self, model, ident):
        super(Network, self).__init__(model, ident)
        self.admin_methods = ['PUT', 'POST', 'DELETE']
        self.uri_fmt = '/networks/%s'
        self.activate = self.generate_action_handler('activate')
        self.deactivate = self.generate_action_handler('deactivate',
                                                       destructive=True)
        self.log_map = NETWORK_REQUESTS

    @property
    def data(self):
        return {'name': self.ident,
                'vms': self.info['vms'],
                'in_use': self.info['in_use'],
                'autostart': self.info['autostart'],
                'connection': self.info['connection'],
                'interfaces': self.info['interfaces'],
                'subnet': self.info['subnet'],
                'dhcp': self.info['dhcp'],
                'state': self.info['state'],
                'persistent': self.info['persistent']}
