#
# Project Kimchi
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

import unittest


from kimchi.osinfo import lookup, modern_version_bases


class OSInfoTests(unittest.TestCase):
    def test_default_lookup(self):
        entry = lookup(None, None)
        self.assertEquals('unknown', entry['os_distro'])
        self.assertEquals('unknown', entry['os_version'])
        self.assertEquals(['default'], entry['networks'])

    def test_fedora_lookup(self):
        cd = 'http://fedora.mirrors.tds.net/pub/fedora/releases/17/Live/x86_64/Fedora-17-x86_64-Live-Desktop.iso'
        entry = lookup('fedora', '17')
        self.assertEquals(10, entry['disks'][0]['size'])
        self.assertEquals(cd, entry['cdrom'])
        self.assertEquals('/storagepools/default', entry['storagepool'])

    def test_old_distros(self):
        old_versions = {'debian': '5.0', 'ubuntu': '7.04', 'opensuse': '10.1',
                        'centos': '5.1', 'rhel': '5.1', 'fedora': '15'}
        for distro, version in old_versions.iteritems():
            entry = lookup(distro, version)
            self.assertEquals(entry['disk_bus'], 'ide')
            self.assertEquals(entry['nic_model'], 'e1000')

    def test_modern_bases(self):
        for distro, version in modern_version_bases.iteritems():
            entry = lookup(distro, version)
            self.assertEquals(entry['disk_bus'], 'virtio')
            self.assertEquals(entry['nic_model'], 'virtio')

    def test_modern_distros(self):
        modern_versions = {'debian': '7.0', 'ubuntu': '12.04',
                           'opensuse': '12.3', 'centos': '6.4', 'rhel': '6.3',
                           'fedora': '18', 'gentoo': '12.1'}
        for distro, version in modern_versions.iteritems():
            entry = lookup(distro, version)
            self.assertEquals(entry['disk_bus'], 'virtio')
            self.assertEquals(entry['nic_model'], 'virtio')
