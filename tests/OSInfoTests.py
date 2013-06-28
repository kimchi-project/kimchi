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

import unittest
from burnet.osinfo import *

class OSInfoTests(unittest.TestCase):
    def test_default_lookup(self):
        name, entry = lookup(None, None)
        self.assertEquals(name, 'unknown')
        self.assertEquals('unknown', entry['os_distro'])
        self.assertEquals('unknown', entry['os_version'])
        self.assertEquals('default', entry['network'])

    def test_fedora_lookup(self):
        cd = 'http://fedora.mirrors.tds.net/pub/fedora/releases/17/Live/x86_64/Fedora-17-x86_64-Live-Desktop.iso'
        name, entry = lookup('fedora', '17')
        self.assertEquals(name, 'fedora')
        self.assertEquals(10, entry['disks'][0]['size'])
        self.assertEquals(cd, entry['cdrom'])
        self.assertEquals('/storagepools/default', entry['storagepool'])
