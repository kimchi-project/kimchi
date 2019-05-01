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
from wok.control.base import AsyncCollection
from wok.control.base import AsyncResource
from wok.control.utils import UrlSubNode


VMHOSTDEVS_REQUESTS = {'POST': {'default': 'KCHVMHDEV0001L'}}

VMHOSTDEV_REQUESTS = {'DELETE': {'default': 'KCHVMHDEV0002L'}}


@UrlSubNode('hostdevs')
class VMHostDevs(AsyncCollection):
    def __init__(self, model, vmid):
        super(VMHostDevs, self).__init__(model)
        self.resource = VMHostDev
        self.vmid = vmid
        self.resource_args = [self.vmid]
        self.model_args = [self.vmid]

        # set user log messages and make sure all parameters are present
        self.log_map = VMHOSTDEVS_REQUESTS
        self.log_args.update(
            {'name': '', 'vmid': self.vmid if self.vmid else ''})


class VMHostDev(AsyncResource):
    def __init__(self, model, vmid, ident):
        super(VMHostDev, self).__init__(model, ident)
        self.vmid = vmid
        self.ident = ident
        self.model_args = [self.vmid, self.ident]

        # set user log messages and make sure all parameters are present
        self.log_map = VMHOSTDEV_REQUESTS
        self.log_args.update({'vmid': self.vmid if self.vmid else ''})

    @property
    def data(self):
        return self.info
