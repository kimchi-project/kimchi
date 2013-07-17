#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
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

osinfo = [
    # Entries are searched in order and the first match will be returned
    ('debian', {
        'version': lambda d,v: bool(d == 'debian' and v in ('6.0', '7.0')),
        'icon': 'images/icon-debian.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'virtio', 'nic_model': 'virtio',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('debian-old', {
        'version': lambda d,v: bool(d == 'debian'),
        'icon': 'images/icon-debian.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'ide', 'nic_model': 'e1000',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('ubuntu', {
        'version': lambda d,v: bool(d == 'ubuntu' and v in
            ('7.10', '8.04', '8.10', '9.04', '9.10', '10.04', '10.10',
             '11.04', '11.10', '12.04', '12.10', '13.04', '13.10')),
        'icon': 'images/icon-ubuntu.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'virtio', 'nic_model': 'virtio',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('ubuntu-old', {
        'version': lambda d,v: bool(d == 'ubuntu'),
        'icon': 'images/icon-ubuntu.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'ide', 'nic_model': 'e1000',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('opensuse', {
        'version': lambda d,v: bool(d == 'opensuse' and v in
            ('10.3', '11.0', '11.1', '11.2', '11.3', '11.4', '12.1', '12.2',
             '12.3',)),
        'icon': 'images/icon-opensuse.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'virtio', 'nic_model': 'virtio',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('opensuse-old', {
        'version': lambda d,v: bool(d == 'opensuse'),
        'icon': 'images/icon-opensuse.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'ide', 'nic_model': 'e1000',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('fedora', {
        'version': lambda d,v: bool(d == 'fedora' and v in
            ('16', '17', '18', '19')),
        'icon': 'images/icon-fedora.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'virtio', 'nic_model': 'virtio',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('fedora-old', {
        'version': lambda d,v: bool(d == 'fedora'),
        'icon': 'images/icon-fedora.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'ide', 'nic_model': 'e1000',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('rhel', {
        'version': lambda d,v: bool(d == 'rhel' and
            v.startswith('6.')),
        'icon': 'images/icon-vm.svg',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'virtio', 'nic_model': 'virtio',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('rhel-old', {
        'version': lambda d,v: bool(d == 'rhel'),
        'icon': 'images/icon-vm.png',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'ide', 'nic_model': 'e1000',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
    ('unknown', {
        'version': lambda d,v: True,
        'icon': 'images/icon-vm.svg',
        'os_distro': 'unknown', 'os_version': 'unknown',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'cdrom': '',
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'ide', 'nic_model': 'e1000',
        'cdrom_bus': 'ide', 'cdrom_index': 2,
    }),
]

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

defaults = {'network': 'default', 'storagepool': '/storagepools/default',
        'domain': 'kvm', 'arch': os.uname()[4]
}

def lookup(distro, version):
    """
    Lookup all parameters needed to run a VM of a known or unknown operating
    system type and version.  The data is constructed by starting with the
    'defaults' and merging the parameters given for the identified OS.  If
    known, a link to a remote install CD is added.
    """
    for name, entry in osinfo:
        # Test if this entry is a valid match
        if entry['version'](distro, version):
            params = copy.copy(defaults)
            params['os_distro'] = distro
            params['os_version'] = version
            params.update(entry)
            params['cdrom'] = isolinks.get(distro, {}).get(version, '')
            del params['version']  # Don't pass around the version function
            return (name, params)
