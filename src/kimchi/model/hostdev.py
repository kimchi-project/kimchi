#
# Kimchi
#
# Copyright IBM, Corp. 2014
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

import os
from pprint import pformat
from pprint import pprint

from kimchi.model.libvirtconnection import LibvirtConnection
from kimchi.utils import kimchi_log
from kimchi.xmlutils.utils import dictize


def _get_all_host_dev_infos(libvirt_conn):
    node_devs = libvirt_conn.listAllDevices(0)
    return [get_dev_info(node_dev) for node_dev in node_devs]


def _get_dev_info_tree(dev_infos):
    devs = dict([(dev_info['name'], dev_info) for dev_info in dev_infos])
    root = None
    for dev_info in dev_infos:
        if dev_info['parent'] is None:
            root = dev_info
            continue

        try:
            parent = devs[dev_info['parent']]
        except KeyError:
            kimchi_log.error('Parent %s of device %s does not exist.',
                             dev_info['parent'], dev_info['name'])
            continue

        try:
            children = parent['children']
        except KeyError:
            parent['children'] = [dev_info]
        else:
            children.append(dev_info)
    return root


def _is_pci_qualified(pci_dev):
    # PCI bridge is not suitable to passthrough
    # KVM does not support passthrough graphic card now
    blacklist_classes = (0x030000, 0x060000)

    with open(os.path.join(pci_dev['path'], 'class')) as f:
        pci_class = int(f.readline().strip(), 16)

    if pci_class & 0xff0000 in blacklist_classes:
        return False

    return True


def get_passthrough_dev_infos(libvirt_conn):
    ''' Get devices eligible to be passed through to VM. '''

    def is_eligible(dev):
        return dev['device_type'] in ('usb_device', 'scsi') or \
            (dev['device_type'] == 'pci' and _is_pci_qualified(dev))

    dev_infos = _get_all_host_dev_infos(libvirt_conn)

    return [dev_info for dev_info in dev_infos if is_eligible(dev_info)]


def _get_same_iommugroup_devices(dev_infos, device_info):
    dev_dict = dict([(dev_info['name'], dev_info) for dev_info in dev_infos])

    def get_iommu_group(dev_info):
        # Find out the iommu group of a given device.
        # Child device belongs to the same iommu group as the parent device.
        try:
            return dev_info['iommuGroup']
        except KeyError:
            pass

        parent = dev_info['parent']
        while parent is not None:
            try:
                parent_info = dev_dict[parent]
            except KeyError:
                kimchi_log.error("Parent %s of device %s does not exist",
                                 parent, dev_info['name'])
                break

            try:
                iommuGroup = parent_info['iommuGroup']
            except KeyError:
                pass
            else:
                return iommuGroup

            parent = parent_info['parent']

        return None

    iommu_group = get_iommu_group(device_info)

    if iommu_group is None:
        return []

    return [dev_info for dev_info in dev_infos
            if dev_info['name'] != device_info['name'] and
            get_iommu_group(dev_info) == iommu_group]


def _get_children_devices(dev_infos, device_info):
    def get_children_recursive(parent):
        try:
            children = parent['children']
        except KeyError:
            return []

        result = []
        for child in children:
            result.append(child)
            result.extend(get_children_recursive(child))

        return result

    # Annotate every the dev_info element with children information
    _get_dev_info_tree(dev_infos)

    for dev_info in dev_infos:
        if dev_info['name'] == device_info['name']:
            return get_children_recursive(dev_info)

    return []


def get_affected_passthrough_devices(libvirt_conn, passthrough_dev):
    dev_infos = _get_all_host_dev_infos(libvirt_conn)

    group_devices = _get_same_iommugroup_devices(dev_infos, passthrough_dev)
    if not group_devices:
        # On host without iommu group support, the affected devices should
        # at least include all children devices
        group_devices.extend(_get_children_devices(dev_infos, passthrough_dev))

    return group_devices


def get_dev_info(node_dev):
    ''' Parse the node device XML string into dict according to
    http://libvirt.org/formatnode.html.

    scsi_generic is not documented in libvirt official website. Try to
    parse scsi_generic according to the following libvirt path series.
    https://www.redhat.com/archives/libvir-list/2013-June/msg00014.html

    scsi_target is not documented in libvirt official website. Try to
    parse scsi_target according to the libvirt commit db19834a0a.
    '''

    xmlstr = node_dev.XMLDesc(0)
    info = dictize(xmlstr)['device']
    dev_type = info['capability'].pop('type')
    info['device_type'] = dev_type
    cap_dict = info.pop('capability')
    info.update(cap_dict)
    info['parent'] = node_dev.parent()

    if dev_type in ('scsi', 'scsi_generic', 'scsi_target', 'system', 'usb'):
        return info

    if dev_type in ('net', 'pci', 'scsi_host', 'storage', 'usb_device'):
        return globals()['_get_%s_dev_info' % dev_type](info)

    kimchi_log.error("Unknown device type: %s", dev_type)
    return info


def _get_net_dev_info(info):
    cap = info.pop('capability')
    links = {"80203": "IEEE 802.3", "80211": "IEEE 802.11"}
    link_raw = cap['type']
    info['link_type'] = links.get(link_raw, link_raw)

    return info


def _get_pci_dev_info(info):
    for k in ('vendor', 'product'):
        try:
            description = info[k].pop('pyval')
        except KeyError:
            description = None
        info[k]['description'] = description
    if 'path' not in info:
        # Old libvirt does not provide syspath info
        info['path'] = \
            "/sys/bus/pci/devices/" \
            "%(domain)04x:%(bus)02x:%(slot)02x.%(function)01x" % {
                'domain': info['domain'], 'bus': info['bus'],
                'slot': info['slot'], 'function': info['function']}
    try:
        info['iommuGroup'] = int(info['iommuGroup']['number'])
    except KeyError:
        # Old libvirt does not provide syspath info, figure it out ourselves
        iommu_link = os.path.join(info['path'], 'iommu_group')
        if os.path.exists(iommu_link):
            iommu_path = os.path.realpath(iommu_link)
            try:
                info['iommuGroup'] = int(iommu_path.rsplit('/', 1)[1])
            except (ValueError, IndexError):
                # No IOMMU group support at all.
                pass
        else:
            # No IOMMU group support at all.
            pass
    return info


def _get_scsi_host_dev_info(info):
    try:
        cap_info = info.pop('capability')
    except KeyError:
        # kimchi.model.libvirtstoragepool.ScsiPoolDef assumes
        # info['adapter']['type'] always exists.
        info['adapter'] = {'type': ''}
        return info
    if isinstance(cap_info, list):
        info['adapter'] = {}
        for cap in cap_info:
            if cap['type'] == 'vport_ops':
                del cap['type']
                info['adapter']['vport_ops'] = cap
            else:
                info['adapter'].update(cap)
    else:
        info['adapter'] = cap_info
    return info


def _get_storage_dev_info(info):
    try:
        cap_info = info.pop('capability')
    except KeyError:
        return info

    if cap_info['type'] == 'removable':
        cap_info['available'] = bool(cap_info.pop('media_available'))
        if cap_info['available']:
            for k in ('size', 'label'):
                try:
                    cap_info[k] = cap_info.pop('media_' + k)
                except KeyError:
                    cap_info[k] = None
    info['media'] = cap_info
    return info


def _get_usb_device_dev_info(info):
    for k in ('vendor', 'product'):
        try:
            info[k]['description'] = info[k].pop('pyval')
        except KeyError:
            # Some USB devices don't provide vendor/product description.
            pass
    return info


# For test and debug
def _print_host_dev_tree(libvirt_conn):
    dev_infos = _get_all_host_dev_infos(libvirt_conn)
    root = _get_dev_info_tree(dev_infos)
    if root is None:
        print "No device found"
        return
    print '-----------------'
    print '\n'.join(_format_dev_node(root))


def _format_dev_node(node):
    try:
        children = node['children']
        del node['children']
    except KeyError:
        children = []

    lines = []
    lines.extend([' ~' + line for line in pformat(node).split('\n')])

    count = len(children)
    for i, child in enumerate(children):
        if count == 1:
            lines.append('   \-----------------')
        else:
            lines.append('   +-----------------')
        clines = _format_dev_node(child)
        if i == count - 1:
            p = '    '
        else:
            p = '   |'
        lines.extend([p + cline for cline in clines])
    lines.append('')

    return lines


if __name__ == '__main__':
    libvirt_conn = LibvirtConnection('qemu:///system').get()
    _print_host_dev_tree(libvirt_conn)
    print 'Eligible passthrough devices:'
    pprint(get_passthrough_dev_infos(libvirt_conn))
