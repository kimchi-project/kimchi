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

from kimchi.control.cpuinfo import CPUInfo
from kimchi.control.base import Collection, Resource, SimpleCollection
from kimchi.control.utils import UrlSubNode
from kimchi.exception import NotFoundError


@UrlSubNode('host', True)
class Host(Resource):
    def __init__(self, model, id=None):
        super(Host, self).__init__(model, id)
        self.role_key = 'host'
        self.admin_methods = ['GET', 'POST']
        self.uri_fmt = '/host/%s'
        self.reboot = self.generate_action_handler('reboot')
        self.shutdown = self.generate_action_handler('shutdown')
        self.stats = HostStats(self.model)
        self.partitions = Partitions(self.model)
        self.devices = Devices(self.model)
        self.packagesupdate = PackagesUpdate(self.model)
        self.repositories = Repositories(self.model)
        self.swupdate = self.generate_action_handler_task('swupdate')
        self.cpuinfo = CPUInfo(self.model)

    @property
    def data(self):
        return self.info


class HostStats(Resource):
    def __init__(self, model, id=None):
        super(HostStats, self).__init__(model, id)
        self.role_key = 'host'
        self.admin_methods = ['GET']
        self.history = HostStatsHistory(self.model)

    @property
    def data(self):
        return self.info


class HostStatsHistory(Resource):
    @property
    def data(self):
        return self.info


class Partitions(Collection):
    def __init__(self, model):
        super(Partitions, self).__init__(model)
        self.role_key = 'storage'
        self.admin_methods = ['GET']
        self.resource = Partition

    # Defining get_resources in order to return list of partitions in UI
    # sorted by their path
    def _get_resources(self, flag_filter):
        res_list = super(Partitions, self)._get_resources(flag_filter)
        res_list = filter(lambda x: x.info['available'], res_list)
        res_list.sort(key=lambda x: x.info['path'])
        return res_list


class Partition(Resource):
    def __init__(self, model, id):
        self.role_key = 'storage'
        self.admin_methods = ['GET']
        super(Partition, self).__init__(model, id)

    @property
    def data(self):
        if not self.info['available']:
            raise NotFoundError("KCHPART0001E", {'name': self.info['name']})

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


class PackagesUpdate(Collection):
    def __init__(self, model):
        super(PackagesUpdate, self).__init__(model)
        self.role_key = 'host'
        self.admin_methods = ['GET']
        self.resource = PackageUpdate


class PackageUpdate(Resource):
    def __init__(self, model, id=None):
        super(PackageUpdate, self).__init__(model, id)
        self.role_key = 'host'
        self.admin_methods = ['GET']

    @property
    def data(self):
        return self.info


class Repositories(Collection):
    def __init__(self, model):
        super(Repositories, self).__init__(model)
        self.role_key = 'host'
        self.admin_methods = ['GET', 'POST']
        self.resource = Repository


class Repository(Resource):
    def __init__(self, model, id):
        super(Repository, self).__init__(model, id)
        self.role_key = 'host'
        self.admin_methods = ['GET', 'PUT', 'POST', 'DELETE']
        self.uri_fmt = "/host/repositories/%s"
        self.enable = self.generate_action_handler('enable')
        self.disable = self.generate_action_handler('disable')

    @property
    def data(self):
        return self.info
