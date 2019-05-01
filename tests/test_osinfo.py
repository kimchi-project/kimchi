#
# Project Kimchi
#
# Copyright IBM Corp, 2013-2016
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
import unittest

from wok.plugins.kimchi.osinfo import _get_arch
from wok.plugins.kimchi.osinfo import get_template_default
from wok.plugins.kimchi.osinfo import lookup
from wok.plugins.kimchi.osinfo import modern_version_bases


class OSInfoTests(unittest.TestCase):
    def test_default_lookup(self):
        entry = lookup(None, None)
        self.assertEqual('unknown', entry['os_distro'])
        self.assertEqual('unknown', entry['os_version'])
        if not os.uname()[4] == 's390x':
            self.assertEqual(['default'], entry['networks'])

    def test_old_distros(self):
        old_versions = {
            'debian': '5.0',
            'ubuntu': '7.04',
            'opensuse': '10.1',
            'centos': '5.1',
            'rhel': '5.1',
            'fedora': '15',
        }
        for distro, version in old_versions.items():
            entry = lookup(distro, version)
            self.assertEqual(entry['disk_bus'],
                             get_template_default('old', 'disk_bus'))
            self.assertEqual(
                entry['nic_model'], get_template_default('old', 'nic_model')
            )

    def test_modern_bases(self):
        if not os.uname()[4] == 's390x':
            for distro, version in modern_version_bases[_get_arch()].items():
                entry = lookup(distro, version)
                self.assertEqual(
                    entry['disk_bus'], get_template_default(
                        'modern', 'disk_bus')
                )
                self.assertEqual(
                    entry['nic_model'], get_template_default(
                        'modern', 'nic_model')
                )

    def test_modern_distros(self):
        # versions based on ppc64 modern distros
        modern_versions = {
            'ubuntu': '14.04',
            'opensuse': '13.1',
            'rhel': '6.5',
            'fedora': '19',
            'sles': '11sp3',
        }
        for distro, version in modern_versions.items():
            entry = lookup(distro, version)
            self.assertEqual(
                entry['disk_bus'], get_template_default('modern', 'disk_bus')
            )
            self.assertEqual(
                entry['nic_model'], get_template_default('modern', 'nic_model')
            )

    def test_lookup_unknown_distro_version_returns_old_distro(self):
        distro = 'unknown_distro'
        version = 'unknown_version'
        entry = lookup(distro, version)
        self.assertEqual(entry['disk_bus'],
                         get_template_default('old', 'disk_bus'))
        self.assertEqual(entry['nic_model'],
                         get_template_default('old', 'nic_model'))
