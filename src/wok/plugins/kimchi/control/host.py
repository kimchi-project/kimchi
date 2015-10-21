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

from wok.control.base import Collection
from wok.control.base import Resource, SimpleCollection
from wok.control.utils import UrlSubNode

from wok.plugins.kimchi.control.cpuinfo import CPUInfo


@UrlSubNode('host', True)
class Host(Resource):
    def __init__(self, model, id=None):
        super(Host, self).__init__(model, id)
        self.role_key = 'host'
        self.admin_methods = ['GET', 'POST']
        self.uri_fmt = '/host/%s'
        self.devices = Devices(self.model)
        self.cpuinfo = CPUInfo(self.model)

    @property
    def data(self):
        return self.info


class Devices(Collection):
    def __init__(self, model):
        super(Devices, self).__init__(model)
        self.resource = Device


class VMHolders(SimpleCollection):
    def __init__(self, model, device_id):
        super(VMHolders, self).__init__(model)
        self.model_args = (device_id, )


class Device(Resource):
    def __init__(self, model, id):
        super(Device, self).__init__(model, id)
        self.vm_holders = VMHolders(self.model, id)

    @property
    def data(self):
        return self.info
