#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

import ipaddr
import libvirt

from kimchi import netinfo
from kimchi import network as knetwork
from kimchi import networkxml
from kimchi import xmlutils
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import MissingParameter, NotFoundError, OperationFailed


class NetworksModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def create(self, params):
        conn = self.conn.get()
        name = params['name']
        if name in self.get_list():
            raise InvalidOperation("KCHNET0001E", {'name': name})

        connection = params["connection"]
        # set forward mode, isolated do not need forward
        if connection != 'isolated':
            params['forward'] = {'mode': connection}

        # set subnet, bridge network do not need subnet
        if connection in ["nat", 'isolated']:
            self._set_network_subnet(params)

        # only bridge network need bridge(linux bridge) or interface(macvtap)
        if connection == 'bridge':
            self._set_network_bridge(params)

        xml = networkxml.to_network_xml(**params)

        try:
            network = conn.networkDefineXML(xml)
            network.setAutostart(True)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHNET0008E",
                                  {'name': name, 'err': e.get_error_message()})

        return name

    def get_list(self):
        conn = self.conn.get()
        return sorted(conn.listNetworks() + conn.listDefinedNetworks())

    def _set_network_subnet(self, params):
        netaddr = params.get('subnet', '')
        net_addrs = []
        # lookup a free network address for nat and isolated automatically
        if not netaddr:
            for net_name in self.get_list():
                network = self._get_network(net_name)
                xml = network.XMLDesc(0)
                subnet = NetworkModel.get_network_from_xml(xml)['subnet']
                subnet and net_addrs.append(ipaddr.IPNetwork(subnet))
            netaddr = knetwork.get_one_free_network(net_addrs)
            if not netaddr:
                raise OperationFailed("KCHNET0009E", {'name': params['name']})

        try:
            ip = ipaddr.IPNetwork(netaddr)
        except ValueError:
            raise InvalidParameter("KCHNET0003E", {'subent': netaddr,
                                                   'network': params['name']})

        if ip.ip == ip.network:
            ip.ip = ip.ip + 1

        dhcp_start = str(ip.ip + ip.numhosts / 2)
        dhcp_end = str(ip.ip + ip.numhosts - 2)
        params.update({'net': str(ip),
                       'dhcp': {'range': {'start': dhcp_start,
                                'end': dhcp_end}}})

    def _set_network_bridge(self, params):
        try:
            iface = params['interface']
            if iface in self.get_all_networks_interfaces():
                msg_args = {'iface': iface, 'network': params['name']}
                raise InvalidParameter("KCHNET0006E", msg_args)
        except KeyError:
            raise MissingParameter("KCHNET0004E", {'name': params['name']})

        if netinfo.is_bridge(iface):
            params['bridge'] = iface
        elif netinfo.is_bare_nic(iface) or netinfo.is_bonding(iface):
            if params.get('vlan_id') is None:
                params['forward']['dev'] = iface
            else:
                params['bridge'] = \
                    self._create_vlan_tagged_bridge(str(iface),
                                                    str(params['vlan_id']))
        else:
            raise InvalidParameter("KCHNET0007E")

    def get_all_networks_interfaces(self):
        net_names = self.get_list()
        interfaces = []
        for name in net_names:
            conn = self.conn.get()
            network = conn.networkLookupByName(name)
            xml = network.XMLDesc(0)
            net_dict = NetworkModel.get_network_from_xml(xml)
            forward = net_dict['forward']
            (forward['mode'] == 'bridge' and forward['interface'] and
             interfaces.append(forward['interface'][0]) is None or
             interfaces.extend(forward['interface'] + forward['pf']))
            net_dict['bridge'] and interfaces.append(net_dict['bridge'])
        return interfaces

    def _create_vlan_tagged_bridge(self, interface, vlan_id):
        br_name = '-'.join(('kimchi', interface, vlan_id))
        br_xml = networkxml.create_vlan_tagged_bridge_xml(br_name, interface,
                                                          vlan_id)
        conn = self.conn.get()
        conn.changeBegin()
        try:
            vlan_tagged_br = conn.interfaceDefineXML(br_xml)
            vlan_tagged_br.create()
        except libvirt.libvirtError as e:
            conn.changeRollback()
            raise OperationFailed("KCHNET0010E", {'iface': interface,
                                                  'err': e.message})
        else:
            conn.changeCommit()
            return br_name


class NetworkModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def lookup(self, name):
        network = self._get_network(name)
        xml = network.XMLDesc(0)
        net_dict = self.get_network_from_xml(xml)
        subnet = net_dict['subnet']
        dhcp = net_dict['dhcp']
        forward = net_dict['forward']
        interface = net_dict['bridge']

        connection = forward['mode'] or "isolated"
        # FIXME, if we want to support other forward mode well.
        if connection == 'bridge':
            # macvtap bridge
            interface = interface or forward['interface'][0]
            # exposing the network on linux bridge or macvtap interface
            interface_subnet = knetwork.get_dev_netaddr(interface)
            subnet = subnet if subnet else interface_subnet

        # libvirt use format 192.168.0.1/24, standard should be 192.168.0.0/24
        # http://www.ovirt.org/File:Issue3.png
        if subnet:
            subnet = ipaddr.IPNetwork(subnet)
            subnet = "%s/%s" % (subnet.network, subnet.prefixlen)

        return {'connection': connection,
                'interface': interface,
                'subnet': subnet,
                'dhcp': dhcp,
                'vms': self._get_vms_attach_to_a_network(name),
                'autostart': network.autostart() == 1,
                'state':  network.isActive() and "active" or "inactive"}

    def _get_vms_attach_to_a_network(self, network):
        vms = []
        conn = self.conn.get()
        for dom in conn.listAllDomains(0):
            networks = self._vm_get_networks(dom)
            if network in networks:
                vms.append(dom.name())
        return vms

    def _vm_get_networks(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/interface[@type='network']/source/@network"
        return xmlutils.xpath_get_text(xml, xpath)

    def activate(self, name):
        network = self._get_network(name)
        network.create()

    def deactivate(self, name):
        network = self._get_network(name)
        network.destroy()

    def delete(self, name):
        network = self._get_network(name)
        if network.isActive():
            raise InvalidOperation("KCHNET0005E", {'name': name})

        self._remove_vlan_tagged_bridge(network)
        network.undefine()

    def _get_network(self, name):
        conn = self.conn.get()
        try:
            return conn.networkLookupByName(name)
        except libvirt.libvirtError:
            raise NotFoundError("KCHNET0002E", {'name': name})

    @staticmethod
    def get_network_from_xml(xml):
        address = xmlutils.xpath_get_text(xml, "/network/ip/@address")
        address = address and address[0] or ''
        netmask = xmlutils.xpath_get_text(xml, "/network/ip/@netmask")
        netmask = netmask and netmask[0] or ''
        net = address and netmask and "/".join([address, netmask]) or ''

        dhcp_start = xmlutils.xpath_get_text(xml,
                                             "/network/ip/dhcp/range/@start")
        dhcp_start = dhcp_start and dhcp_start[0] or ''
        dhcp_end = xmlutils.xpath_get_text(xml, "/network/ip/dhcp/range/@end")
        dhcp_end = dhcp_end and dhcp_end[0] or ''
        dhcp = {'start': dhcp_start, 'end': dhcp_end}

        forward_mode = xmlutils.xpath_get_text(xml, "/network/forward/@mode")
        forward_mode = forward_mode and forward_mode[0] or ''
        forward_if = xmlutils.xpath_get_text(xml,
                                             "/network/forward/interface/@dev")
        forward_pf = xmlutils.xpath_get_text(xml, "/network/forward/pf/@dev")
        bridge = xmlutils.xpath_get_text(xml, "/network/bridge/@name")
        bridge = bridge and bridge[0] or ''
        return {'subnet': net, 'dhcp': dhcp, 'bridge': bridge,
                'forward': {'mode': forward_mode,
                            'interface': forward_if,
                            'pf': forward_pf}}

    def _remove_vlan_tagged_bridge(self, network):
        try:
            bridge = network.bridgeName()
        except libvirt.libvirtError:
            pass
        else:
            if bridge.startswith('kimchi-'):
                conn = self.conn.get()
                iface = conn.interfaceLookupByName(bridge)
                if iface.isActive():
                    iface.destroy()
                iface.undefine()
