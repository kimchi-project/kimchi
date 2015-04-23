#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
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

import sys
import time

import ipaddr
import libvirt

from xml.sax.saxutils import escape

from kimchi import netinfo
from kimchi import network as knetwork
from kimchi.config import paths
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import MissingParameter, NotFoundError, OperationFailed
from kimchi.osinfo import defaults as tmpl_defaults
from kimchi.rollbackcontext import RollbackContext
from kimchi.utils import kimchi_log, run_command
from kimchi.xmlutils.network import create_vlan_tagged_bridge_xml
from kimchi.xmlutils.network import to_network_xml
from kimchi.xmlutils.utils import xpath_get_text


KIMCHI_BRIDGE_PREFIX = 'kb'


class NetworksModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        if self.conn.isQemuURI():
            self._check_default_networks()

    def _check_default_networks(self):
        networks = list(set(tmpl_defaults['networks']))
        conn = self.conn.get()

        error_msg = ("Please, check the configuration in %s/template.conf to "
                     "ensure it lists only valid networks." % paths.conf_dir)

        for net_name in networks:
            try:
                net = conn.networkLookupByName(net_name)
            except libvirt.libvirtError, e:
                msg = "Fatal: Unable to find network %s."
                kimchi_log.error(msg, net_name)
                kimchi_log.error(error_msg)
                kimchi_log.error("Details: %s", e.message)
                sys.exit(1)

            if net.isActive() == 0:
                try:
                    net.create()
                except libvirt.libvirtError as e:
                    msg = "Fatal: Unable to activate network %s."
                    kimchi_log.error(msg, net_name)
                    kimchi_log.error(error_msg)
                    kimchi_log.error("Details: %s", e.message)
                    sys.exit(1)

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

        params['name'] = escape(params['name'])
        xml = to_network_xml(**params)

        try:
            network = conn.networkDefineXML(xml.encode("utf-8"))
            network.setAutostart(True)
        except libvirt.libvirtError as e:
            raise OperationFailed("KCHNET0008E",
                                  {'name': name, 'err': e.get_error_message()})

        return name

    def get_list(self):
        conn = self.conn.get()
        names = conn.listNetworks() + conn.listDefinedNetworks()
        return sorted(map(lambda x: x.decode('utf-8'), names))

    def _get_available_address(self, addr_pools=[]):
        invalid_addrs = []
        for net_name in self.get_list():
            network = NetworkModel.get_network(self.conn.get(), net_name)
            xml = network.XMLDesc(0)
            subnet = NetworkModel.get_network_from_xml(xml)['subnet']
            subnet and invalid_addrs.append(ipaddr.IPNetwork(subnet))
            addr_pools = addr_pools if addr_pools else knetwork.PrivateNets
        return knetwork.get_one_free_network(invalid_addrs, addr_pools)

    def _set_network_subnet(self, params):
        netaddr = params.get('subnet', '')
        # lookup a free network address for nat and isolated automatically
        if not netaddr:
            netaddr = self._get_available_address()
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

    def _ensure_iface_up(self, iface):
        if netinfo.operstate(iface) != 'up':
            _, err, rc = run_command(['ip', 'link', 'set', 'dev', iface, 'up'])
            if rc != 0:
                raise OperationFailed("KCHNET0020E",
                                      {'iface': iface, 'err': err})
            # Add a delay to wait for the link change takes into effect.
            for i in range(10):
                time.sleep(1)
                if netinfo.operstate(iface) == 'up':
                    break
            else:
                raise OperationFailed("KCHNET0021E", {'iface': iface})

    def _set_network_bridge(self, params):
        try:
            iface = params['interface']
            if iface in self.get_all_networks_interfaces():
                msg_args = {'iface': iface, 'network': params['name']}
                raise InvalidParameter("KCHNET0006E", msg_args)
        except KeyError:
            raise MissingParameter("KCHNET0004E", {'name': params['name']})

        self._ensure_iface_up(iface)
        if netinfo.is_bridge(iface):
            if 'vlan_id' in params:
                raise InvalidParameter('KCHNET0019E', {'name': iface})
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
            network = conn.networkLookupByName(name.encode("utf-8"))
            xml = network.XMLDesc(0)
            net_dict = NetworkModel.get_network_from_xml(xml)
            forward = net_dict['forward']
            (forward['mode'] == 'bridge' and forward['interface'] and
             interfaces.append(forward['interface'][0]) is None or
             interfaces.extend(forward['interface'] + forward['pf']))
            net_dict['bridge'] and interfaces.append(net_dict['bridge'])
        return interfaces

    def _create_vlan_tagged_bridge(self, interface, vlan_id):
        # Truncate the interface name if it exceeds 8 characters to make sure
        # the length of bridge name is less than 15 (its maximum value).
        br_name = KIMCHI_BRIDGE_PREFIX + interface[-8:] + '-' + vlan_id
        br_xml = create_vlan_tagged_bridge_xml(br_name, interface, vlan_id)
        conn = self.conn.get()

        bridges = []
        for net in conn.listAllNetworks():
            # Bridged networks do not have a bridge name
            # So in those cases, libvirt raises an error when trying to get
            # the bridge name
            try:
                bridges.append(net.bridgeName())
            except libvirt.libvirtError, e:
                kimchi_log.error(e.message)

        if br_name in bridges:
            raise InvalidOperation("KCHNET0010E", {'iface': br_name})

        with RollbackContext() as rollback:
            try:
                vlan_tagged_br = conn.interfaceDefineXML(br_xml, 0)
                rollback.prependDefer(vlan_tagged_br.destroy)
                vlan_tagged_br.create(0)
            except libvirt.libvirtError as e:
                raise OperationFailed(e.message)
            else:
                return br_name


class NetworkModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']

    def lookup(self, name):
        network = self.get_network(self.conn.get(), name)
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
                'in_use': self._is_network_in_use(name),
                'autostart': network.autostart() == 1,
                'state':  network.isActive() and "active" or "inactive",
                'persistent': True if network.isPersistent() else False}

    def _is_network_in_use(self, name):
        # All the networks listed as default in template.conf file should not
        # be deactivate or deleted. Otherwise, we will allow user create
        # inconsistent templates from scratch
        if name in tmpl_defaults['networks']:
            return True

        vms = self._get_vms_attach_to_a_network(name)
        return bool(vms) or self._is_network_used_by_template(name)

    def _is_network_used_by_template(self, network):
        with self.objstore as session:
            templates = session.get_list('template')
            for tmpl in templates:
                tmpl_net = session.get('template', tmpl)['networks']
                if network in tmpl_net:
                    return True
            return False

    def _get_vms_attach_to_a_network(self, network, filter="all"):
        DOM_STATE_MAP = {'nostate': 0, 'running': 1, 'blocked': 2,
                         'paused': 3, 'shutdown': 4, 'shutoff': 5,
                         'crashed': 6}
        state = DOM_STATE_MAP.get(filter)
        vms = []
        conn = self.conn.get()
        for dom in conn.listAllDomains(0):
            networks = self._vm_get_networks(dom)
            if network.encode('utf-8') in networks and \
               (state is None or state == dom.state(0)[0]):
                vms.append(dom.name())
        return vms

    def _vm_get_networks(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/interface[@type='network']/source/@network"
        return xpath_get_text(xml, xpath)

    def activate(self, name):
        network = self.get_network(self.conn.get(), name)
        try:
            network.create()
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHNET0022E', {'name': name,
                                                  'err': e.message})

    def deactivate(self, name):
        if self._is_network_in_use(name):
            vms = self._get_vms_attach_to_a_network(name)
            vms.sort()
            raise InvalidOperation("KCHNET0018E", {'name': name,
                                                   'vms': ', '.join(vms)})

        network = self.get_network(self.conn.get(), name)
        network.destroy()

    def delete(self, name):
        if self._is_network_in_use(name):
            vms = self._get_vms_attach_to_a_network(name)
            vms.sort()
            raise InvalidOperation("KCHNET0017E", {'name': name,
                                                   'vms': ', '.join(vms)})

        network = self.get_network(self.conn.get(), name)
        if network.isActive():
            raise InvalidOperation("KCHNET0005E", {'name': name})

        self._remove_vlan_tagged_bridge(network)
        network.undefine()

    @staticmethod
    def get_network(conn, name):
        name = name.encode("utf-8")
        try:
            return conn.networkLookupByName(name)
        except libvirt.libvirtError:
            raise NotFoundError("KCHNET0002E", {'name': name})

    @staticmethod
    def get_network_from_xml(xml):
        address = xpath_get_text(xml, "/network/ip/@address")
        address = address and address[0] or ''
        netmask = xpath_get_text(xml, "/network/ip/@netmask")
        netmask = netmask and netmask[0] or ''
        net = address and netmask and "/".join([address, netmask]) or ''

        dhcp_start = xpath_get_text(xml, "/network/ip/dhcp/range/@start")
        dhcp_start = dhcp_start and dhcp_start[0] or ''
        dhcp_end = xpath_get_text(xml, "/network/ip/dhcp/range/@end")
        dhcp_end = dhcp_end and dhcp_end[0] or ''
        dhcp = {'start': dhcp_start, 'end': dhcp_end}

        forward_mode = xpath_get_text(xml, "/network/forward/@mode")
        forward_mode = forward_mode and forward_mode[0] or ''
        forward_if = xpath_get_text(xml, "/network/forward/interface/@dev")
        forward_pf = xpath_get_text(xml, "/network/forward/pf/@dev")
        bridge = xpath_get_text(xml, "/network/bridge/@name")
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
            if bridge.startswith(KIMCHI_BRIDGE_PREFIX):
                conn = self.conn.get()
                iface = conn.interfaceLookupByName(bridge)
                iface.isActive() and iface.destroy(0)
                iface.undefine()
