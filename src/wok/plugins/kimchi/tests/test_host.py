# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM, Corp. 2015
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
import os
import tempfile
import unittest
from functools import partial

from wok.plugins.kimchi.mockmodel import MockModel

from utils import get_free_port, patch_auth, request, run_server


test_server = None
model = None
host = None
ssl_port = None
tmpfile = None


def setUpModule():
    global test_server, model, host, ssl_port, tmpfile

    patch_auth()
    tmpfile = tempfile.mktemp()
    model = MockModel(tmpfile)
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink(tmpfile)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)

    def test_host_devices(self):
        def asset_devices_type(devices, dev_type):
            for dev in devices:
                self.assertEquals(dev['device_type'], dev_type)

        resp = self.request('/plugins/kimchi/host/devices?_cap=scsi_host')
        nodedevs = json.loads(resp.read())
        # Mockmodel brings 3 preconfigured scsi fc_host
        self.assertEquals(3, len(nodedevs))

        nodedev = json.loads(
            self.request('/plugins/kimchi/host/devices/scsi_host2').read()
        )
        # Mockmodel generates random wwpn and wwnn
        self.assertEquals('scsi_host2', nodedev['name'])
        self.assertEquals('fc_host', nodedev['adapter']['type'])
        self.assertEquals(16, len(nodedev['adapter']['wwpn']))
        self.assertEquals(16, len(nodedev['adapter']['wwnn']))

        devs = json.loads(self.request('/plugins/kimchi/host/devices').read())
        dev_names = [dev['name'] for dev in devs]
        for dev_type in ('pci', 'usb_device', 'scsi'):
            resp = self.request('/plugins/kimchi/host/devices?_cap=%s' %
                                dev_type)
            devsByType = json.loads(resp.read())
            names = [dev['name'] for dev in devsByType]
            self.assertTrue(set(names) <= set(dev_names))
            asset_devices_type(devsByType, dev_type)

        resp = self.request('/plugins/kimchi/host/devices?_passthrough=true')
        passthru_devs = [dev['name'] for dev in json.loads(resp.read())]
        self.assertTrue(set(passthru_devs) <= set(dev_names))

        for dev_type in ('pci', 'usb_device', 'scsi'):
            resp = self.request(
                '/plugins/kimchi/host/devices?_cap=%s&_passthrough=true' %
                dev_type
            )
            filteredDevs = json.loads(resp.read())
            filteredNames = [dev['name'] for dev in filteredDevs]
            self.assertTrue(set(filteredNames) <= set(dev_names))
            asset_devices_type(filteredDevs, dev_type)

        for dev in passthru_devs:
            resp = self.request(
                '/plugins/kimchi/host/devices?_passthrough_affected_by=%s' %
                dev
            )
            affected_devs = [dev['name'] for dev in json.loads(resp.read())]
            self.assertTrue(set(affected_devs) <= set(dev_names))

    def test_get_available_passthrough_devices(self):
        resp = self.request('/plugins/kimchi/host/devices?_passthrough=true')
        all_devs = [dev['name'] for dev in json.loads(resp.read())]

        resp = self.request('/plugins/kimchi/host/devices?'
                            '_passthrough=true&_available_only=true')
        available_devs = [dev['name'] for dev in json.loads(resp.read())]

        self.assertLessEqual(len(available_devs), len(all_devs))
