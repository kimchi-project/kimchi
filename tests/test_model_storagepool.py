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
import os
import shutil
import tempfile
import unittest
import urllib
from functools import partial

import cherrypy
import mock
from wok.rollbackcontext import RollbackContext

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server

model = None
objectstore_loc = tempfile.mktemp()
test_server = None


@mock.patch('wok.plugins.kimchi.config.get_object_store')
def setUpModule(func):
    func.return_value = objectstore_loc
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=False)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model


def tearDownModule():
    test_server.stop()
    os.unlink(objectstore_loc)


class StoragepoolTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request)

    def test_get_storagepools(self):
        storagepools = json.loads(self.request(
            '/plugins/kimchi/storagepools').read())
        self.assertIn('default', [pool['name'] for pool in storagepools])

        with RollbackContext() as rollback:
            # Now add a couple of storage pools
            for i in range(3):
                name = f'kīмсhī-storagepool-{i}'
                path = f'/var/lib/libvirt/images/{i}'
                req = json.dumps({'name': name, 'type': 'dir', 'path': path})
                resp = self.request(
                    '/plugins/kimchi/storagepools', req, 'POST')
                rollback.prependDefer(model.storagepool_delete, name)
                rollback.prependDefer(shutil.rmtree, path)

                self.assertEqual(201, resp.status)

                # Pool name must be unique
                req = json.dumps(
                    {
                        'name': name,
                        'type': 'dir',
                        'path': f'/var/lib/libvirt/images/{i}',
                    }
                )
                resp = self.request(
                    '/plugins/kimchi/storagepools', req, 'POST')
                self.assertEqual(400, resp.status)

                # Verify pool information
                quote_uri = urllib.parse.quote(
                    f'/plugins/kimchi/storagepools/{name}')
                resp = self.request(quote_uri)
                p = json.loads(resp.read())
                keys = [
                    'name',
                    'state',
                    'capacity',
                    'allocated',
                    'available',
                    'path',
                    'source',
                    'type',
                    'nr_volumes',
                    'autostart',
                    'persistent',
                    'in_use',
                ]
                self.assertEqual(sorted(keys), sorted(p.keys()))
                self.assertEqual(name, p['name'])
                self.assertEqual('inactive', p['state'])
                self.assertEqual(True, p['persistent'])
                self.assertEqual(True, p['autostart'])
                self.assertEqual(0, p['nr_volumes'])

            pools = json.loads(self.request(
                '/plugins/kimchi/storagepools').read())
            self.assertEqual(len(storagepools) + 3, len(pools))

            # Create a pool with an existing path
            tmp_path = tempfile.mkdtemp(dir='/var/lib/kimchi')
            rollback.prependDefer(os.rmdir, tmp_path)
            req = json.dumps(
                {'name': 'existing_path', 'type': 'dir', 'path': tmp_path})
            resp = self.request('/plugins/kimchi/storagepools', req, 'POST')
            rollback.prependDefer(model.storagepool_delete, 'existing_path')
            self.assertEqual(201, resp.status)

            # Reserved pool return 400
            req = json.dumps(
                {
                    'name': 'kimchi_isos',
                    'type': 'dir',
                    'path': '/var/lib/libvirt/images/%i' % i,
                }
            )
            resp = request('/plugins/kimchi/storagepools', req, 'POST')
            self.assertEqual(400, resp.status)
