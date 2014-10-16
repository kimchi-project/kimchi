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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import ipaddr
import lxml.etree as ET

from lxml.builder import E


# FIXME, do not support ipv6
def _get_dhcp_elem(**kwargs):
    """
    <dhcp>
      <range start="192.168.122.100" end="192.168.122.254" />
      <host mac="00:16:3e:77:e2:ed" name="foo.test.com" ip="192.168.122.10" />
      <host mac="00:16:3e:3e:a9:1a" name="bar.test.com" ip="192.168.122.11" />
    </dhcp>
    """
    dhcp = E.dhcp()
    if 'range' in kwargs.keys():
        dhcp_range = E.range(start=kwargs['range']['start'],
                             end=kwargs['range']['end'])
        dhcp.append(dhcp_range)

    if 'hosts' in kwargs.keys():
        for host in kwargs['hosts']:
            dhcp.append(E.host(mac=host['mac'],
                               name=host['name'],
                               ip=host['ip']))

    return dhcp if len(dhcp) > 0 else None


def _get_ip_elem(**kwargs):
    """
    <ip address="192.168.152.1" netmask="255.255.255.0">
      <dhcp>
        <range start="192.168.152.2" end="192.168.152.254" />
      </dhcp>
    </ip>
    """
    if 'net' not in kwargs.keys():
        return None

    net = ipaddr.IPNetwork(kwargs['net'])
    ip = E.ip(address=str(net.ip), netmask=str(net.netmask))

    dhcp_params = kwargs.get('dhcp', {})
    dhcp = _get_dhcp_elem(**dhcp_params)
    if dhcp is not None:
        ip.append(dhcp)

    return ip


def _get_forward_elem(**kwargs):
    """
    <forward mode='hostdev' dev='eth0' managed='yes'>
    </forward>
    """
    if "mode" in kwargs.keys() and kwargs['mode'] is None:
        return None

    forward = E.forward()
    if 'mode' in kwargs.keys():
        forward.set('mode', kwargs['mode'])

    if 'dev' in kwargs.keys():
        forward.set('dev', kwargs['dev'])

    if 'managed' in kwargs.keys():
        forward.set('managed', kwargs['managed'])

    return forward


def to_network_xml(**kwargs):
    network = E.network(E.name(kwargs['name']))
    bridge = kwargs.get('bridge')
    if bridge:
        network.append(E.bridge(name=bridge))

    # None means is Isolated network, {} means default mode nat
    params = kwargs.get('forward', {"mode": None})
    forward = _get_forward_elem(**params)
    if forward is not None:
        network.append(forward)

    if 'net' in kwargs:
        network.append(_get_ip_elem(**kwargs))

    return ET.tostring(network)


def create_vlan_tagged_bridge_xml(bridge, interface, vlan_id):
    vlan = E.vlan(E.interface(name=interface))
    vlan.set('tag', vlan_id)
    m = E.interface(
        E.start(mode='onboot'),
        E.bridge(
            E.interface(
                vlan,
                type='vlan',
                name='.'.join([interface, vlan_id]))),
        type='bridge',
        name=bridge)
    return ET.tostring(m)
