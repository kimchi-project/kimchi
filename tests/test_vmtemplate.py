#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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
import uuid


from kimchi.vmtemplate import VMTemplate
from kimchi.xmlutils import xpath_get_text


class VMTemplateTests(unittest.TestCase):
    def test_minimal_construct(self):
        fields = (('name', 'test'), ('os_distro', 'unknown'),
                  ('os_version', 'unknown'), ('cpus', 1),
                  ('memory', 1024), ('cdrom', ''), ('networks', ['default']),
                  ('disk_bus', 'ide'), ('nic_model', 'e1000'),
                  ('graphics', {'type': 'vnc', 'listen': '127.0.0.1'}))

        args = {'name': 'test'}
        t = VMTemplate(args)
        for name, val in fields:
            self.assertEquals(val, t.info.get(name))

    def test_construct_overrides(self):
        graphics = {'type': 'spice', 'listen': '127.0.0.1'}
        args = {'name': 'test', 'disks': [{'size': 10}, {'size': 20}],
                'graphics': graphics}
        t = VMTemplate(args)
        self.assertEquals(2, len(t.info['disks']))
        self.assertEquals(graphics, t.info['graphics'])

    def test_specified_graphics(self):
        # Test specified listen
        graphics = {'type': 'vnc', 'listen': '127.0.0.1'}
        args = {'name': 'test', 'disks': [{'size': 10}, {'size': 20}],
                'graphics': graphics}
        t = VMTemplate(args)
        self.assertEquals(graphics, t.info['graphics'])

        # Test specified type
        graphics = {'type': 'spice', 'listen': '127.0.0.1'}
        args['graphics'] = graphics
        t = VMTemplate(args)
        self.assertEquals(graphics, t.info['graphics'])

        # If no listen specified, test the default listen
        graphics = {'type': 'vnc'}
        args['graphics'] = graphics
        t = VMTemplate(args)
        self.assertEquals(graphics['type'], t.info['graphics']['type'])
        self.assertEquals('127.0.0.1', t.info['graphics']['listen'])

    def test_to_xml(self):
        graphics = {'type': 'spice', 'listen': '127.0.0.1'}
        vm_uuid = str(uuid.uuid4()).replace('-', '')
        t = VMTemplate({'name': 'test-template'})
        xml = t.to_vm_xml('test-vm', vm_uuid, graphics=graphics)
        self.assertEquals(vm_uuid, xpath_get_text(xml, "/domain/uuid")[0])
        self.assertEquals('test-vm', xpath_get_text(xml, "/domain/name")[0])
        expr = "/domain/devices/graphics/@type"
        self.assertEquals(graphics['type'], xpath_get_text(xml, expr)[0])
        expr = "/domain/devices/graphics/@listen"
        self.assertEquals(graphics['listen'], xpath_get_text(xml, expr)[0])

    def test_arg_merging(self):
        """
        Make sure that default parameters from osinfo do not override user-
        provided parameters.
        """
        graphics = {'type': 'vnc', 'listen': '127.0.0.1'}
        args = {'name': 'test', 'os_distro': 'opensuse', 'os_version': '12.3',
                'cpus': 2, 'memory': 2048, 'networks': ['foo'],
                'cdrom': '/cd.iso', 'graphics': graphics}
        t = VMTemplate(args)
        self.assertEquals(2, t.info.get('cpus'))
        self.assertEquals(2048, t.info.get('memory'))
        self.assertEquals(['foo'], t.info.get('networks'))
        self.assertEquals('/cd.iso', t.info.get('cdrom'))
        self.assertEquals(graphics, t.info.get('graphics'))
