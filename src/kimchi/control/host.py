#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
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

import cherrypy

from kimchi.control.base import Collection, Resource
from kimchi.control.utils import UrlSubNode, validate_method
from kimchi.exception import OperationFailed
from kimchi.template import render


@UrlSubNode("host", True, ['POST'])
class Host(Resource):
    def __init__(self, model, id=None):
        super(Host, self).__init__(model, id)
        self.uri_fmt = '/host/%s'
        self.reboot = self.generate_action_handler('reboot')
        self.shutdown = self.generate_action_handler('shutdown')
        self.stats = HostStats(self.model)
        self.partitions = Partitions(self.model)
        self.devices = Devices(self.model)
        self.packagesupdate = PackagesUpdate(self.model)
        self.repositories = Repositories(self.model)

    @cherrypy.expose
    def swupdate(self):
        validate_method(('POST'))
        try:
            task = self.model.host_swupdate()
            cherrypy.response.status = 202
            return render("Task", task)
        except OperationFailed, e:
            raise cherrypy.HTTPError(500, e.message)

    @property
    def data(self):
        return self.info


class HostStats(Resource):
    @property
    def data(self):
        return self.info


class Partitions(Collection):
    def __init__(self, model):
        super(Partitions, self).__init__(model)
        self.resource = Partition


class Partition(Resource):
    def __init__(self, model, id):
        super(Partition, self).__init__(model, id)

    @property
    def data(self):
        return self.info


class Devices(Collection):
    def __init__(self, model):
        super(Devices, self).__init__(model)
        self.resource = Device


class Device(Resource):
    def __init__(self, model, id):
        super(Device, self).__init__(model, id)

    @property
    def data(self):
        return self.info


class PackagesUpdate(Collection):
    def __init__(self, model):
        super(PackagesUpdate, self).__init__(model)
        self.resource = PackageUpdate


class PackageUpdate(Resource):
    def __init__(self, model, id=None):
        super(PackageUpdate, self).__init__(model, id)

    @property
    def data(self):
        return self.info


class Repositories(Collection):
    def __init__(self, model):
        super(Repositories, self).__init__(model)
        self.resource = Repository


class Repository(Resource):
    def __init__(self, model, id):
        super(Repository, self).__init__(model, id)
        self.update_params = ["config", "baseurl"]
        self.uri_fmt = "/host/repositories/%s"
        self.enable = self.generate_action_handler('enable')
        self.disable = self.generate_action_handler('disable')

    @property
    def data(self):
        return self.info
