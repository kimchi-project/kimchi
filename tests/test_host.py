# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2017
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
import json
import unittest
from functools import partial

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server


test_server = None


def setUpModule():
    global test_server

    patch_auth()
    test_server = run_server(test_mode=True)


def tearDownModule():
    test_server.stop()


class HostTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request)

    def test_host_devices(self):
        def asset_devices_type(devices, dev_type):
            for dev in devices:
                self.assertEqual(dev['device_type'], dev_type)

        resp = self.request('/plugins/kimchi/host/devices?_cap=scsi_host')
        nodedevs = json.loads(resp.read())
        # Mockmodel brings 3 preconfigured scsi fc_host
        self.assertEqual(3, len(nodedevs))

        nodedev = json.loads(
            self.request('/plugins/kimchi/host/devices/scsi_host2').read()
        )
        # Mockmodel generates random wwpn and wwnn
        self.assertEqual('scsi_host2', nodedev['name'])
        self.assertEqual('fc_host', nodedev['adapter']['type'])
        self.assertEqual(16, len(nodedev['adapter']['wwpn']))
        self.assertEqual(16, len(nodedev['adapter']['wwnn']))

        devs = json.loads(self.request('/plugins/kimchi/host/devices').read())
        dev_names = [dev['name'] for dev in devs]
        for dev_type in ('pci', 'usb_device', 'scsi'):
            resp = self.request(
                '/plugins/kimchi/host/devices?_cap=%s' % dev_type)
            devsByType = json.loads(resp.read())
            names = [dev['name'] for dev in devsByType]
            self.assertTrue(set(names) <= set(dev_names))
            asset_devices_type(devsByType, dev_type)

        resp = self.request('/plugins/kimchi/host/devices?_passthrough=true')
        passthru_devs = [dev['name'] for dev in json.loads(resp.read())]
        self.assertTrue(set(passthru_devs) <= set(dev_names))

        for dev_type in ('pci', 'usb_device', 'scsi'):
            resp = self.request(
                '/plugins/kimchi/host/devices?_cap=%s&_passthrough=true' % dev_type
            )
            filteredDevs = json.loads(resp.read())
            filteredNames = [dev['name'] for dev in filteredDevs]
            self.assertTrue(set(filteredNames) <= set(dev_names))
            asset_devices_type(filteredDevs, dev_type)

        for dev in passthru_devs:
            resp = self.request(
                '/plugins/kimchi/host/devices?_passthrough_affected_by=%s' % dev
            )
            affected_devs = [dev['name'] for dev in json.loads(resp.read())]
            self.assertTrue(set(affected_devs) <= set(dev_names))

    def test_get_available_passthrough_devices(self):
        resp = self.request('/plugins/kimchi/host/devices?_passthrough=true')
        all_devs = [dev['name'] for dev in json.loads(resp.read())]

        resp = self.request(
            '/plugins/kimchi/host/devices?' '_passthrough=true&_available_only=true'
        )
        available_devs = [dev['name'] for dev in json.loads(resp.read())]

        self.assertLessEqual(len(available_devs), len(all_devs))

    def test_host_partitions(self):
        resp = self.request('/plugins/kimchi/host/partitions')
        self.assertEqual(200, resp.status)
        partitions = json.loads(resp.read())

        keys = ['name', 'path', 'type', 'fstype',
                'size', 'mountpoint', 'available']
        for item in partitions:
            resp = self.request(
                '/plugins/kimchi/host/partitions/%s' % item['name'])
            info = json.loads(resp.read())
            self.assertEqual(sorted(info.keys()), sorted(keys))
