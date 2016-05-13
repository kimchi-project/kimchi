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


VMSTORAGES_REQUESTS = {
    'POST': {
        'default': "KCHVMSTOR0001L",
    },
}

VMSTORAGE_REQUESTS = {
    'DELETE': {'default': "KCHVMSTOR0002L"},
    'PUT': {'default': "KCHVMSTOR0003L"},
}


@UrlSubNode("storages")
class VMStorages(Collection):
    def __init__(self, model, vm):
        super(VMStorages, self).__init__(model)
        self.resource = VMStorage
        self.vm = vm
        self.resource_args = [self.vm, ]
        self.model_args = [self.vm, ]
        self.log_map = VMSTORAGES_REQUESTS
        self.log_args.update({
            'vm': self.vm.encode('utf-8') if self.vm else '',
            'path': '',
        })


class VMStorage(Resource):
    def __init__(self, model, vm, ident):
        super(VMStorage, self).__init__(model, ident)
        self.vm = vm
        self.ident = ident
        self.info = {}
        self.model_args = [self.vm, self.ident]
        self.uri_fmt = '/vms/%s/storages/%s'
        self.log_map = VMSTORAGE_REQUESTS
        self.log_args.update({
            'vm': self.vm.encode('utf-8') if self.vm else '',
        })

    @property
    def data(self):
        return self.info
