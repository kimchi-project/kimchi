#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.

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
        self.assertEquals(name, 'fedora-18')
        self.assertEquals(10, entry['disks'][0]['size'])
        self.assertEquals(cd, entry['cdrom'])
        self.assertEquals('/storagepools/default', entry['storagepool'])
