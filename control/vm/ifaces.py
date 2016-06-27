#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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

from wok.control.base import Collection, Resource
from wok.control.utils import UrlSubNode


VMIFACES_REQUESTS = {
    'POST': {
        'default': "KCHVMIF0001L",
    },
}

VMIFACE_REQUESTS = {
    'DELETE': {
        'default': "KCHVMIF0002L",
    },
    'PUT': {
        'default': "KCHVMIF0003L",
    },
}


@UrlSubNode("ifaces")
class VMIfaces(Collection):
    def __init__(self, model, vm):
        super(VMIfaces, self).__init__(model)
        self.resource = VMIface
        self.vm = vm
        self.resource_args = [self.vm, ]
        self.model_args = [self.vm, ]

        # set user log messages and make sure all parameters are present
        self.log_map = VMIFACES_REQUESTS
        self.log_args.update({
            'network': '',
            'vm': self.vm.encode('utf-8') if self.vm else '',
        })


class VMIface(Resource):
    def __init__(self, model, vm, ident):
        super(VMIface, self).__init__(model, ident)
        self.vm = vm
        self.ident = ident
        self.info = {}
        self.model_args = [self.vm, self.ident]
        self.uri_fmt = '/vms/%s/ifaces/%s'

        # set user log messages and make sure all parameters are present
        self.log_map = VMIFACE_REQUESTS
        self.log_args.update({
            'vm': self.vm.encode('utf-8') if self.vm else '',
        })

    @property
    def data(self):
        return self.info
