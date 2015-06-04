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

import libvirt
from lxml import etree, objectify
from lxml.builder import E, ElementMaker

from kimchi.exception import OperationFailed

KIMCHI_META_URL = "https://github.com/kimchi-project/kimchi"
KIMCHI_NAMESPACE = "kimchi"


def get_vm_name(vm_name, t_name, name_list):
    if vm_name:
        return vm_name
    for i in xrange(1, 1000):
        # VM will have templace name, but without slashes
        vm_name = "%s-vm-%i" % (t_name.replace('/', '-'), i)
        if vm_name not in name_list:
            return vm_name
    raise OperationFailed("KCHUTILS0003E")


def get_vm_config_flag(dom, mode="persistent"):
    # libvirt.VIR_DOMAIN_AFFECT_CURRENT is 0
    # VIR_DOMAIN_AFFECT_LIVE is 1, VIR_DOMAIN_AFFECT_CONFIG is 2
    flag = {"live": libvirt.VIR_DOMAIN_AFFECT_LIVE,
            "persistent": libvirt.VIR_DOMAIN_AFFECT_CONFIG,
            "current": libvirt.VIR_DOMAIN_AFFECT_CURRENT,
            "all": libvirt.VIR_DOMAIN_AFFECT_CONFIG +
            libvirt.VIR_DOMAIN_AFFECT_LIVE if dom.isActive() and
            dom.isPersistent() else libvirt.VIR_DOMAIN_AFFECT_CURRENT}

    return flag[mode]


# avoid duplicate codes
def update_node(root, node):
    old_node = root.find(node.tag)
    (root.replace(old_node, node) if old_node is not None
     else root.append(node))
    return root


def _kimchi_set_metadata_node(dom, node):
    # some other tools will not let libvirt create a persistent
    # configuration, raise exception.
    if not dom.isPersistent():
        msg = 'The VM has not a persistent configuration'
        raise OperationFailed("KCHVM0030E",
                              {'name': dom.name(), "err": msg})
    xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
    root = etree.fromstring(xml)
    kimchi = root.find("metadata/{%s}kimchi" % KIMCHI_META_URL)

    EM = ElementMaker(namespace=KIMCHI_META_URL,
                      nsmap={KIMCHI_NAMESPACE: KIMCHI_META_URL})
    kimchi = EM("kimchi") if kimchi is None else kimchi

    update_node(kimchi, node)
    metadata = root.find("metadata")
    metadata = E.metadata() if metadata is None else metadata
    update_node(metadata, kimchi)
    update_node(root, metadata)
    dom.connect().defineXML(etree.tostring(root))


def libvirt_get_kimchi_metadata_node(dom, mode="current"):
    if not metadata_exists(dom):
        return None
    try:
        xml = dom.metadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT,
                           KIMCHI_META_URL,
                           flags=get_vm_config_flag(dom, mode))
        return etree.fromstring(xml)
    except libvirt.libvirtError:
        return None


def set_metadata_node(dom, node, metadata_support, mode="all"):
    if metadata_support:
        kimchi = libvirt_get_kimchi_metadata_node(dom, mode)
        kimchi = E.metadata(E.kimchi()) if kimchi is None else kimchi

        update_node(kimchi, node)
        kimchi_xml = etree.tostring(kimchi)
        # From libvirt doc, Passing None for @metadata says to remove that
        # element from the domain XML (passing the empty string leaves the
        # element present).  Do not support remove the old metadata.
        dom.setMetadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT, kimchi_xml,
                        KIMCHI_NAMESPACE, KIMCHI_META_URL,
                        flags=get_vm_config_flag(dom, mode))
    else:
        # FIXME remove this code when all distro libvirt supports metadata
        # element
        _kimchi_set_metadata_node(dom, node)


def _kimchi_get_metadata_node(dom, tag):
    # some other tools will not let libvirt create a persistent
    # configuration, just return empty
    if not dom.isPersistent():
        return None
    xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
    root = etree.fromstring(xml)
    kimchi = root.find("metadata/{%s}kimchi" % KIMCHI_META_URL)
    # remove the "kimchi" prefix of xml
    if kimchi is not None:
        for elem in kimchi.getiterator():
            if not hasattr(elem.tag, 'find'):
                continue
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i+1:]

        objectify.deannotate(kimchi)
        etree.cleanup_namespaces(kimchi)
        return kimchi
    return None


def get_metadata_node(dom, tag, metadata_support, mode="current"):
    if metadata_support:
        kimchi = libvirt_get_kimchi_metadata_node(dom, mode)
    else:
        # FIXME remove this code when all distro libvirt supports metadata
        # element
        kimchi = _kimchi_get_metadata_node(dom, tag)

    if kimchi is not None:
        node = kimchi.find(tag)
        if node is not None:
            return etree.tostring(node)
    return ""


def metadata_exists(dom):
    xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)
    root = etree.fromstring(xml)

    if root.find("metadata") is None:
        return False
    return True
