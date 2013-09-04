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
import cherrypy
import json
import os

import kimchi.mockmodel
import kimchi.controller

from utils import *

#utils.silence_server()
test_server = None
model = None
host = None
port = None

class MockModelTests(unittest.TestCase):
    def setUp(self):
        global port, host, model, test_server
        cherrypy.request.headers = {'Accept': 'application/json'}
        model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
        port = get_free_port()
        host = '127.0.0.1'
        test_server = run_server(host, port, None, test_mode=True, model=model)

    def tearDown(self):
        test_server.stop()
        os.unlink('/tmp/obj-store-test')

    def test_collection(self):
        c = kimchi.controller.Collection(model)

        # The base Collection is always empty
        cherrypy.request.method = 'GET'
        self.assertEquals('[]', c.index())

        # POST and DELETE raise HTTP:405 by default
        for method in ('POST', 'DELETE'):
            cherrypy.request.method = method
            try:
                c.index()
            except cherrypy.HTTPError, e:
                self.assertEquals(405, e.code)
            else:
                self.fail("Expected exception not raised")

    def test_resource(self):
        r = kimchi.controller.Resource(model)

        # Test the base Resource representation
        cherrypy.request.method = 'GET'
        self.assertEquals('{}', r.index())

        # POST and DELETE raise HTTP:405 by default
        for method in ('POST', 'DELETE'):
            cherrypy.request.method = method
            try:
                r.index()
            except cherrypy.HTTPError, e:
                self.assertEquals(405, e.code)
            else:
                self.fail("Expected exception not raised")

    def test_screenshot_refresh(self):
        # Create a VM
        req = json.dumps({'name': 'test'})
        request(host, port, '/templates', req, 'POST')
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        request(host, port, '/vms', req, 'POST')

        # Test screenshot refresh for running vm
        request(host, port, '/vms/test-vm/start', '{}', 'POST')
        resp = request(host, port, '/vms/test-vm/screenshot')
        self.assertEquals(200, resp.status)
        self.assertEquals('image/png', resp.getheader('content-type'))
        resp1 = request(host, port, '/vms/test-vm')
        rspBody=resp1.read()
        testvm_Data=json.loads(rspBody)
        screenshotURL = testvm_Data['screenshot']
        time.sleep(5)
        resp2 = request(host, port, screenshotURL)
        self.assertEquals(200, resp2.status)
        self.assertEquals(resp2.getheader('content-type'), resp.getheader('content-type'))
        self.assertEquals(resp2.getheader('content-length'), resp.getheader('content-length'))
        self.assertEquals(resp2.getheader('last-modified'), resp.getheader('last-modified'))

    def test_vm_list_sorted(self):
        req = json.dumps({'name': 'test'})
        request(host, port, '/templates', req, 'POST')
        def add_vm(name):

            # Create a VM
            req = json.dumps({'name': name, 'template': '/templates/test'})
            request(host, port, '/vms', req, 'POST')

        add_vm('bca')
        add_vm('xba')
        add_vm('abc')
        add_vm('cab')

        self.assertEqual(model.vms_get_list(), ['abc', 'bca', 'cab', 'xba'])
