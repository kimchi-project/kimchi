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

import ethtool

from wok.exception import InvalidParameter, NotFoundError
from wok.stringutils import encode_value
from wok.utils import wok_log

from wok.plugins.kimchi import network as netinfo
from wok.plugins.kimchi.model.networks import NetworksModel


class InterfacesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.networks = NetworksModel(**kargs)

    def get_list(self, _inuse=None):
        if _inuse == "true":
            return list(set(netinfo.all_favored_interfaces()) &
                        set(self.networks.get_all_networks_interfaces()))
        elif _inuse == "false":
            return list(set(netinfo.all_favored_interfaces()) -
                        set(self.networks.get_all_networks_interfaces()))
        elif _inuse is None:
            return list(set(netinfo.all_favored_interfaces()))
        else:
            wok_log.error("Invalid filter _inuse. _inuse: %s. Supported"
                          " options are %s" % (_inuse, 'true/false'))
            raise InvalidParameter("KCHIFACE0002E",
                                   {'supported_inuse': ['true', 'false']})


class InterfaceModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        if encode_value(name) not in map(encode_value, ethtool.get_devices()):
            raise NotFoundError("KCHIFACE0001E", {'name': name})

        ipaddr = ''
        netmask = ''
        module = 'unknown'
        status = 'down'
        try:
            ipaddr = ethtool.get_ipaddr(encode_value(name))
            netmask = ethtool.get_netmask(encode_value(name))
            module = ethtool.get_module(encode_value(name))

            flags = ethtool.get_flags(encode_value(name))
            status = 'up' if flags & (ethtool.IFF_RUNNING | ethtool.IFF_UP) \
                     else 'down'
        except IOError:
            pass

        iface_type = netinfo.get_interface_type(name)

        return {'name': name,
                'type': iface_type,
                'status': status,
                'ipaddr': ipaddr,
                'netmask': netmask,
                'module': module}
