#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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
import kimchi.server
from kimchi.utils import get_enabled_plugins
import utils


test_server = None
model = None
host = None
port = None
ssl_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port

    utils.patch_auth()
    model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = utils.get_free_port('http')
    ssl_port = utils.get_free_port('https')
    test_server = utils.run_server(host, port, ssl_port, test_mode=True,
                                   model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


@unittest.skipUnless(
    'sample' in [plugin for plugin, _config in get_enabled_plugins()],
    'sample plugin is not enabled, skip this test!')
class PluginTests(unittest.TestCase):

    def setUp(self):
        self.request = partial(utils.request, host, ssl_port)

    def _create_rectangle(self, name, length, width):
        req = json.dumps({'name': name, 'length': length, 'width': width})
        resp = self.request('/plugins/sample/rectangles', req, 'POST')
        return resp

    def _get_rectangle(self, name):
        resp = self.request('/plugins/sample/rectangles/%s' % name)
        return json.loads(resp.read())

    def _create_rectangle_and_assert(self, name, length, width):
        resp = self._create_rectangle(name, length, width)
        self.assertEquals(201, resp.status)

        rectangle = self._get_rectangle(name)
        self.assertEquals(rectangle['name'], name)
        self.assertEquals(rectangle['length'], length)
        self.assertEquals(rectangle['width'], width)

    def _get_rectangles_list(self):
        resp = self.request('/plugins/sample/rectangles')
        rectangles = json.loads(resp.read())
        name_list = [rectangle['name'] for rectangle in rectangles]
        return name_list

    def test_rectangles(self):
        # Create two new rectangles
        self._create_rectangle_and_assert('small', 10, 8)
        self._create_rectangle_and_assert('big', 20, 16)

        # Verify they're in the list
        name_list = self._get_rectangles_list()
        self.assertIn('small', name_list)
        self.assertIn('big', name_list)

        # Update the big rectangle.
        req = json.dumps({'length': 40, 'width': 30})
        resp = self.request('/plugins/sample/rectangles/big', req, 'PUT')
        self.assertEquals(200, resp.status)
        big = self._get_rectangle('big')
        self.assertEquals(big['length'], 40)
        self.assertEquals(big['width'], 30)

        # Delete two rectangles
        resp = self.request('/plugins/sample/rectangles/big', '{}', 'DELETE')
        self.assertEquals(204, resp.status)
        resp = self.request('/plugins/sample/rectangles/small', '{}', 'DELETE')
        self.assertEquals(204, resp.status)
        name_list = self._get_rectangles_list()
        self.assertEquals([], name_list)

    def test_bad_params(self):
        # Bad name
        resp = self._create_rectangle(1.0, 30, 40)
        self.assertEquals(400, resp.status)

        # Bad length value
        resp = self._create_rectangle('test', -10.0, 40)
        self.assertEquals(400, resp.status)

        # Missing param for width
        req = json.dumps({'name': 'nowidth', 'length': 40})
        resp = self.request('/plugins/sample/rectangles', req, 'POST')
        self.assertEquals(400, resp.status)
