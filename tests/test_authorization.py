#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
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
import unittest


from functools import partial


import kimchi.mockmodel
from utils import get_free_port, patch_auth, request
from utils import run_server


test_server = None
model = None
host = None
port = None
ssl_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port

    patch_auth(sudo = False)
    model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    test_server = run_server(host, port, ssl_port, test_mode=True, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)
        model.reset()

    def test_nonroot_access(self):
        # Non-root users can access static host information
        resp = self.request('/host', '{}', 'GET')
        self.assertEquals(403, resp.status)

        # Non-root users can access host stats
        resp = self.request('/host/stats', '{}', 'GET')
        self.assertEquals(403, resp.status)

        # Non-root users can not reboot/shutdown host system
        resp = self.request('/host/reboot', '{}', 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/host/shutdown', '{}', 'POST')
        self.assertEquals(403, resp.status)

        # Non-root users can not get or debug reports
        resp = self.request('/debugreports', '{}', 'GET')
        self.assertEquals(403, resp.status)
        resp = self.request('/debugreports', '{}', 'POST')
        self.assertEquals(403, resp.status)

        # Non-root users can not create or delete network (only get)
        resp = self.request('/networks', '{}', 'GET')
        self.assertEquals(200, resp.status)
        resp = self.request('/networks', '{}', 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/networks/default/activate', '{}', 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/networks/default', '{}', 'DELETE')
        self.assertEquals(403, resp.status)

        # Non-root users can not create or delete storage pool (only get)
        resp = self.request('/storagepools', '{}', 'GET')
        self.assertEquals(200, resp.status)
        resp = self.request('/storagepools', '{}', 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/storagepools/default/activate', '{}', 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/storagepools/default', '{}', 'DELETE')
        self.assertEquals(403, resp.status)

        # Non-root users can not update or delete a template
        # but he can get and create a new one
        resp = self.request('/templates', '{}', 'GET')
        self.assertEquals(403, resp.status)
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/templates/test', '{}', 'PUT')
        self.assertEquals(403, resp.status)
        resp = self.request('/templates/test', '{}', 'DELETE')
        self.assertEquals(403, resp.status)


        # Non-root users can only get vms authorized to them
        model.templates_create({'name': u'test', 'cdrom': '/nonexistent.iso'})

        model.vms_create({'name': u'test-me', 'template': '/templates/test'})
        model.vm_update(u'test-me', {'users': [ kimchi.mockmodel.fake_user.keys()[0] ], 'groups': []})

        model.vms_create({'name': u'test-usera', 'template': '/templates/test'})
        model.vm_update(u'test-usera', {'users': [ 'userA' ], 'groups': []})

        resp = self.request('/vms', '{}', 'GET')
        self.assertEquals(200, resp.status)
        vms_data = json.loads(resp.read())
        self.assertEquals([ u'test-me' ], [ v['name'] for v in vms_data ])
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(403, resp.status)

        # Create a vm using mockmodel directly to test Resource access
        model.vms_create({'name': 'test', 'template': '/templates/test'})

        resp = self.request('/vms/test', '{}', 'PUT')
        self.assertEquals(403, resp.status)
        resp = self.request('/vms/test', '{}', 'DELETE')
        self.assertEquals(403, resp.status)

        # Non-root users can only update VMs authorized by them
        resp = self.request('/vms/test-me/start', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/vms/test-usera/start', '{}', 'POST')
        self.assertEquals(403, resp.status)

        model.template_delete('test')
        model.vm_delete('test')
