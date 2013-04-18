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

