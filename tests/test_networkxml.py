#
# Kimchi
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

import ipaddr
import unittest
import lxml.etree as ET

import utils

from kimchi.xmlutils import network as nxml
from kimchi.xmlutils.utils import xpath_get_text


class NetworkXmlTests(unittest.TestCase):
    def test_dhcp_xml(self):
        """
        Test network dhcp xml
        """
        dhcp_range = {"start": "192.168.122.100", "end": "192.168.122.254"}
        host1 = {"mac": "00:16:3e:77:e2:ed",
                 "name": "foo.example.com",
                 "ip": "192.168.122.10"}
        host2 = {"mac": "00:16:3e:3e:a9:1a",
                 "name": "bar.example.com",
                 "ip": "192.168.122.11"}
        params = {}

        dhcp = nxml._get_dhcp_elem(**params)
        self.assertEquals(None, dhcp)

        params["range"] = dhcp_range
        xml = ET.tostring(nxml._get_dhcp_elem(**params))
        start = xpath_get_text(xml, "/dhcp/range/@start")
        end = xpath_get_text(xml, "/dhcp/range/@end")
        self.assertEquals(dhcp_range['start'], start[0])
        self.assertEquals(dhcp_range['end'], end[0])

        params["hosts"] = [host1, host2]
        xml = ET.tostring(nxml._get_dhcp_elem(**params))
        ip = xpath_get_text(xml, "/dhcp/host/@ip")
        self.assertEquals(ip, [host1['ip'], host2['ip']])

    def test_ip_xml(self):
        """
        Test network ip xml
        """
        dhcp_range = {"start": "192.168.122.100", "end": "192.168.122.254"}
        params = {}

        dhcp = nxml._get_dhcp_elem(**params)
        self.assertEquals(None, dhcp)

        params["net"] = "192.168.122.0/255.255.255.0"
        params["dhcp"] = {'range': dhcp_range}
        xml = ET.tostring(nxml._get_ip_elem(**params))
        start = xpath_get_text(xml, "/ip/dhcp/range/@start")[0]
        end = xpath_get_text(xml, "/ip/dhcp/range/@end")[0]
        self.assertEquals(dhcp_range['start'], start)
        self.assertEquals(dhcp_range['end'], end)

        address = xpath_get_text(xml, "/ip/@address")[0]
        netmask = xpath_get_text(xml, "/ip/@netmask")[0]
        self.assertEquals(address, params["net"].split("/")[0])
        self.assertEquals(netmask, params["net"].split("/")[1])

        # test _get_ip_xml can accepts strings: '192.168.122.0/24',
        # which is same as "192.168.122.0/255.255.255.0"
        params["net"] = "192.168.122.0/24"
        xml = ET.tostring(nxml._get_ip_elem(**params))
        netmask = xpath_get_text(xml, "/ip/@netmask")[0]
        self.assertEquals(netmask,
                          str(ipaddr.IPNetwork(params["net"]).netmask))

    def test_forward_xml(self):
        """
        Test network forward xml
        """
        params = {"mode": None}

        forward = nxml._get_forward_elem(**params)
        self.assertEquals(None, forward)

        params["mode"] = 'nat'
        params["dev"] = 'eth0'
        xml = ET.tostring(nxml._get_forward_elem(**params))
        mode = xpath_get_text(xml, "/forward/@mode")[0]
        dev = xpath_get_text(xml, "/forward/@dev")[0]
        self.assertEquals(params['mode'], mode)
        self.assertEquals(params['dev'], dev)

    def test_network_xml(self):
        """
        Test network xml
        """
        params = {"name": "test",
                  "forward": {"mode": "nat", "dev": ""},
                  "net": "192.168.0.0/255.255.255.0"}
        xml = nxml.to_network_xml(**params)
        name = xpath_get_text(xml, "/network/name")[0]
        self.assertEquals(name, params['name'])

        forward_mode = xpath_get_text(xml, "/network/forward/@mode")[0]
        self.assertEquals(forward_mode, params['forward']['mode'])
        forward_dev = xpath_get_text(xml, "/network/forward/@dev")[0]
        self.assertEquals(forward_dev, '')

        address = xpath_get_text(xml, "/network/ip/@address")[0]
        self.assertEquals(address, params["net"].split("/")[0])
        netmask = xpath_get_text(xml, "/network/ip/@netmask")[0]
        self.assertEquals(netmask, params["net"].split("/")[1])

        dhcp_start = xpath_get_text(xml, "/network/ip/dhcp/range/@start")
        self.assertEquals(dhcp_start, [])
        dhcp_end = xpath_get_text(xml, "/network/ip/dhcp/range/@end")
        self.assertEquals(dhcp_end, [])

        # test optional params
        params['forward']['dev'] = "eth0"
        params['dhcp'] = {"range": {'start': '192.168.0.1',
                                    'end': '192.168.0.254'}}
        xml = nxml.to_network_xml(**params)
        forward_dev = xpath_get_text(xml, "/network/forward/@dev")[0]
        self.assertEquals(forward_dev, params['forward']['dev'])

        dhcp_start = xpath_get_text(xml, "/network/ip/dhcp/range/@start")[0]
        self.assertEquals(dhcp_start, params['dhcp']['range']['start'])
        dhcp_end = xpath_get_text(xml, "/network/ip/dhcp/range/@end")[0]
        self.assertEquals(dhcp_end, params['dhcp']['range']['end'])

        # test _get_ip_xml can accepts strings: '192.168.122.0/24',
        # which is same as "192.168.122.0/255.255.255.0"
        params["net"] = "192.168.0.0/24"
        xml = nxml.to_network_xml(**params)
        netmask = xpath_get_text(xml, "/network/ip/@netmask")[0]
        self.assertEquals(netmask,
                          str(ipaddr.IPNetwork(params["net"]).netmask))


class InterfaceXmlTests(unittest.TestCase):

    def test_vlan_tagged_bridge_no_ip(self):
        expected_xml = """
            <interface type='bridge' name='br10'>
                <start mode='onboot'/>
                <bridge>
                    <interface type='vlan' name='em1.10'>
                      <vlan tag='10'>
                        <interface name='em1'/>
                      </vlan>
                    </interface>
              </bridge>
            </interface>
            """
        actual_xml = nxml.create_vlan_tagged_bridge_xml('br10', 'em1', '10')
        self.assertEquals(actual_xml, utils.normalize_xml(expected_xml))
