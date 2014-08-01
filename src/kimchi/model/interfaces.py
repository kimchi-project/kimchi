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

from kimchi import netinfo
from kimchi.exception import NotFoundError
from kimchi.model.networks import NetworksModel


class InterfacesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.networks = NetworksModel(**kargs)

    def get_list(self):
        return list(set(netinfo.all_favored_interfaces()) -
                    set(self.networks.get_all_networks_interfaces()))


class InterfaceModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        try:
            return netinfo.get_interface_info(name)
        except ValueError:
            raise NotFoundError("KCHIFACE0001E", {'name': name})
