#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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
import psutil

from collections import defaultdict
from configobj import ConfigObj
from distutils.version import LooseVersion

from kimchi.config import paths


SUPPORTED_ARCHS = {'x86': ('i386', 'i686', 'x86_64'),
                   'power': ('ppc', 'ppc64'),
                   'ppc64le': ('ppc64le')}


template_specs = {'x86': {'old': dict(disk_bus='ide',
                                      nic_model='e1000', sound_model='ich6'),
                          'modern': dict(disk_bus='virtio',
                                         nic_model='virtio',
                                         sound_model='ich6')},
                  'power': {'old': dict(disk_bus='scsi',
                                        nic_model='spapr-vlan',
                                        cdrom_bus='scsi',
                                        kbd_type="kbd",
                                        kbd_bus='usb', mouse_bus='usb',
                                        tablet_bus='usb', memory=1280),
                            'modern': dict(disk_bus='virtio',
                                           nic_model='virtio',
                                           cdrom_bus='scsi',
                                           kbd_bus='usb',
                                           kbd_type="kbd",
                                           mouse_bus='usb', tablet_bus='usb',
                                           memory=1280)},
                  'ppc64le': {'old': dict(disk_bus='virtio',
                                          nic_model='virtio',
                                          cdrom_bus='scsi',
                                          kbd_bus='usb',
                                          kbd_type="keyboard",
                                          mouse_bus='usb', tablet_bus='usb',
                                          memory=1280),
                              'modern': dict(disk_bus='virtio',
                                             nic_model='virtio',
                                             cdrom_bus='scsi',
                                             kbd_bus='usb',
                                             kbd_type="keyboard",
                                             mouse_bus='usb', tablet_bus='usb',
                                             memory=1280)}}


custom_specs = {'fedora': {'22': dict(video_model='qxl')}}


modern_version_bases = {'x86': {'debian': '6.0', 'ubuntu': '7.10',
                                'opensuse': '10.3', 'centos': '5.3',
                                'rhel': '6.0', 'fedora': '16', 'gentoo': '0',
                                'sles': '11', 'arch': '0'},
                        'power': {'rhel': '6.5', 'fedora': '19',
                                  'ubuntu': '14.04',
                                  'opensuse': '13.1',
                                  'sles': '11sp3'},
                        'ppc64le': {'rhel': '6.5', 'fedora': '19',
                                    'ubuntu': '14.04',
                                    'opensuse': '13.1',
                                    'sles': '11sp3'}}


icon_available_distros = [icon[5:-4] for icon in glob.glob1('%s/images/'
                          % paths.ui_dir, 'icon-*.png')]


def _get_tmpl_defaults():
    """
    ConfigObj returns a dict like below when no changes were made in the
    template configuration file (template.conf)

    {'main': {}, 'storage': {'disk.0': {}}, 'processor': {}, 'graphics': {}}

    The default values should be like below:

    {'main': {'networks': ['default'], 'memory': '1024'},
     'storage': {'pool': 'default',
                 'disk.0': {'format': 'qcow2', 'size': '10'}},
     'processor': {'cpus': '1'},
     'graphics': {'type': 'spice', 'listen': '127.0.0.1'}}
    """
    # Create dict with default values
    tmpl_defaults = defaultdict(dict)
    tmpl_defaults['main']['networks'] = ['default']
    tmpl_defaults['main']['memory'] = 1024
    tmpl_defaults['storage']['pool'] = 'default'
    tmpl_defaults['storage']['disk.0'] = {'size': 10, 'format': 'qcow2'}
    tmpl_defaults['processor']['cpus'] = 1
    tmpl_defaults['graphics'] = {'type': 'vnc', 'listen': '127.0.0.1'}

    default_config = ConfigObj(tmpl_defaults)

    # Load template configuration file
    config_file = os.path.join(paths.conf_dir, 'template.conf')
    config = ConfigObj(config_file)

    # Merge default configuration with file configuration
    default_config.merge(config)

    # Create a dict with default values according to data structure
    # expected by VMTemplate
    defaults = {'domain': 'kvm', 'arch': os.uname()[4],
                'cdrom_bus': 'ide', 'cdrom_index': 2, 'mouse_bus': 'ps2'}

    # Parse main section to get networks and memory values
    main_section = default_config.pop('main')
    defaults.update(main_section)

    # Parse storage section to get storage pool and disks values
    storage_section = default_config.pop('storage')
    defaults['storagepool'] = '/storagepools/' + storage_section.pop('pool')
    defaults['disks'] = []
    for disk in storage_section.keys():
        data = storage_section[disk]
        data['index'] = int(disk.split('.')[1])
        defaults['disks'].append(data)

    # Parse processor section to get cpus and cpu_topology values
    processor_section = default_config.pop('processor')
    defaults['cpus'] = processor_section.pop('cpus')
    defaults['cpu_info'] = {}
    if len(processor_section.keys()) > 0:
        defaults['cpu_info']['topology'] = processor_section

    # Update defaults values with graphics values
    defaults['graphics'] = default_config.pop('graphics')

    return defaults


# Set defaults values according to template.conf file
defaults = _get_tmpl_defaults()


def _get_arch():
    for arch, sub_archs in SUPPORTED_ARCHS.iteritems():
        if os.uname()[4] in sub_archs:
            return arch


def get_template_default(template_type, field):
    host_arch = _get_arch()
    # Assuming 'power' = 'ppc64le' because lookup() does the same,
    # claiming libvirt compatibility.
    host_arch = 'power' if host_arch == 'ppc64le' else host_arch
    tmpl_defaults = copy.deepcopy(defaults)
    tmpl_defaults.update(template_specs[host_arch][template_type])
    return tmpl_defaults[field]


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

    # Setting maxMemory of the VM, which will be equal total Host memory in Kib
    params['max_memory'] = psutil.TOTAL_PHYMEM >> 10

    # set up arch to ppc64 instead of ppc64le due to libvirt compatibility
    if params["arch"] == "ppc64le":
        params["arch"] = "ppc64"

    if distro in modern_version_bases[arch]:
        if LooseVersion(version) >= LooseVersion(
                modern_version_bases[arch][distro]):
            params.update(template_specs[arch]['modern'])
        else:
            params.update(template_specs[arch]['old'])
    else:
        params['os_distro'] = params['os_version'] = "unknown"
        params.update(template_specs[arch]['old'])

    # Get custom specifications
    params.update(custom_specs.get(distro, {}).get(version, {}))

    if distro in icon_available_distros:
        params['icon'] = 'images/icon-%s.png' % distro
    else:
        params['icon'] = 'images/icon-vm.png'

    return params
