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

from kimchi.model.model import Model
from kimchi.rollbackcontext import RollbackContext
from utils import get_free_port, patch_auth, request
from utils import run_server


model = None
test_server = None
host = None
port = None
ssl_port = None
cherrypy_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port, cherrypy_port

    patch_auth()
    model = Model(None, '/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


class StoragepoolTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)

    def test_get_storagepools(self):
        storagepools = json.loads(self.request('/storagepools').read())
        self.assertIn('default', [pool['name'] for pool in storagepools])

        with RollbackContext() as rollback:
            # Now add a couple of storage pools
            for i in xrange(3):
                name = u'kīмсhī-storagepool-%i' % i
                req = json.dumps({'name': name, 'type': 'dir',
                                  'path': '/var/lib/libvirt/images/%i' % i})
                resp = self.request('/storagepools', req, 'POST')
                rollback.prependDefer(model.storagepool_delete, name)

                self.assertEquals(201, resp.status)

                # Pool name must be unique
                req = json.dumps({'name': name, 'type': 'dir',
                                  'path': '/var/lib/libvirt/images/%i' % i})
                resp = self.request('/storagepools', req, 'POST')
                self.assertEquals(400, resp.status)

                # Verify pool information
                resp = self.request('/storagepools/%s' % name.encode("utf-8"))
                p = json.loads(resp.read())
                keys = [u'name', u'state', u'capacity', u'allocated',
                        u'available', u'path', u'source', u'type',
                        u'nr_volumes', u'autostart', u'persistent']
                self.assertEquals(sorted(keys), sorted(p.keys()))
                self.assertEquals(name, p['name'])
                self.assertEquals('inactive', p['state'])
                self.assertEquals(True, p['persistent'])
                self.assertEquals(True, p['autostart'])
                self.assertEquals(0, p['nr_volumes'])

            pools = json.loads(self.request('/storagepools').read())
            self.assertEquals(len(storagepools) + 3, len(pools))

            # Create a pool with an existing path
            tmp_path = tempfile.mkdtemp(dir='/var/lib/kimchi')
            rollback.prependDefer(os.rmdir, tmp_path)
            req = json.dumps({'name': 'existing_path', 'type': 'dir',
                              'path': tmp_path})
            resp = self.request('/storagepools', req, 'POST')
            rollback.prependDefer(model.storagepool_delete, 'existing_path')
            self.assertEquals(201, resp.status)

            # Reserved pool return 400
            req = json.dumps({'name': 'kimchi_isos', 'type': 'dir',
                              'path': '/var/lib/libvirt/images/%i' % i})
            resp = request(host, ssl_port, '/storagepools', req, 'POST')
            self.assertEquals(400, resp.status)
