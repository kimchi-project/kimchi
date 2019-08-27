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
import lxml.etree as ET
from lxml.builder import E
from wok.plugins.kimchi import osinfo


def get_iface_xml(params, arch=None, os_distro=None, os_version=None):
    typ = params.get('type', 'network')
    if typ == 'bridge':
        return get_iface_ovs_xml(params, arch)
    elif typ == 'direct':
        return get_iface_macvtap_xml(params, arch)
    return get_iface_network_xml(params, arch, os_distro, os_version)


def get_iface_network_xml(params, arch=None, os_distro=None, os_version=None):
    """
    <interface type='network' name='ethX'>
      <start mode='onboot'/>
      <source network='default'/>
      <model type='virtio'/>
    </interface>
    """
    name = params.get('name', None)
    if name:
        interface = E.interface(type=params.get('type', 'network'), name=name)
    else:
        interface = E.interface(type=params.get('type', 'network'))

    stmode = params.get('startmode', None)
    if stmode:
        interface.append(E.start(mode=stmode))

    nw = params.get('network', None)
    if nw:
        interface.append(E.source(network=nw))

    model = params.get('model', None)

    # no model specified; let's try querying osinfo
    if model is None:
        # if os_distro and os_version are invalid, nic_model will also be None
        model = osinfo.lookup(os_distro, os_version).get('nic_model')

    # only append 'model' to the XML if it's been specified as a parameter or
    # returned by osinfo.lookup; otherwise let libvirt use its default value
    if model is not None:
        interface.append(E.model(type=model))

    mac = params.get('mac', None)
    if mac is not None:
        interface.append(E.mac(address=mac))

    return ET.tostring(interface, encoding='unicode', pretty_print=True)


def get_iface_macvtap_xml(params, arch=None):
    """
    <interface type="direct">
      <source dev="bondX" mode="bridge"/>
      <model type="virtio"/>
    </interface>
    """
    device = params['name']
    interface = E.interface(type=params['type'])
    mode = params.get('mode', None)
    if mode is not None:
        interface.append(E.source(dev=device, mode=mode))
    else:
        interface.append(E.source(dev=device))

    model = params.get('model', None)

    # only append 'model' to the XML if it's been specified as a parameter
    # otherwise let libvirt use its default value
    if model is not None:
        interface.append(E.model(type=model))

    mac = params.get('mac', None)
    if mac is not None:
        interface.append(E.mac(address=mac))

    return ET.tostring(interface, encoding='unicode', pretty_print=True)


def get_iface_ovs_xml(params, arch=None):
    """
    <interface type="bridge">
      <source bridge="vswitchX"/>
      <virtualport type="openvswitch"/>
      <model type="virtio"/>
    </interface>
    """
    device = params['name']
    interface = E.interface(type=params['type'])
    interface.append(E.source(bridge=device))
    virtualport_type = params.get('virtualport_type', 'openvswitch')
    interface.append(E.virtualport(type=virtualport_type))

    model = params.get('model', None)

    # only append 'model' to the XML if it's been specified as a parameter
    # otherwise let libvirt use its default value
    if model is not None:
        interface.append(E.model(type=model))

    mac = params.get('mac', None)
    if mac is not None:
        interface.append(E.mac(address=mac))

    return ET.tostring(interface, encoding='unicode', pretty_print=True)
