#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

import ethtool
import ipaddr


APrivateNets = ipaddr.IPNetwork("10.0.0.0/8")
BPrivateNets = ipaddr.IPNetwork("172.16.0.0/12")
CPrivateNets = ipaddr.IPNetwork('192.168.0.0/16')
PrivateNets = [CPrivateNets, BPrivateNets, APrivateNets]
DefaultNetsPool = [ipaddr.IPNetwork('192.168.122.0/23'),
                   ipaddr.IPNetwork('192.168.124.0/22'),
                   ipaddr.IPNetwork('192.168.128.0/17')]


def get_dev_netaddr(dev):
    info = ethtool.get_interfaces_info(dev)[0]
    return (info.ipv4_address and
            "%s/%s" % (info.ipv4_address, info.ipv4_netmask) or '')


def get_dev_netaddrs():
    nets = []
    for dev in ethtool.get_devices():
        devnet = get_dev_netaddr(dev)
        devnet and nets.append(ipaddr.IPNetwork(devnet))
    return nets


# used_nets should include all the subnet allocated in libvirt network
# will get host network by get_dev_netaddrs
def get_one_free_network(used_nets, nets_pool=PrivateNets):
    def _get_free_network(nets, used_nets):
        for net in nets.subnet(new_prefix=24):
            if not any(net.overlaps(used) for used in used_nets):
                return str(net)
        return None

    used_nets = used_nets + get_dev_netaddrs()
    for nets in nets_pool:
        net = _get_free_network(nets, used_nets)
        if net:
            return net
    return None
