#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.

import unittest
import cherrypy
import json

import burnet.mockmodel
import burnet.controller

from utils import *

#utils.silence_server()

class MockModelTests(unittest.TestCase):
    def setUp(self):
        cherrypy.request.headers = {'Accept': 'application/json'}

    def test_collection(self):
        model = burnet.mockmodel.MockModel()
        c = burnet.controller.Collection(model)

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
        model = burnet.mockmodel.MockModel()
        r = burnet.controller.Resource(model)

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
        model = burnet.mockmodel.MockModel()
        port = get_free_port()
        host = '127.0.0.1'
        test_server = run_server(host, port, test_mode=True, model=model)

        # Create a VM
        req = json.dumps({'name': 'test'})
        request(host, port, '/templates', req, 'POST')
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        request(host, port, '/vms', req, 'POST')

        # Test screenshot refresh for running vm
        request(host, port, '/vms/test-vm/start', '{}', 'POST')
        resp = request(host, port, '/vms/test-vm/screenshot')
        url_1 = resp.getheader('Location')
        time.sleep(5)
        resp = request(host, port, '/vms/test-vm/screenshot')
        url_2 = resp.getheader('Location')
        self.assertNotEqual(url_1, url_2)

        # screenshots within 1 min is stored for slow user
        resp = request(host, port, url_1)
        self.assertEquals(200, resp.status)

        test_server.stop()
