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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
import glob
import ipaddress
import os
from distutils.spawn import find_executable

import ethtool
from wok.stringutils import encode_value
from wok.utils import run_command


APrivateNets = ipaddress.IPv4Network('10.0.0.0/8', False)
BPrivateNets = ipaddress.IPv4Network('172.16.0.0/12', False)
CPrivateNets = ipaddress.IPv4Network('192.168.0.0/16', False)
PrivateNets = [CPrivateNets, BPrivateNets, APrivateNets]
DefaultNetsPool = [ipaddress.IPv4Network('192.168.122.0/23', False),
                   ipaddress.IPv4Network('192.168.124.0/22', False),
                   ipaddress.IPv4Network('192.168.128.0/17', False)]

NET_PATH = '/sys/class/net'
NIC_PATH = '/sys/class/net/*/device'
BRIDGE_PATH = '/sys/class/net/*/bridge'
BONDING_PATH = '/sys/class/net/*/bonding'
WLAN_PATH = '/sys/class/net/*/wireless'
NET_BRPORT = '/sys/class/net/%s/brport'
NET_MASTER = '/sys/class/net/%s/master'
PROC_NET_VLAN = '/proc/net/vlan/'
BONDING_SLAVES = '/sys/class/net/%s/bonding/slaves'
BRIDGE_PORTS = '/sys/class/net/%s/brif'


def wlans():
    """Get all wlans declared in /sys/class/net/*/wireless.

    Returns:
        List[str]: a list with the wlans found.

    """
    return [b.split('/')[-2] for b in glob.glob(WLAN_PATH)]


def nics():
    """Get all nics of the host.

    This function returns every nic, including those
    that might be loaded from an usb port.

    Returns:
        List[str]: a list with the nics found.

    """
    return list(set([b.split('/')[-2] for b in glob.glob(NIC_PATH)]) -
                set(wlans()))


def is_nic(iface):
    """Checks if iface is a nic.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a nic, False otherwise.

    """
    return encode_value(iface) in map(encode_value, nics())


def bondings():
    """Get all bondings of the host.

    Returns:
        List[str]: a list with the bonds found.

    """
    return [b.split('/')[-2] for b in glob.glob(BONDING_PATH)]


def is_bonding(iface):
    """Checks if iface is a bond.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bond, False otherwise.

    """
    return encode_value(iface) in map(encode_value, bondings())


def vlans():
    """Get all vlans of the host.

    Returns:
        List[str]: a list with the vlans found.

    """
    return list(
        set([b.split('/')[-1] for b in glob.glob(NET_PATH + '/*')]) &
        set([b.split('/')[-1] for b in glob.glob(PROC_NET_VLAN + '*')])
    )


def is_vlan(iface):
    """Checks if iface is a vlan.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a vlan, False otherwise.

    """
    return encode_value(iface) in map(encode_value, vlans())


def bridges():
    """Get all bridges of the host.

    Returns:
        List[str]: a list with the bridges found.

    """
    return list(set([b.split('/')[-2] for b in glob.glob(BRIDGE_PATH)] +
                    ovs_bridges()))


def is_bridge(iface):
    """Checks if iface is a bridge.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bridge, False otherwise.

    """
    return encode_value(iface) in map(encode_value, bridges())


def is_openvswitch_running():
    """Checks if the openvswitch service is running in the host.

    Returns:
        bool: True if openvswitch service is running, False otherwise.

    """
    cmd = ['systemctl', 'is-active', 'openvswitch', '--quiet']
    _, _, r_code = run_command(cmd, silent=True)
    return r_code == 0


def ovs_bridges():
    """Get the OVS Bridges of the host.

    In some distributions, like Fedora, the files bridge and brif are
    not created under /sys/class/net/<ovsbridge> for OVS bridges.
    These specific functions allows one to differentiate OVS bridges
    from other types of bridges.

    Returns:
        List[str]: a list with the OVS bridges found.

    """
    if not is_openvswitch_running():
        return []

    ovs_cmd = find_executable('ovs-vsctl')

    # openvswitch not installed: there is no OVS bridge configured
    if ovs_cmd is None:
        return []

    out, _, r_code = run_command([ovs_cmd, 'list-br'], silent=True)
    if r_code != 0:
        return []

    return [x.strip() for x in out.rstrip('\n').split('\n') if x.strip()]


def is_ovs_bridge(iface):
    """Checks if iface is an OVS bridge.

    In some distributions, like Fedora, the files bridge and brif are
    not created under /sys/class/net/<ovsbridge> for OVS bridges.
    These specific functions allows one to differentiate OVS bridges
    from other types of bridges.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is an OVS bridge, False otherwise.

    """
    return iface in ovs_bridges()


def ovs_bridge_ports(ovsbr):
    """Get the ports of a OVS bridge.

    In some distributions, like Fedora, the files bridge and brif are
    not created under /sys/class/net/<ovsbridge> for OVS bridges.
    These specific functions allows one to differentiate OVS bridges
    from other types of bridges.

    Args:
        ovsbr (str): name of the OVS bridge

    Returns:
        List[str]: a list with the ports of this bridge.

    """
    if not is_openvswitch_running():
        return []

    ovs_cmd = find_executable('ovs-vsctl')

    # openvswitch not installed: there is no OVS bridge configured
    if ovs_cmd is None:
        return []

    out, _, r_code = run_command([ovs_cmd, 'list-ports', ovsbr], silent=True)
    if r_code != 0:
        return []

    return [x.strip() for x in out.rstrip('\n').split('\n') if x.strip()]


def all_interfaces():
    """Returns all interfaces of the host.

    Returns:
        List[str]: a list with all interfaces of the host.

    """
    return [d.rsplit('/', 1)[-1] for d in glob.glob(NET_PATH + '/*')]


def slaves(bonding):
    """Get all slaves from a bonding.

    Args:
        bonding (str): the name of the bond.

    Returns:
        List[str]: a list with all slaves.

    """
    with open(BONDING_SLAVES % bonding) as bonding_file:
        res = bonding_file.readline().split()
    return res


def ports(bridge):
    """Get all ports from a bridge.

    Args:
        bridge (str): the name of the OVS bridge.

    Returns:
        List[str]: a list with all ports.

    """
    if bridge in ovs_bridges():
        return ovs_bridge_ports(bridge)

    return os.listdir(BRIDGE_PORTS % bridge)


def is_brport(nic):
    """Checks if nic is a port of a bridge.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a port of a bridge, False otherwise.

    """
    ovs_brports = []

    for ovsbr in ovs_bridges():
        ovs_brports += ovs_bridge_ports(ovsbr)

    return os.path.exists(NET_BRPORT % nic) or nic in ovs_brports


def is_bondlave(nic):
    """Checks if nic is a bond slave.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bond slave, False otherwise.

    """
    return os.path.exists(NET_MASTER % nic)


def operstate(dev):
    """Get the operstate status of a device.

    Args:
        dev (str): name of the device.

    Returns:
        str: "up" or "down"

    """
    flags = ethtool.get_flags(encode_value(dev))
    return 'up' if flags & (ethtool.IFF_RUNNING | ethtool.IFF_UP) else 'down'


def get_vlan_device(vlan):
    """ Return the device of the given VLAN.

    Args:
        vlan (str): the vlan name.

    Returns:
        str: the device of the VLAN.

    """
    dev = None

    if os.path.exists(PROC_NET_VLAN + vlan):
        with open(PROC_NET_VLAN + vlan) as vlan_file:
            for line in vlan_file:
                if 'Device:' in line:
                    dummy, dev = line.split()
                    break
    return dev


def get_bridge_port_device(bridge):
    """Return the nics list that belongs to a port of 'bridge'.

    Args:
        bridge (str): the bridge name.

    Returns:
        List[str]: the nic list.

    """
    #   br  --- v  --- bond --- nic1
    if encode_value(bridge) not in map(encode_value, bridges()):
        raise ValueError('unknown bridge %s' % bridge)
    nics_list = []
    for port in ports(bridge):
        if encode_value(port) in map(encode_value, vlans()):
            device = get_vlan_device(port)
            if encode_value(device) in map(encode_value, bondings()):
                nics_list.extend(slaves(device))
            else:
                nics_list.append(device)
        if encode_value(port) in map(encode_value, bondings()):
            nics_list.extend(slaves(port))
        else:
            nics_list.append(port)
    return nics_list


def aggregated_bridges():
    """Get the list of aggregated bridges of the host.

    Returns:
        List[str]: the aggregated bridges list.

    """
    return [bridge for bridge in bridges() if
            (set(get_bridge_port_device(bridge)) & set(nics()))]


def bare_nics():
    """Get the list of bare nics of the host.

    A nic is called bare when it is not a port of a bridge
    or a slave of bond.

    Returns:
        List[str]: the list of bare nics of the host.

    """
    return [nic for nic in nics() if not (is_brport(nic) or is_bondlave(nic))]


def is_bare_nic(iface):
    """Checks if iface is a bare nic.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bare nic, False otherwise.

    """
    return encode_value(iface) in map(encode_value, bare_nics())


#  The nic will not be exposed when it is a port of a bridge or
#  a slave of bond.
#  The bridge will not be exposed when all it's port are tap.
def all_favored_interfaces():
    """Get the list of all favored interfaces of the host.

    The nic will not be exposed when it is a port of a bridge or
    a slave of bond. The bridge will not be exposed when all its
    port are tap.

    Returns:
        List[str]: the list of favored interfaces.

   """
    return aggregated_bridges() + bare_nics() + bondings()


def get_interface_type(iface):
    """Get the interface type of iface.

    Types supported: nic, bonding, bridge, vlan. If the type
    can't be verified, 'unknown' is returned.

    Args:
        iface (str): the interface name.

    Returns:
        str: the interface type.

    """
    try:
        if is_nic(iface):
            return 'nic'
        if is_bonding(iface):
            return 'bonding'
        if is_bridge(iface):
            return 'bridge'
        if is_vlan(iface):
            return 'vlan'
        return 'unknown'
    except IOError:
        return 'unknown'


def get_dev_macaddr(dev):
    info = ethtool.get_interfaces_info(dev)[0]
    return info.mac_address


def get_dev_netaddr(dev):
    info = ethtool.get_interfaces_info(dev)[0]
    return (info.ipv4_address and
            '%s/%s' % (info.ipv4_address, info.ipv4_netmask) or '')


def get_dev_netaddrs():
    nets = []
    for dev in ethtool.get_devices():
        devnet = get_dev_netaddr(dev)
        devnet and nets.append(ipaddress.IPv4Network(devnet, False))
    return nets


# used_nets should include all the subnet allocated in libvirt network
# will get host network by get_dev_netaddrs
def get_one_free_network(used_nets, nets_pool=None):
    if nets_pool is None:
        nets_pool = PrivateNets

    def _get_free_network(nets, used_nets):
        for net in nets.subnets(new_prefix=24):
            if not any(net.overlaps(used) for used in used_nets):
                return str(net)
        return None

    used_nets = used_nets + get_dev_netaddrs()
    for nets in nets_pool:
        net = _get_free_network(nets, used_nets)
        if net:
            return net
    return None
