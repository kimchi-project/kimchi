#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import copy
import os


from distutils.version import LooseVersion


SUPPORTED_ARCHS = {'x86': ('i386', 'x86_64'), 'power': ('ppc', 'ppc64')}


common_spec = {'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1, 'memory': 1024,
               'disks': [{'index': 0, 'size': 10}], 'cdrom_bus': 'ide',
               'cdrom_index': 2, 'mouse_bus': 'ps2'}


modern_spec = dict(common_spec, disk_bus='virtio', nic_model='virtio')


template_specs = {'x86': {'old': dict(common_spec, disk_bus='ide',
                                      nic_model='e1000', sound_model= 'ich6'),
                          'modern': dict(common_spec, disk_bus='virtio',
                                         nic_model='virtio',
                                         sound_model= 'ich6')},
                  'power': {'old': dict(common_spec, disk_bus='scsi',
                                        nic_model='spapr-vlan', cdrom_bus='scsi',
                                        kbd_bus='usb', mouse_bus='usb'),
                            'modern': dict(common_spec, disk_bus='virtio',
                                           nic_model='virtio',
                                           cdrom_bus='scsi', kbd_bus='usb',
                                           mouse_bus='usb')}}


modern_version_bases = {'x86': {'debian': '6.0', 'ubuntu': '7.10',
                                'opensuse': '10.3', 'centos': '5.3',
                                'rhel': '6.0', 'fedora': '16', 'gentoo': '0'},
                        'power': {'rhel': '7.0', 'fedora': '19'}}


isolinks = {
    'debian': {
        'squeeze': 'http://cdimage.debian.org/debian-cd/6.0.7-live/amd64/iso-hybrid/debian-live-6.0.7-amd64-gnome-desktop.iso',
    },
    'ubuntu': {
        'raring': 'http://ubuntu-releases.cs.umn.edu/13.04/ubuntu-13.04-desktop-amd64.iso',
    },
    'opensuse': {
        '12.3': 'http://suse.mirrors.tds.net/pub/opensuse/distribution/12.3/iso/openSUSE-12.3-DVD-x86_64.iso',
    },
    'fedora': {
        '16': 'http://fedora.mirrors.tds.net/pub/fedora/releases/16/Live/x86_64/Fedora-16-x86_64-Live-Desktop.iso',
        '17': 'http://fedora.mirrors.tds.net/pub/fedora/releases/17/Live/x86_64/Fedora-17-x86_64-Live-Desktop.iso',
        '18': 'http://fedora.mirrors.tds.net/pub/fedora/releases/18/Live/x86_64/Fedora-18-x86_64-Live-Desktop.iso',
    },
}

defaults = {'networks': ['default'],
            'storagepool': '/storagepools/default',
            'domain': 'kvm', 'arch': os.uname()[4],
            'graphics': {'type': 'vnc', 'listen': '0.0.0.0'}}



def _get_arch():
    for arch, sub_archs in SUPPORTED_ARCHS.iteritems():
        if os.uname()[4] in sub_archs:
            return arch


def lookup(distro, version):
    """
    Lookup all parameters needed to run a VM of a known or unknown operating
    system type and version.  The data is constructed by starting with the
    'defaults' and merging the parameters given for the identified OS.  If
    known, a link to a remote install CD is added.
    """
    params = copy.deepcopy(defaults)
    params['os_distro'] = distro
    params['os_version'] = version
    params['cdrom'] = isolinks.get(distro, {}).get(version, '')
    arch = _get_arch()

    if distro in modern_version_bases[arch]:
        params['icon'] = 'images/icon-%s.png' % distro
        if LooseVersion(version) >= LooseVersion(
            modern_version_bases[arch][distro]):
            params.update(template_specs[arch]['modern'])
        else:
            params.update(template_specs[arch]['old'])
    else:
        params['icon'] = 'images/icon-vm.png'
        params['os_distro'] = params['os_version'] = "unknown"
        params.update(template_specs[arch]['old'])

    return params
