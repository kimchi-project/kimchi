#
# Project Kimchi
#
# Copyright IBM Corp, 2014-2017
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

import cherrypy
import mock
from iso_gen import construct_fake_iso

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server
from tests.utils import wait_task

test_server = None
model = None
fake_iso = '/tmp/fake.iso'


def setUpModule():
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=True)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model

    # Create fake ISO to do the tests
    construct_fake_iso(fake_iso, True, '12.04', 'ubuntu')


def tearDownModule():
    test_server.stop()
    os.unlink(fake_iso)


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, user='user')
        model.reset()

    @mock.patch('wok.plugins.kimchi.model.users.PAMUsersModel._validate')
    def test_nonroot_access(self, validate_users):
        validate_users.return_value = True

        # Non-root users can not create or delete network (only get)
        resp = self.request('/plugins/kimchi/networks', '{}', 'GET')
        self.assertEqual(200, resp.status)
        resp = self.request('/plugins/kimchi/networks', '{}', 'POST')
        self.assertEqual(403, resp.status)
        resp = self.request(
            '/plugins/kimchi/networks/default/activate', '{}', 'POST')
        self.assertEqual(403, resp.status)
        resp = self.request('/plugins/kimchi/networks/default', '{}', 'DELETE')
        self.assertEqual(403, resp.status)

        # Non-root users can not create or delete storage pool (only get)
        resp = self.request('/plugins/kimchi/storagepools', '{}', 'GET')
        self.assertEqual(200, resp.status)
        resp = self.request('/plugins/kimchi/storagepools', '{}', 'POST')
        self.assertEqual(403, resp.status)
        resp = self.request(
            '/plugins/kimchi/storagepools/default/activate', '{}', 'POST'
        )
        self.assertEqual(403, resp.status)
        resp = self.request(
            '/plugins/kimchi/storagepools/default', '{}', 'DELETE')
        self.assertEqual(403, resp.status)

        # Non-root users can not update or delete a template
        # but he can get and create a new one
        resp = self.request('/plugins/kimchi/templates', '{}', 'GET')
        self.assertEqual(403, resp.status)
        req = json.dumps({'name': 'test', 'source_media': fake_iso})
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(403, resp.status)
        resp = self.request('/plugins/kimchi/templates/test', '{}', 'PUT')
        self.assertEqual(403, resp.status)
        resp = self.request('/plugins/kimchi/templates/test', '{}', 'DELETE')
        self.assertEqual(403, resp.status)

        # Non-root users can only get vms authorized to them
        model.templates_create(
            {'name': u'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
        )

        task_info = model.vms_create(
            {'name': u'test-me', 'template': '/plugins/kimchi/templates/test'}
        )
        wait_task(model.task_lookup, task_info['id'])

        model.vm_update(u'test-me', {'users': ['user'], 'groups': []})

        task_info = model.vms_create(
            {'name': u'test-usera', 'template': '/plugins/kimchi/templates/test'}
        )
        wait_task(model.task_lookup, task_info['id'])

        non_root = list(set(model.users_get_list()) - set(['admin']))[0]
        model.vm_update(u'test-usera', {'users': [non_root], 'groups': []})

        task_info = model.vms_create(
            {'name': u'test-groupa', 'template': '/plugins/kimchi/templates/test'}
        )
        wait_task(model.task_lookup, task_info['id'])
        a_group = model.groups_get_list()[0]
        model.vm_update(u'test-groupa', {'groups': [a_group]})

        resp = self.request('/plugins/kimchi/vms', '{}', 'GET')
        self.assertEqual(200, resp.status)
        vms_data = json.loads(resp.read())
        self.assertEqual(
            [u'test-groupa', u'test-me'], sorted([v['name'] for v in vms_data])
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(403, resp.status)

        # Create a vm using mockmodel directly to test Resource access
        task_info = model.vms_create(
            {'name': 'kimchi-test', 'template': '/plugins/kimchi/templates/test'}
        )
        wait_task(model.task_lookup, task_info['id'])
        resp = self.request('/plugins/kimchi/vms/kimchi-test', '{}', 'PUT')
        self.assertEqual(403, resp.status)
        resp = self.request('/plugins/kimchi/vms/kimchi-test', '{}', 'DELETE')
        self.assertEqual(403, resp.status)

        # Non-root users can only update VMs authorized by them
        resp = self.request('/plugins/kimchi/vms/test-me/start', '{}', 'POST')
        self.assertEqual(200, resp.status)
        resp = self.request(
            '/plugins/kimchi/vms/test-usera/start', '{}', 'POST')
        self.assertEqual(403, resp.status)

        model.template_delete('test')
        model.vm_delete('test-me')
