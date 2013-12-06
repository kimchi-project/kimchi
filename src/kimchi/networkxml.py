#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import ipaddr


# FIXME, do not support ipv6

def _get_dhcp_xml(**kwargs):
    """
    <dhcp>
      <range start="192.168.122.100" end="192.168.122.254" />
      <host mac="00:16:3e:77:e2:ed" name="foo.test.com" ip="192.168.122.10" />
      <host mac="00:16:3e:3e:a9:1a" name="bar.test.com" ip="192.168.122.11" />
    </dhcp>
    """
    xml = ''
    dhcp_range = "  <range start='%(start)s' end='%(end)s' />"
    ipv4host = "  <host mac='%(mac)s' name='%(name)s' ip='%(ip)s' />"
    dhcp = []
    if 'range' in kwargs.keys():
        dhcp.append(dhcp_range % kwargs['range'])
    if 'hosts' in kwargs.keys():
        dhcp.extend([ipv4host % host for host in kwargs['hosts']])
    if dhcp:
        xml = "\n".join(["<dhcp>"] + dhcp + ["</dhcp>"])
    return xml


def _get_ip_xml(**kwargs):
    """
    <ip address="192.168.152.1" netmask="255.255.255.0">
      <dhcp>
        <range start="192.168.152.2" end="192.168.152.254" />
      </dhcp>
    </ip>
    """
    xml = ""
    if 'net' in kwargs.keys():
        net = ipaddr.IPNetwork(kwargs['net'])
        address = str(net.ip)
        netmask = str(net.netmask)
        dhcp_params = kwargs.get('dhcp', {})
        dhcp = _get_dhcp_xml(**dhcp_params)
        xml = """
          <ip address='%s' netmask='%s'>"
            %s
          </ip>""" % (address, netmask, dhcp)
    return xml


def _get_forward_xml(**kwargs):
    """
    <forward mode='hostdev' dev='eth0' managed='yes'>
    </forward>
    """

    if "mode" in kwargs.keys() and kwargs['mode'] is None:
        return ""
    mode = " mode='%s'" % kwargs['mode'] if 'mode' in kwargs.keys() else ""
    dev = " dev='%s'" % kwargs['dev'] if 'dev' in kwargs.keys() else ""
    managed = (" managed='%s'" % kwargs['managed']
               if 'managed' in kwargs.keys() else "")
    xml = """
      <forward %s%s%s>
      </forward>
    """ % (mode, dev, managed)
    return xml


def to_network_xml(**kwargs):

    params = {'name': kwargs['name']}
    # None means is Isolated network, {} means default mode nat
    forward = kwargs.get('forward', {"mode": None})
    ip = {'net': kwargs['net']} if 'net' in kwargs else {}
    ip['dhcp'] = kwargs.get('dhcp', {})
    bridge = kwargs.get('bridge')
    params = {'name': kwargs['name'],
              'forward': _get_forward_xml(**forward),
              'bridge': "<bridge name='%s' />" % bridge if bridge else "",
              'ip': _get_ip_xml(**ip)}

    xml = """
    <network>
      <name>%(name)s</name>
        %(bridge)s
        %(forward)s
        %(ip)s
    </network>
    """ % params
    return xml
