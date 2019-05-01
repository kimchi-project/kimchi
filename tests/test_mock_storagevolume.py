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
import urllib
from functools import partial

import cherrypy
from test_model_storagevolume import _do_volume_test

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server


model = None
test_server = None


def setUpModule():
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=True)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model


def tearDownModule():
    test_server.stop()


class MockStorageVolumeTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request)

    def test_storagevolume(self):
        # MockModel always returns 2 partitions (vdx, vdz)
        partitions = json.loads(
            self.request(
                '/plugins/kimchi/host/partitions').read().decode('utf-8')
        )
        devs = [dev['path'] for dev in partitions]

        # MockModel always returns 3 FC devices
        fc_devs = json.loads(
            self.request('/plugins/kimchi/host/devices?_cap=fc_host')
            .read()
            .decode('utf-8')
        )
        fc_devs = [dev['name'] for dev in fc_devs]

        poolDefs = [
            {
                'type': 'dir',
                'name': 'kīмсhīUnitTestDirPool',
                'path': '/tmp/kimchi-images',
            },
            {
                'type': 'netfs',
                'name': 'kīмсhīUnitTestNSFPool',
                'source': {'host': 'localhost', 'path': '/var/lib/kimchi/nfs-pool'},
            },
            {
                'type': 'scsi',
                'name': 'kīмсhīUnitTestSCSIFCPool',
                'source': {'adapter_name': fc_devs[0]},
            },
            {
                'type': 'iscsi',
                'name': 'kīмсhīUnitTestISCSIPool',
                'source': {
                    'host': '127.0.0.1',
                    'target': 'iqn.2015-01.localhost.kimchiUnitTest',
                },
            },
            {
                'type': 'logical',
                'name': 'kīмсhīUnitTestLogicalPool',
                'source': {'devices': [devs[0]]},
            },
        ]

        for pool in poolDefs:
            pool_name = pool['name']
            uri = urllib.parse.quote(
                f'/plugins/kimchi/storagepools/{pool_name}')
            req = json.dumps(pool)
            resp = self.request('/plugins/kimchi/storagepools', req, 'POST')
            self.assertEqual(201, resp.status)
            # activate the storage pool
            resp = self.request(uri + '/activate', '{}', 'POST')
            self.assertEqual(200, resp.status)
            _do_volume_test(self, model, pool_name)
