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

import burnet.mockmodel
import burnet.controller

import utils

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
