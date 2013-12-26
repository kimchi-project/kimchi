#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#  Aline Manera <alinefm@linux.vnet.ibm.com>
#  Daniel Henrique Barboza <danielhb@linux.vnet.ibm.com>
#  ShaoHe Feng <shaohef@linux.vnet.ibm.com>
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


class Host(Resource):
    def __init__(self, model, id=None):
        super(Host, self).__init__(model, id)
        self.uri_fmt = '/host/%s'
        self.reboot = self.generate_action_handler('reboot')
        self.shutdown = self.generate_action_handler('shutdown')
        self.stats = HostStats(self.model)
        self.stats.exposed = True
        self.partitions = Partitions(self.model)
        self.partitions.exposed = True

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
