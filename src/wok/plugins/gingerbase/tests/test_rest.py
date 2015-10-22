# -*- coding: utf-8 -*-
#
# Project Ginger Base
#
# Copyright IBM, Corp. 2013-2015
#
# Code derived from Project Kimchi
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
import time
import unittest
from functools import partial

from wok.rollbackcontext import RollbackContext

from wok.plugins.gingerbase import mockmodel

from utils import get_free_port, patch_auth, request
from utils import run_server, wait_task


test_server = None
model = None
host = None
port = None
ssl_port = None
cherrypy_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port, cherrypy_port

    patch_auth()
    model = mockmodel.MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


class RestTests(unittest.TestCase):
    def _async_op(self, cb, opaque):
        time.sleep(1)
        cb('success', True)

    def _except_op(self, cb, opaque):
        time.sleep(1)
        raise Exception("Oops, this is an exception handle test."
                        " You can ignore it safely")
        cb('success', True)

    def _intermid_op(self, cb, opaque):
        time.sleep(1)
        cb('in progress')

    def setUp(self):
        self.request = partial(request, host, ssl_port)
        model.reset()

    def _task_lookup(self, taskid):
        return json.loads(
            self.request('/tasks/%s' % taskid).read()
        )

    def assertHTTPStatus(self, code, *args):
        resp = self.request(*args)
        self.assertEquals(code, resp.status)

    def test_debugreports(self):
        resp = request(host, ssl_port, '/plugins/gingerbase/debugreports')
        self.assertEquals(200, resp.status)

    def _report_delete(self, name):
        request(host, ssl_port, '/plugins/gingerbase/debugreports/%s' % name,
                '{}', 'DELETE')

    def test_create_debugreport(self):
        req = json.dumps({'name': 'report1'})
        with RollbackContext() as rollback:
            resp = request(host, ssl_port, '/plugins/gingerbase/debugreports',
                           req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            wait_task(self._task_lookup, task['id'])
            rollback.prependDefer(self._report_delete, 'report2')
            resp = request(host, ssl_port,
                           '/plugins/gingerbase/debugreports/report1')
            debugreport = json.loads(resp.read())
            self.assertEquals("report1", debugreport['name'])
            self.assertEquals(200, resp.status)
            req = json.dumps({'name': 'report2'})
            resp = request(host, ssl_port,
                           '/plugins/gingerbase/debugreports/report1',
                           req, 'PUT')
            self.assertEquals(303, resp.status)

    def test_debugreport_download(self):
        req = json.dumps({'name': 'report1'})
        with RollbackContext() as rollback:
            resp = request(host, ssl_port, '/plugins/gingerbase/debugreports',
                           req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            wait_task(self._task_lookup, task['id'], 20)
            rollback.prependDefer(self._report_delete, 'report1')
            resp = request(host, ssl_port,
                           '/plugins/gingerbase/debugreports/report1')
            debugreport = json.loads(resp.read())
            self.assertEquals("report1", debugreport['name'])
            self.assertEquals(200, resp.status)
            resp = request(host, ssl_port,
                           '/plugins/gingerbase/debugreports/report1/content')
            self.assertEquals(200, resp.status)
            resp = request(host, ssl_port,
                           '/plugins/gingerbase/debugreports/report1')
            debugre = json.loads(resp.read())
            resp = request(host, ssl_port, '/' + debugre['uri'])
            self.assertEquals(200, resp.status)

    def test_repositories(self):
        def verify_repo(t, res):
            for field in ('repo_id', 'enabled', 'baseurl', 'config'):
                if field in t.keys():
                    self.assertEquals(t[field], res[field])

        base_uri = '/plugins/gingerbase/host/repositories'
        resp = self.request(base_uri)
        self.assertEquals(200, resp.status)
        # Already have one repo in Kimchi's system
        self.assertEquals(1, len(json.loads(resp.read())))

        # Create a repository
        repo = {'repo_id': 'fedora-fake',
                'baseurl': 'http://www.fedora.org'}
        req = json.dumps(repo)
        resp = self.request(base_uri, req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the repository
        res = json.loads(self.request('%s/fedora-fake' % base_uri).read())
        verify_repo(repo, res)

        # Update the repository
        params = {}
        params['baseurl'] = repo['baseurl'] = 'http://www.fedoraproject.org'
        resp = self.request('%s/fedora-fake' % base_uri, json.dumps(params),
                            'PUT')

        # Verify the repository
        res = json.loads(self.request('%s/fedora-fake' % base_uri).read())
        verify_repo(repo, res)

        # Delete the repository
        resp = self.request('%s/fedora-fake' % base_uri, '{}', 'DELETE')
        self.assertEquals(204, resp.status)


class HttpsRestTests(RestTests):
    """
    Run all of the same tests as above, but use https instead
    """
    def setUp(self):
        self.request = partial(request, host, ssl_port)
        model.reset()
