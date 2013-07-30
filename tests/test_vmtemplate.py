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

from kimchi.vmtemplate import *
from kimchi.xmlutils import xpath_get_text

class VMTemplateTests(unittest.TestCase):
    def test_minimal_construct(self):
        fields = (('name', 'test'), ('os_distro', 'unknown'),
                  ('os_version', 'unknown'), ('cpus', 1),
                  ('memory', 1024), ('cdrom', ''), ('network', 'default'),
                  ('disk_bus', 'ide'), ('nic_model', 'e1000'))

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

    def test_arg_merging(self):
        """
        Make sure that default parameters from osinfo do not override user-
        provided parameters.
        """
        args = {'name': 'test', 'os_distro': 'opensuse', 'os_version': '12.3',
                'cpus': 2, 'memory': 2048, 'network': 'foo',
                'cdrom': '/cd.iso'}
        t = VMTemplate(args)
        self.assertEquals(2, t.info.get('cpus'))
        self.assertEquals(2048, t.info.get('memory'))
        self.assertEquals('foo', t.info.get('network'))
        self.assertEquals('/cd.iso', t.info.get('cdrom'))
