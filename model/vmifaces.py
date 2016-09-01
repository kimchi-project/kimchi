#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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

import libvirt
import os
import random
from lxml import etree, objectify

from wok.exception import InvalidParameter, MissingParameter
from wok.exception import NotFoundError, InvalidOperation

from wok.plugins.kimchi.model.config import CapabilitiesModel
from wok.plugins.kimchi.model.vms import DOM_STATE_MAP, VMModel
from wok.plugins.kimchi.xmlutils.interface import get_iface_xml


class VMIfacesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.caps = CapabilitiesModel(**kargs)

    def get_list(self, vm):
        macs = []
        for iface in self.get_vmifaces(vm, self.conn):
            macs.append(iface.mac.get('address'))
        return macs

    def create(self, vm, params):
        conn = self.conn.get()

        if params['type'] == 'network':
            network = params.get("network")

            if network is None:
                raise MissingParameter('KCHVMIF0007E')

            networks = conn.listNetworks() + conn.listDefinedNetworks()
            networks = map(lambda x: x.decode('utf-8'), networks)

            if network not in networks:
                raise InvalidParameter('KCHVMIF0002E',
                                       {'name': vm, 'network': network})

        # For architecture other than s390x/s390 type ovs/macvtap
        # and source interface are not supported.
        if os.uname()[4] not in ['s390x', 's390']:
            if params['type'] in ['ovs', 'macvtap']:
                raise InvalidParameter('KCHVMIF0012E')
            if params.get('source'):
                raise InvalidParameter('KCHVMIF0013E')

        # For s390x/s390 architecture
        if os.uname()[4] in ['s390x', 's390']:
            params['name'] = params.get("source", None)

            # For type ovs and mavtap, source interface has to be provided.
            if params['name'] is None and params['type'] in ['ovs', 'macvtap']:
                raise InvalidParameter('KCHVMIF0015E')
            # If source interface provided, only type supported are ovs
            # and mavtap.
            if params['name'] is not None and \
               params['type'] not in ['ovs', 'macvtap']:
                raise InvalidParameter('KCHVMIF0014E')

            # FIXME: Validation if source interface exists.
            if params['type'] == 'macvtap':
                params['type'] = 'direct'
                params['mode'] = params.get('mode', None)
            elif params['type'] == 'ovs':
                params['type'] = 'bridge'
                params['virtualport_type'] = 'openvswitch'

        macs = (iface.mac.get('address')
                for iface in self.get_vmifaces(vm, self.conn))

        # user defined customized mac address
        if 'mac' in params and params['mac']:
            # make sure it is unique
            if params['mac'] in macs:
                raise InvalidParameter('KCHVMIF0009E',
                                       {'name': vm, 'mac': params['mac']})

        # otherwise choose a random mac address
        else:
            while True:
                params['mac'] = VMIfacesModel.random_mac()
                if params['mac'] not in macs:
                    break

        dom = VMModel.get_vm(vm, self.conn)

        os_data = VMModel.vm_get_os_metadata(dom)
        os_version, os_distro = os_data
        xml = get_iface_xml(params, conn.getInfo()[0], os_distro, os_version)

        flags = 0
        if dom.isPersistent():
            flags |= libvirt.VIR_DOMAIN_AFFECT_CONFIG
        if DOM_STATE_MAP[dom.info()[0]] != "shutoff":
            flags |= libvirt.VIR_DOMAIN_AFFECT_LIVE
        dom.attachDeviceFlags(xml, flags)

        return params['mac']

    @staticmethod
    def get_vmifaces(vm, conn):
        dom = VMModel.get_vm(vm, conn)
        xml = dom.XMLDesc(0)
        root = objectify.fromstring(xml)

        return root.devices.findall("interface")

    @staticmethod
    def random_mac():
        mac = [0x52, 0x54, 0x00,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: u'%02x' % x, mac))


class VMIfaceModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def _get_vmiface(self, vm, mac):
        ifaces = VMIfacesModel.get_vmifaces(vm, self.conn)

        for iface in ifaces:
            if iface.mac.get('address') == mac:
                return iface
        return None

    def lookup(self, vm, mac):
        info = {}

        iface = self._get_vmiface(vm, mac)
        if iface is None:
            raise NotFoundError("KCHVMIF0001E", {'name': vm, 'iface': mac})

        info['type'] = iface.attrib['type']
        info['mac'] = iface.mac.get('address')

        if iface.find('virtualport') is not None:
            info['virtualport'] = iface.virtualport.get('type')

        if info['type'] == 'direct':
            info['source'] = iface.source.get('dev')
            info['mode'] = iface.source.get('mode')
            info['type'] = 'macvtap'
        elif (info['type'] == 'bridge' and
              info.get('virtualport') == 'openvswitch'):
            info['source'] = iface.source.get('bridge')
            info['type'] = 'ovs'
        else:
            info['network'] = iface.source.get('network')

        if iface.find("model") is not None:
            info['model'] = iface.model.get('type')
        if info['type'] == 'bridge' and \
           info.get('virtualport') != 'openvswitch':
            info['bridge'] = iface.source.get('bridge')
        if info.get('network'):
            info['ips'] = self._get_ips(vm, info['mac'], info['network'])
        info.pop('virtualport', None)
        return info

    def _get_ips(self, vm, mac, network):
        ips = []

        # Return empty list if shutoff, even if leases still valid or ARP
        #   cache has entries for this MAC.
        conn = self.conn.get()
        dom = VMModel.get_vm(vm, self.conn)
        if DOM_STATE_MAP[dom.info()[0]] == "shutoff":
            return ips

        # An iface may have multiple IPs
        # An IP could have been assigned without libvirt.
        # First check the ARP cache.
        with open('/proc/net/arp') as f:
            ips = [line.split()[0] for line in f.xreadlines() if mac in line]

        # Some ifaces may be inactive, so if the ARP cache didn't have them,
        # and they happen to be assigned via DHCP, we can check there too.
        try:
            # Some type of interfaces may not have a network associated with
            net = conn.networkLookupByName(network)
            leases = net.DHCPLeases(mac)
            for lease in leases:
                ip = lease.get('ipaddr')
                if ip not in ips:
                    ips.append(ip)
        except libvirt.libvirtError:
            pass

        return ips

    def delete(self, vm, mac):
        dom = VMModel.get_vm(vm, self.conn)
        iface = self._get_vmiface(vm, mac)

        if iface is None:
            raise NotFoundError("KCHVMIF0001E", {'name': vm, 'iface': mac})

        flags = 0
        if dom.isPersistent():
            flags |= libvirt.VIR_DOMAIN_AFFECT_CONFIG
        if DOM_STATE_MAP[dom.info()[0]] != "shutoff":
            flags |= libvirt.VIR_DOMAIN_AFFECT_LIVE

        dom.detachDeviceFlags(etree.tostring(iface), flags)

    def update(self, vm, mac, params):
        dom = VMModel.get_vm(vm, self.conn)
        iface = self._get_vmiface(vm, mac)

        if iface is None:
            raise NotFoundError("KCHVMIF0001E", {'name': vm, 'iface': mac})

        # cannot change mac address in a running system
        if DOM_STATE_MAP[dom.info()[0]] != "shutoff":
            raise InvalidOperation('KCHVMIF0011E')

        # mac address is a required parameter
        if 'mac' not in params:
            raise MissingParameter('KCHVMIF0008E')

        # new mac address must be unique
        if self._get_vmiface(vm, params['mac']) is not None:
            raise InvalidParameter('KCHVMIF0009E',
                                   {'name': vm, 'mac': params['mac']})

        flags = 0
        if dom.isPersistent():
            flags |= libvirt.VIR_DOMAIN_AFFECT_CONFIG

        # remove the current nic
        xml = etree.tostring(iface)
        dom.detachDeviceFlags(xml, flags=flags)

        # add the nic with the desired mac address
        iface.mac.attrib['address'] = params['mac']
        xml = etree.tostring(iface)
        dom.attachDeviceFlags(xml, flags=flags)

        return [vm, params['mac']]
