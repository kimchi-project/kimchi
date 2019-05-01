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
import unittest
from functools import partial

import cherrypy
from test_model_network import _do_network_test
from wok.plugins.kimchi.model.featuretests import FeatureTests

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server


model = None
test_server = None


def setUpModule():
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=True)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model


def tearDownModule():
    test_server.stop()


class MockNetworkTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request)
        model.reset()

    @unittest.skipIf(
        FeatureTests.is_nm_running(),
        'test_vlan_tag_bridge skipped because Network ' 'Manager is running.',
    )
    def test_vlan_tag_bridge(self):
        # Verify the current system has at least one interface to create a
        # bridged network
        interfaces = json.loads(
            self.request('/plugins/kimchi/interfaces?_inuse=false&type=nic')
            .read()
            .decode('utf-8')
        )
        if len(interfaces) > 0:
            iface = interfaces[0]['name']
            _do_network_test(
                self,
                model,
                {
                    'name': u'vlan-tagged-bridge',
                    'connection': 'bridge',
                    'interface': iface,
                    'vlan_id': 987,
                },
            )
