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
import os
import tempfile
import unittest
import urllib
from functools import partial

import cherrypy
import mock
from wok.plugins.kimchi.model.featuretests import FeatureTests
from wok.rollbackcontext import RollbackContext

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import rollback_wrapper
from tests.utils import run_server

model = None
objectstore_loc = tempfile.mktemp()
test_server = None


@mock.patch('wok.plugins.kimchi.config.get_object_store')
def setUpModule(func):
    func.return_value = objectstore_loc
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=False)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model


def tearDownModule():
    test_server.stop()
    os.unlink(objectstore_loc)


def _do_network_test(self, model, params):
    with RollbackContext() as rollback:
        net_name = params['name']
        uri = urllib.parse.quote(f'/plugins/kimchi/networks/{net_name}')

        # Create a network
        req = json.dumps(params)
        resp = self.request('/plugins/kimchi/networks', req, 'POST')
        rollback.prependDefer(rollback_wrapper, model.network_delete, net_name)
        self.assertEqual(201, resp.status)

        # Verify the network
        resp = self.request(uri)
        network = json.loads(resp.read().decode('utf-8'))
        self.assertEqual('inactive', network['state'])
        self.assertTrue(network['persistent'])

        # activate the network
        resp = self.request(uri + '/activate', '{}', 'POST')
        rollback.prependDefer(
            rollback_wrapper, model.network_deactivate, net_name)
        self.assertEqual(200, resp.status)
        resp = self.request(uri)
        network = json.loads(resp.read().decode('utf-8'))
        self.assertEqual('active', network['state'])

        # Deactivate the network
        resp = self.request(uri + '/deactivate', '{}', 'POST')
        self.assertEqual(200, resp.status)
        resp = self.request(uri)
        network = json.loads(resp.read().decode('utf-8'))
        self.assertEqual('inactive', network['state'])

        # Define network update parameters
        updateParams = {'name': net_name + 'renamed'}
        connection = params.get('connection')
        if connection in ['isolated', 'nat'] and 'subnet' in params:
            updateParams['subnet'] = '127.0.200.0/24'
        elif connection == 'bridge' and 'vlan_id' in params:
            updateParams['vlan_id'] = 389

        # Test network update
        req = json.dumps(updateParams)
        resp = self.request(uri, req, 'PUT')
        self.assertEqual(303, resp.status)

        # Assert old name does not exist anymore
        resp = self.request(uri, '{}', 'GET')
        self.assertEqual(404, resp.status)

        # Delete the network
        resp = self.request(uri + 'renamed', '{}', 'DELETE')
        self.assertEqual(204, resp.status)


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request)

    def test_get_networks(self):
        networks = json.loads(
            self.request('/plugins/kimchi/networks').read().decode('utf-8')
        )
        self.assertIn('default', [net['name'] for net in networks])

        with RollbackContext() as rollback:
            # Now add a couple of Networks to the mock model
            for i in range(5):
                name = 'network-%i' % i
                req = json.dumps(
                    {'name': name, 'connection': 'nat',
                        'subnet': '127.0.10%i.0/24' % i}
                )

                resp = self.request('/plugins/kimchi/networks', req, 'POST')
                rollback.prependDefer(model.network_delete, name)
                self.assertEqual(201, resp.status)
                network = json.loads(resp.read().decode('utf-8'))
                self.assertEqual([], network['vms'])

            nets = json.loads(
                self.request('/plugins/kimchi/networks').read().decode('utf-8')
            )
            self.assertEqual(len(networks) + 5, len(nets))

            network = json.loads(
                self.request('/plugins/kimchi/networks/network-1')
                .read()
                .decode('utf-8')
            )
            keys = [
                'name',
                'connection',
                'interfaces',
                'subnet',
                'dhcp',
                'vms',
                'in_use',
                'autostart',
                'state',
                'persistent',
            ]
            self.assertEqual(sorted(keys), sorted(network.keys()))

    def test_network_lifecycle(self):
        # Verify all the supported network type
        networks = [
            {'name': 'kīмсhī-пet', 'connection': 'isolated'},
            {'name': '<!nat-network>&', 'connection': 'nat'},
            {'name': 'subnet-network', 'connection': 'nat',
                'subnet': '127.0.100.0/24'},
        ]

        # Verify the current system has at least one interface to create a
        # bridged network
        interfaces = json.loads(
            self.request('/plugins/kimchi/interfaces?_inuse=false&type=nic')
            .read()
            .decode('utf-8')
        )
        if len(interfaces) > 0:
            iface = interfaces[0]['name']
            networks.append(
                {
                    'name': 'macvtap-network',
                    'connection': 'macvtap',
                    'interfaces': [iface],
                }
            )
            if not FeatureTests.is_nm_running():
                networks.append(
                    {
                        'name': 'bridge-network',
                        'connection': 'bridge',
                        'interfaces': [iface],
                    }
                )

        for net in networks:
            _do_network_test(self, model, net)

    def test_macvtap_network_create_fails_more_than_one_interface(self):
        network = {
            'name': 'macvtap-network',
            'connection': 'macvtap',
            'interfaces': ['fake_iface1', 'fake_iface2', 'fake_iface3'],
        }

        expected_error_msg = 'KCHNET0030E'
        req = json.dumps(network)
        resp = self.request('/plugins/kimchi/networks', req, 'POST')
        self.assertEqual(400, resp.status)
        self.assertIn(expected_error_msg, resp.read().decode('utf-8'))

    def test_bridge_network_create_fails_more_than_one_interface(self):
        network = {
            'name': 'bridge-network',
            'connection': 'bridge',
            'interfaces': ['fake_iface1', 'fake_iface2', 'fake_iface3'],
        }
        expected_error_msg = 'KCHNET0030E'
        req = json.dumps(network)
        resp = self.request('/plugins/kimchi/networks', req, 'POST')
        self.assertEqual(400, resp.status)
        self.assertIn(expected_error_msg, resp.read().decode('utf-8'))
