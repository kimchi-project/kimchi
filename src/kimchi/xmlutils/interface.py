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

import lxml.etree as ET

from distutils.version import LooseVersion
from lxml.builder import E

from kimchi import osinfo


def get_iface_xml(params, arch=None, os_distro=None, os_version=None):
    """
    <interface type='network'>
      <source network='default'/>
      <model type='virtio'/>
    </interface>
    """
    interface = E.interface(type=params['type'])
    interface.append(E.source(network=params['network']))

    model = params.get('model')

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

    # Hack to disable vhost feature in Ubuntu LE and SLES LE (PPC)
    if arch == 'ppc64' and \
       ((os_distro == 'ubuntu' and
         LooseVersion(os_version) >= LooseVersion('14.04')) or
        (os_distro == 'sles' and
         LooseVersion(os_version) >= LooseVersion('12'))):
        interface.append(E.driver(name='qemu'))

    return ET.tostring(interface, encoding='utf-8', pretty_print=True)
