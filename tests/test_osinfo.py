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

import unittest


from kimchi.osinfo import _get_arch, get_template_default, lookup
from kimchi.osinfo import modern_version_bases


class OSInfoTests(unittest.TestCase):
    def test_default_lookup(self):
        entry = lookup(None, None)
        self.assertEquals('unknown', entry['os_distro'])
        self.assertEquals('unknown', entry['os_version'])
        self.assertEquals(['default'], entry['networks'])

    def test_old_distros(self):
        old_versions = {'debian': '5.0', 'ubuntu': '7.04', 'opensuse': '10.1',
                        'centos': '5.1', 'rhel': '5.1', 'fedora': '15'}
        for distro, version in old_versions.iteritems():
            entry = lookup(distro, version)
            self.assertEquals(entry['disk_bus'],
                              get_template_default('old', 'disk_bus'))
            self.assertEquals(entry['nic_model'],
                              get_template_default('old', 'nic_model'))

    def test_modern_bases(self):
        for distro, version in modern_version_bases[_get_arch()].iteritems():
            entry = lookup(distro, version)
            self.assertEquals(entry['disk_bus'],
                              get_template_default('modern', 'disk_bus'))
            self.assertEquals(entry['nic_model'],
                              get_template_default('modern', 'nic_model'))

    def test_modern_distros(self):
        # versions based on ppc64 modern distros
        modern_versions = {'ubuntu': '14.04', 'opensuse': '13.1',
                           'rhel': '6.5', 'fedora': '19', 'sles': '11sp3'}
        for distro, version in modern_versions.iteritems():
            entry = lookup(distro, version)
            self.assertEquals(entry['disk_bus'],
                              get_template_default('modern', 'disk_bus'))
            self.assertEquals(entry['nic_model'],
                              get_template_default('modern', 'nic_model'))

    def test_lookup_unknown_distro_version_returns_old_distro(self):
        distro = 'unknown_distro'
        version = 'unknown_version'
        entry = lookup(distro, version)
        self.assertEquals(entry['disk_bus'],
                          get_template_default('old', 'disk_bus'))
        self.assertEquals(entry['nic_model'],
                          get_template_default('old', 'nic_model'))
