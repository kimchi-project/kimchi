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

from kimchi.model.model import Model
from kimchi.rollbackcontext import RollbackContext
from utils import get_free_port, patch_auth, request, rollback_wrapper
from utils import run_server


model = None
test_server = None
host = None
port = None
ssl_port = None
cherrypy_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port, cherrypy_port

    patch_auth()
    model = Model(None, '/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


def _do_network_test(self, model, params):
    with RollbackContext() as rollback:
        net_name = params['name']
        uri = '/networks/%s' % net_name.encode('utf-8')

        # Create a network
        req = json.dumps(params)
        resp = self.request('/networks', req, 'POST')
        rollback.prependDefer(rollback_wrapper, model.network_delete,
                              net_name)
        self.assertEquals(201, resp.status)

        # Verify the network
        resp = self.request(uri)
        network = json.loads(resp.read())
        self.assertEquals('inactive', network['state'])
        self.assertTrue(network['persistent'])

        # activate the network
        resp = self.request(uri + '/activate', '{}', 'POST')
        rollback.prependDefer(rollback_wrapper,
                              model.network_deactivate, net_name)
        self.assertEquals(200, resp.status)
        resp = self.request(uri)
        network = json.loads(resp.read())
        self.assertEquals('active', network['state'])

        # Deactivate the network
        resp = self.request(uri + '/deactivate', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request(uri)
        network = json.loads(resp.read())
        self.assertEquals('inactive', network['state'])

        # Delete the network
        resp = self.request(uri, '{}', 'DELETE')
        self.assertEquals(204, resp.status)


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)

    def test_get_networks(self):
        networks = json.loads(self.request('/networks').read())
        self.assertIn('default', [net['name'] for net in networks])

        with RollbackContext() as rollback:
            # Now add a couple of Networks to the mock model
            for i in xrange(5):
                name = 'network-%i' % i
                req = json.dumps({'name': name,
                                  'connection': 'nat',
                                  'subnet': '127.0.10%i.0/24' % i})

                resp = self.request('/networks', req, 'POST')
                rollback.prependDefer(model.network_delete, name)
                self.assertEquals(201, resp.status)
                network = json.loads(resp.read())
                self.assertEquals([], network["vms"])

            nets = json.loads(self.request('/networks').read())
            self.assertEquals(len(networks) + 5, len(nets))

            network = json.loads(self.request('/networks/network-1').read())
            keys = [u'name', u'connection', u'interface', u'subnet', u'dhcp',
                    u'vms', u'in_use', u'autostart', u'state', u'persistent']
            self.assertEquals(sorted(keys), sorted(network.keys()))

    def test_network_lifecycle(self):
        # Verify all the supported network type
        networks = [{'name': u'kīмсhī-пet', 'connection': 'isolated'},
                    {'name': u'nat-network', 'connection': 'nat'},
                    {'name': u'subnet-network', 'connection': 'nat',
                     'subnet': '127.0.100.0/24'}]

        # Verify the current system has at least one interface to create a
        # bridged network
        interfaces = json.loads(self.request('/interfaces?type=nic').read())
        if len(interfaces) > 0:
            iface = interfaces[0]['name']
            networks.append({'name': u'bridge-network', 'connection': 'bridge',
                             'interface': iface})

        for net in networks:
            _do_network_test(self, model, net)
