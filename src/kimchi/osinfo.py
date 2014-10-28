#
# Project Kimchi
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import copy
import glob
import os


from distutils.version import LooseVersion


from kimchi.config import paths


SUPPORTED_ARCHS = {'x86': ('i386', 'i686', 'x86_64'),
                   'power': ('ppc', 'ppc64')}


common_spec = {'cpus': 1, 'memory': 1024, 'disks': [{'index': 0, 'size': 10}],
               'cdrom_bus': 'ide', 'cdrom_index': 2, 'mouse_bus': 'ps2'}


modern_spec = dict(common_spec, disk_bus='virtio', nic_model='virtio')


template_specs = {'x86': {'old': dict(common_spec, disk_bus='ide',
                                      nic_model='e1000', sound_model='ich6'),
                          'modern': dict(common_spec, disk_bus='virtio',
                                         nic_model='virtio',
                                         sound_model='ich6')},
                  'power': {'old': dict(common_spec, disk_bus='scsi',
                                        nic_model='spapr-vlan',
                                        cdrom_bus='scsi',
                                        kbd_bus='usb', mouse_bus='usb',
                                        tablet_bus='usb', memory=1280),
                            'modern': dict(common_spec, disk_bus='virtio',
                                           nic_model='virtio',
                                           cdrom_bus='scsi', kbd_bus='usb',
                                           mouse_bus='usb', tablet_bus='usb',
                                           memory=1280)}}


modern_version_bases = {'x86': {'debian': '6.0', 'ubuntu': '7.10',
                                'opensuse': '10.3', 'centos': '5.3',
                                'rhel': '6.0', 'fedora': '16', 'gentoo': '0',
                                'sles': '11'},
                        'power': {'rhel': '6.5', 'fedora': '19',
                                  'ubuntu': '14.04',
                                  'opensuse': '13.1',
                                  'sles': '11sp3'}}


icon_available_distros = [icon[5:-4] for icon in glob.glob1('%s/images/'
                          % paths.ui_dir, 'icon-*.png')]


defaults = {'networks': ['default'],
            'storagepool': '/storagepools/default',
            'domain': 'kvm', 'arch': os.uname()[4],
            'graphics': {'type': 'vnc', 'listen': '127.0.0.1'}}


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
    arch = _get_arch()

    if distro in modern_version_bases[arch]:
        if LooseVersion(version) >= LooseVersion(
                modern_version_bases[arch][distro]):
            params.update(template_specs[arch]['modern'])
        else:
            params.update(template_specs[arch]['old'])
    else:
        params['os_distro'] = params['os_version'] = "unknown"
        params.update(template_specs[arch]['old'])

    if distro in icon_available_distros:
        params['icon'] = 'images/icon-%s.png' % distro
    else:
        params['icon'] = 'images/icon-vm.png'

    return params
