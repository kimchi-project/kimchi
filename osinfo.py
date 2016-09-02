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

import copy
import glob
import os
import psutil
from collections import defaultdict
from configobj import ConfigObj
from distutils.version import LooseVersion

from wok.config import PluginPaths
from wok.plugins.kimchi.config import kimchiPaths


SUPPORTED_ARCHS = {'x86': ('i386', 'i686', 'x86_64'),
                   'power': ('ppc', 'ppc64'),
                   'ppc64le': ('ppc64le'),
                   's390x': ('s390x')}


# Memory devices slot limits by architecture
MEM_DEV_SLOTS = {'ppc64': 256,
                 'ppc64le': 256,
                 'x86_64': 256,
                 'i686': 256,
                 'i386': 256,
                 's390x': 256}


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
                                        tablet_bus='usb'),
                            'modern': dict(disk_bus='virtio',
                                           nic_model='virtio',
                                           cdrom_bus='scsi',
                                           kbd_bus='usb',
                                           kbd_type="kbd",
                                           mouse_bus='usb', tablet_bus='usb')},
                  'ppc64le': {'old': dict(disk_bus='virtio',
                                          nic_model='virtio',
                                          cdrom_bus='scsi',
                                          kbd_bus='usb',
                                          kbd_type="keyboard",
                                          mouse_bus='usb', tablet_bus='usb'),
                              'modern': dict(disk_bus='virtio',
                                             nic_model='virtio',
                                             cdrom_bus='scsi',
                                             kbd_bus='usb',
                                             kbd_type="keyboard",
                                             mouse_bus='usb',
                                             tablet_bus='usb')},
                  's390x': {'old': dict(disk_bus='virtio',
                                        nic_model='virtio', cdrom_bus='scsi'),
                            'modern': dict(disk_bus='virtio',
                                           nic_model='virtio',
                                           cdrom_bus='scsi')}}


custom_specs = {'fedora': {'22': {'x86': dict(video_model='qxl')}},
                'windows': {'xp': {'x86': dict(nic_model='pcnet')}}}


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
                          % PluginPaths('kimchi').ui_dir, 'icon-*.png')]


def _get_arch():
    for arch, sub_archs in SUPPORTED_ARCHS.iteritems():
        if os.uname()[4] in sub_archs:
            return arch


def _get_default_template_mem():
    if hasattr(psutil, 'virtual_memory'):
        mem = psutil.virtual_memory().total >> 10 >> 10
    else:
        mem = psutil.TOTAL_PHYMEM >> 10 >> 10
    if _get_arch() == 'x86':
        return 1024 if mem > 1024 else mem
    else:
        # In PPC some guests does not boot with less than 2G of memory. However
        # we can do nothing if host has less than that amount.
        return 2048 if mem > 2048 else mem


def _get_tmpl_defaults():
    """
    ConfigObj returns a dict like below when no changes were made in the
    template configuration file (template.conf)

    {'main': {}, 'memory': {}, 'storage': {'disk.0': {}}, 'processor': {},
     'graphics': {}}

    The default values should be like below:

    {'main': {'networks': ['default']},
     'memory': {'current': 1024, 'maxmemory': 1024},
     'storage': { 'disk.0': {'format': 'qcow2', 'size': '10',
                             'pool': '/plugins/kimchi/storagepools/default'}},
     'processor': {'vcpus': '1',  'maxvcpus': 1},
     'graphics': {'type': 'spice', 'listen': '127.0.0.1'}}

    The default values on s390x architecture:

    {'memory': {'current': 1024, 'maxmemory': 1024},
     'storage': { 'disk.0': {'format': 'qcow2', 'size': '10',
                             'pool': '/plugins/kimchi/storagepools/default'}},
     'processor': {'vcpus': '1',  'maxvcpus': 1},
     'graphics': {'type': 'spice', 'listen': '127.0.0.1'}}
    """
    # Create dict with default values
    tmpl_defaults = defaultdict(dict)

    host_arch = _get_arch()
    tmpl_defaults['main']['networks'] = ['default']
    if host_arch in ['s390x', 's390']:
        tmpl_defaults['main']['networks'] = []

    tmpl_defaults['memory'] = {'current': _get_default_template_mem(),
                               'maxmemory': _get_default_template_mem()}
    tmpl_defaults['storage']['disk.0'] = {'size': 10, 'format': 'qcow2',
                                          'pool': 'default'}
    tmpl_defaults['processor']['vcpus'] = 1
    tmpl_defaults['processor']['maxvcpus'] = 1
    tmpl_defaults['graphics'] = {'type': 'vnc', 'listen': '127.0.0.1'}

    default_config = ConfigObj(tmpl_defaults)

    # Load template configuration file
    config_file = os.path.join(kimchiPaths.sysconf_dir, 'template.conf')
    config = ConfigObj(config_file)

    # Merge default configuration with file configuration
    default_config.merge(config)

    # Create a dict with default values according to data structure
    # expected by VMTemplate
    defaults = {'domain': 'kvm', 'arch': os.uname()[4],
                'cdrom_bus': 'ide', 'cdrom_index': 2, 'mouse_bus': 'ps2'}

    # Parse main section to get networks and memory values
    defaults.update(default_config.pop('main'))
    defaults['memory'] = default_config.pop('memory')

    defaults['memory']['current'] = int(defaults['memory']['current'])
    defaults['memory']['maxmemory'] = int(defaults['memory']['maxmemory'])

    # Parse storage section to get disks values
    storage_section = default_config.pop('storage')
    defaults['disks'] = []
    for disk in storage_section.keys():
        data = storage_section[disk]
        data['index'] = int(disk.split('.')[1])
        data['pool'] = {"name": '/plugins/kimchi/storagepools/' +
                        storage_section[disk].pop('pool')}
        defaults['disks'].append(data)

    # Parse processor section to get vcpus and cpu_topology values
    processor_section = default_config.pop('processor')
    defaults['cpu_info'] = {'vcpus': processor_section.pop('vcpus'),
                            'maxvcpus': processor_section.pop('maxvcpus')}
    if len(processor_section.keys()) > 0:
        defaults['cpu_info']['topology'] = processor_section

    # Update defaults values with graphics values
    defaults['graphics'] = default_config.pop('graphics')

    # Setting default memory device slots
    defaults['mem_dev_slots'] = MEM_DEV_SLOTS.get(os.uname()[4], 256)

    return defaults


# Set defaults values according to template.conf file
defaults = _get_tmpl_defaults()


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

    # set up arch to ppc64 instead of ppc64le due to libvirt compatibility
    if params["arch"] == "ppc64le":
        params["arch"] = "ppc64"
    # On s390x, template spec does not change based on version.
    if params["arch"] == "s390x":
        params.update(template_specs[arch]['old'])
    elif distro in modern_version_bases[arch]:
        if LooseVersion(version) >= LooseVersion(
                modern_version_bases[arch][distro]):
            params.update(template_specs[arch]['modern'])
        else:
            params.update(template_specs[arch]['old'])
    else:
        params['os_distro'] = params['os_version'] = "unknown"
        params.update(template_specs[arch]['old'])

    # Get custom specifications
    specs = custom_specs.get(distro, {})
    for v, config in specs.iteritems():
        if LooseVersion(version) >= LooseVersion(v):
            params.update(config.get(arch, {}))

    if distro in icon_available_distros:
        params['icon'] = 'plugins/kimchi/images/icon-%s.png' % distro
    else:
        params['icon'] = 'plugins/kimchi/images/icon-vm.png'

    return params
