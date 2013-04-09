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

from burnet.vmtemplate import *
from burnet.xmlutils import xpath_get_text

class VMTemplateTests(unittest.TestCase):
    def test_minimal_construct(self):
        fields = (('name', 'test'), ('os_distro', 'unknown'),
                  ('os_version', 'unknown'), ('cpus', 1),
                  ('memory', 1024), ('cdrom', ''),
                  ('disk_bus', 'ide'), ('nic_model', 'ne2k_pci'))

        args = {'name': 'test'}
        t = VMTemplate(args)
        for name, val in fields:
            self.assertEquals(val, t.info.get(name))

    def test_construct_overrides(self):
        args = {'name': 'test', 'disks': [{'size': 10}, {'size': 20}]}
        t = VMTemplate(args)
        self.assertEquals(2, len(t.info['disks']))

    def test_to_xml(self):
        t = VMTemplate({'name': 'test-template'})
        xml = t.to_vm_xml('test-vm', '/tmp')
        self.assertEquals('test-vm', xpath_get_text(xml, "/domain/name")[0])
        expr = "/domain/devices/disk[@device='disk']/source/@file"
        self.assertEquals('/tmp/test-vm-0.img', xpath_get_text(xml, expr)[0])
        expr = "/domain/devices/disk[@device='disk']/target/@dev"
        self.assertEquals('hda', xpath_get_text(xml, expr)[0])
