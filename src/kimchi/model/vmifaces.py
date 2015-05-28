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

import random

import libvirt
from lxml import etree, objectify

from kimchi.exception import InvalidParameter, MissingParameter
from kimchi.exception import NotFoundError, InvalidOperation
from kimchi.model.config import CapabilitiesModel
from kimchi.model.vms import DOM_STATE_MAP, VMModel
from kimchi.xmlutils.interface import get_iface_xml


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
        networks = conn.listNetworks() + conn.listDefinedNetworks()
        networks = map(lambda x: x.decode('utf-8'), networks)

        if params['type'] == 'network':
            network = params.get("network")

            if network is None:
                raise MissingParameter('KCHVMIF0007E')

            if network not in networks:
                raise InvalidParameter('KCHVMIF0002E',
                                       {'name': vm, 'network': network})

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

        os_data = VMModel.vm_get_os_metadata(dom, self.caps.metadata_support)
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
        if iface.find("model") is not None:
            info['model'] = iface.model.get('type')
        if info['type'] == 'network':
            info['network'] = iface.source.get('network')
        if info['type'] == 'bridge':
            info['bridge'] = iface.source.get('bridge')

        return info

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
