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
import unittest

from functools import partial

from kimchi.mockmodel import MockModel
from test_model_network import _do_network_test
from utils import get_free_port, patch_auth, request, run_server


model = None
test_server = None
host = None
port = None
ssl_port = None
cherrypy_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port, cherrypy_port

    patch_auth()
    model = MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


class MockNetworkTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)
        model.reset()

    def test_vlan_tag_bridge(self):
        # Verify the current system has at least one interface to create a
        # bridged network
        interfaces = json.loads(self.request('/interfaces?type=nic').read())
        if len(interfaces) > 0:
            iface = interfaces[0]['name']
            _do_network_test(self, model, {'name': u'bridge-network',
                                           'connection': 'bridge',
                                           'interface': iface, 'vlan_id': 987})
