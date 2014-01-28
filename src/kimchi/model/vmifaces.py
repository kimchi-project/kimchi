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

import random

import libvirt
from lxml import etree, objectify
from lxml.builder import E

from kimchi.exception import InvalidOperation, InvalidParameter, NotFoundError
from kimchi.model.vms import DOM_STATE_MAP, VMModel


class VMIfacesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def get_list(self, vm):
        macs = []
        for iface in self.get_vmifaces(vm, self.conn):
            macs.append(iface.mac.get('address'))
        return macs

    def create(self, vm, params):
        def randomMAC():
            mac = [0x52, 0x54, 0x00,
                   random.randint(0x00, 0x7f),
                   random.randint(0x00, 0xff),
                   random.randint(0x00, 0xff)]
            return ':'.join(map(lambda x: "%02x" % x, mac))

        conn = self.conn.get()
        networks = conn.listNetworks() + conn.listDefinedNetworks()

        if params["type"] == "network" and params["network"] not in networks:
            raise InvalidParameter("%s is not an available network" %
                                   params["network"])

        dom = VMModel.get_vm(vm, self.conn)
        if DOM_STATE_MAP[dom.info()[0]] != "shutoff":
            raise InvalidOperation("do not support hot plugging attach "
                                   "guest interface")

        macs = (iface.mac.get('address')
                for iface in self.get_vmifaces(vm, self.conn))

        mac = randomMAC()
        while True:
            if mac not in macs:
                break
            mac = randomMAC()

        children = [E.mac(address=mac)]
        ("network" in params.keys() and
         children.append(E.source(network=params['network'])))
        ("model" in params.keys() and
         children.append(E.model(type=params['model'])))
        attrib = {"type": params["type"]}

        xml = etree.tostring(E.interface(*children, **attrib))

        dom.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

        return mac

    @staticmethod
    def get_vmifaces(vm, conn):
        dom = VMModel.get_vm(vm, conn)
        xml = dom.XMLDesc(0)
        root = objectify.fromstring(xml)

        return root.devices.findall("interface")


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
            raise NotFoundError('iface: "%s"' % mac)

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

        if DOM_STATE_MAP[dom.info()[0]] != "shutoff":
            raise InvalidOperation("do not support hot plugging detach "
                                   "guest interface")
        if iface is None:
            raise NotFoundError('iface: "%s"' % mac)

        dom.detachDeviceFlags(etree.tostring(iface),
                              libvirt.VIR_DOMAIN_AFFECT_CURRENT)
