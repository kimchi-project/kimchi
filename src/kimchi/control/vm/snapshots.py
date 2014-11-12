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

from kimchi.control.base import AsyncCollection, Resource
from kimchi.control.utils import UrlSubNode


@UrlSubNode('snapshots')
class VMSnapshots(AsyncCollection):
    def __init__(self, model, vm):
        super(VMSnapshots, self).__init__(model)
        self.resource = VMSnapshot
        self.vm = vm
        self.resource_args = [self.vm, ]
        self.model_args = [self.vm, ]
        self.current = CurrentVMSnapshot(model, vm)


class VMSnapshot(Resource):
    def __init__(self, model, vm, ident):
        super(VMSnapshot, self).__init__(model, ident)
        self.vm = vm
        self.ident = ident
        self.model_args = [self.vm, self.ident]
        self.uri_fmt = '/vms/%s/snapshots/%s'
        self.revert = self.generate_action_handler('revert')

    @property
    def data(self):
        return self.info


class CurrentVMSnapshot(Resource):
    def __init__(self, model, vm):
        super(CurrentVMSnapshot, self).__init__(model)
        self.vm = vm
        self.model_args = [self.vm]
        self.uri_fmt = '/vms/%s/snapshots/current'

    @property
    def data(self):
        return self.info
