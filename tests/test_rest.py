# -*- coding: utf-8 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import base64
import json
import os
import random
import shutil
import time
import unittest


from functools import partial


import iso_gen
import kimchi.mockmodel
import kimchi.server
from kimchi.rollbackcontext import RollbackContext
from utils import fake_user, get_free_port, https_request, patch_auth, request
from utils import run_server


test_server = None
model = None
host = None
port = None
ssl_port = None

#utils.silence_server()


def setUpModule():
    global test_server, model, host, port, ssl_port

    patch_auth()
    model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    test_server = run_server(host, port, ssl_port, test_mode=True, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


class RestTests(unittest.TestCase):
    def _async_op(self, cb, opaque):
        time.sleep(1)
        cb('success', True)

    def _except_op(self, cb, opaque):
        time.sleep(1)
        raise Exception("Oops")
        cb('success', True)

    def _intermid_op(self, cb, opaque):
        time.sleep(1)
        cb('in progress')

    def setUp(self):
        self.request = partial(request, host, port)
        model.reset()

    def assertHTTPStatus(self, code, *args):
        resp = self.request(*args)
        self.assertEquals(code, resp.status)

    def assertValidJSON(self, txt):
        try:
            json.loads(txt)
        except ValueError:
            self.fail("Invalid JSON: %s" % txt)

    def test_404(self):
        """
        A non-existent path should return HTTP:404
        """
        url_list = ['/doesnotexist', '/vms/blah']
        for url in url_list:
            self.assertHTTPStatus(404, url)

        # Make sure it fails for bad HTML requests
        # We must be authenticated first.  Otherwise all requests will return
        # HTTP:401.  Since HTTP Simple Auth is not allowed for text/html, we
        # need to use the login API and establish a session.
        user, pw = fake_user.items()[0]
        req = json.dumps({'userid': user, 'password': pw})
        resp = self.request('/login', req, 'POST')
        self.assertEquals(200, resp.status)
        cookie = resp.getheader('set-cookie')

        self.assertHTTPStatus(404, url, None, 'GET',
                              {'Accept': 'text/html',
                               'Cookie': cookie})

        # Verify it works for DELETE too
        self.assertHTTPStatus(404, '/templates/blah', '', 'DELETE')

    def test_accepts(self):
        """
        Verify the following expectations regarding the client Accept header:
          If omitted, default to html
          If 'application/json', serve the rest api
          If 'text/html', serve the UI
          If both of the above (in any order), serve the rest api
          If neither of the above, HTTP:406
        """
        resp = self.request("/", headers={})
        self.assertTrue('<!doctype html>' in resp.read().lower())

        resp = self.request("/", headers={'Accept': 'application/json'})
        self.assertValidJSON(resp.read())

        resp = self.request("/", headers={'Accept': 'text/html'})
        self.assertTrue('<!doctype html>' in resp.read().lower())

        resp = self.request("/", headers={'Accept':
                                          'application/json, text/html'})
        self.assertValidJSON(resp.read())

        resp = self.request("/", headers={'Accept':
                                          'text/html, application/json'})
        self.assertValidJSON(resp.read())

        h = {'Accept': 'text/plain'}
        self.assertHTTPStatus(406, "/", None, 'GET', h)

    def test_host_devices(self):
        nodedevs = json.loads(self.request('/host/devices').read())
        # Mockmodel brings 3 preconfigured scsi fc_host
        self.assertEquals(3, len(nodedevs))

        nodedev = json.loads(self.request('/host/devices/scsi_host4').read())
        # Mockmodel generates random wwpn and wwnn
        self.assertEquals('scsi_host4', nodedev['name'])
        self.assertEquals('fc_host', nodedev['adapter_type'])
        self.assertEquals(16, len(nodedev['wwpn']))
        self.assertEquals(16, len(nodedev['wwnn']))

    def test_get_vms(self):
        vms = json.loads(self.request('/vms').read())
        self.assertEquals(0, len(vms))

        # Create a template as a base for our VMs
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Now add a couple of VMs to the mock model
        for i in xrange(10):
            name = 'vm-%i' % i
            req = json.dumps({'name': name, 'template': '/templates/test'})
            resp = self.request('/vms', req, 'POST')
            self.assertEquals(201, resp.status)

        vms = json.loads(self.request('/vms').read())
        self.assertEquals(10, len(vms))

        vm = json.loads(self.request('/vms/vm-1').read())
        self.assertEquals('vm-1', vm['name'])
        self.assertEquals('shutoff', vm['state'])

    def test_edit_vm(self):
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        req = json.dumps({'name': 'vm-1', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)

        vm = json.loads(self.request('/vms/vm-1').read())
        self.assertEquals('vm-1', vm['name'])

        resp = self.request('/vms/vm-1/start', '{}', 'POST')
        self.assertEquals(200, resp.status)

        req = json.dumps({'name': 'new-vm'})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        resp = self.request('/vms/vm-1/stop', '{}', 'POST')
        self.assertEquals(200, resp.status)

        req = json.dumps({'name': 12})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'name': ''})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'name': 'new-name', 'cpus': 5})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(405, resp.status)

        req = json.dumps({'name': u'∨м-црdαtеd'})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(303, resp.status)
        vm = json.loads(self.request('/vms/∨м-црdαtеd', req).read())
        self.assertEquals(u'∨м-црdαtеd', vm['name'])

    def test_vm_lifecycle(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'disks': [{'size': 1}],
                          'icon': 'images/icon-debian.png',
                          'cdrom': '/nonexistent.iso'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create a VM
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('shutoff', vm['state'])
        self.assertEquals('images/icon-debian.png', vm['icon'])

        # Verify the volume was created
        vol_uri = '/storagepools/default/storagevolumes/%s-0.img' % vm['uuid']
        resp = self.request(vol_uri)
        vol = json.loads(resp.read())
        self.assertEquals(1 << 30, vol['capacity'])

        # Start the VM
        resp = self.request('/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('running', vm['state'])

        # Test screenshot
        resp = self.request(vm['screenshot'], method='HEAD')
        self.assertEquals(200, resp.status)
        self.assertTrue(resp.getheader('Content-type').startswith('image'))

        # Force stop the VM
        resp = self.request('/vms/test-vm/stop', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('shutoff', vm['state'])

        # Test create VM with same name fails with 400
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)

        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Delete the Template
        resp = self.request('/templates/test', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Verify the volume was deleted
        self.assertHTTPStatus(404, vol_uri)

    def test_vm_graphics(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create a VM with default args
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)
        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('0.0.0.0', vm['graphics']['listen'])
        self.assertEquals('vnc', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Create a VM with specified graphics type and listen
        graphics = {'type': 'vnc', 'listen': '127.0.0.1'}
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test',
                          'graphics': graphics})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)
        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('127.0.0.1', vm['graphics']['listen'])
        self.assertEquals('vnc', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Create a VM with listen as ipv6 address
        graphics = {'type': 'spice', 'listen': 'fe00::0'}
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test',
                          'graphics': graphics})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)
        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('fe00::0', vm['graphics']['listen'])
        self.assertEquals('spice', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Create a VM with specified graphics type and default listen
        graphics = {'type': 'spice'}
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test',
                          'graphics': graphics})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)
        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('0.0.0.0', vm['graphics']['listen'])
        self.assertEquals('spice', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Try to create a VM with invalid graphics type
        graphics = {'type': 'invalid'}
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test',
                          'graphics': graphics})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)

        # Try to create a VM with invalid graphics listen
        graphics = {'type': 'spice', 'listen': 'invalid'}
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test',
                          'graphics': graphics})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)

        # Delete the Template
        resp = self.request('/templates/test', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_vm_storage_devices(self):

        with RollbackContext() as rollback:
            # Create a template as a base for our VMs
            req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
            resp = self.request('/templates', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the template
            rollback.prependDefer(self.request,
                                  '/templates/test', '{}', 'DELETE')

            # Create a VM with default args
            req = json.dumps({'name': 'test-vm',
                              'template': '/templates/test'})
            resp = self.request('/vms', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the VM
            rollback.prependDefer(self.request,
                                  '/vms/test-vm', '{}', 'DELETE')

            # Check storage devices
            resp = self.request('/vms/test-vm/storages', '{}', 'GET')
            devices = json.loads(resp.read())
            self.assertEquals(2, len(devices))
            dev_types = []
            for d in devices:
                self.assertIn(u'type', d.keys())
                self.assertIn(u'dev', d.keys())
                self.assertIn(u'path', d.keys())
                dev_types.append(d['type'])

            self.assertEquals(['cdrom', 'disk'], sorted(dev_types))

            # Attach cdrom with nonexistent iso
            req = json.dumps({'dev': 'hdx',
                              'type': 'cdrom',
                              'path': '/tmp/nonexistent.iso'})
            resp = self.request('/vms/test-vm/storages', req, 'POST')
            self.assertEquals(400, resp.status)

            # Attach a cdrom with existent dev name
            open('/tmp/existent.iso', 'w').close()
            req = json.dumps({'dev': 'hdx',
                              'type': 'cdrom',
                              'path': '/tmp/existent.iso'})
            resp = self.request('/vms/test-vm/storages', req, 'POST')
            self.assertEquals(201, resp.status)
            cd_info = json.loads(resp.read())
            self.assertEquals('hdx', cd_info['dev'])
            self.assertEquals('cdrom', cd_info['type'])
            self.assertEquals('/tmp/existent.iso', cd_info['path'])
            # Delete the file and cdrom
            rollback.prependDefer(self.request,
                                  '/vms/test-vm/storages/hdx', '{}', 'DELETE')
            os.remove('/tmp/existent.iso')

            # Change path of storage cdrom
            req = json.dumps({'path': 'http://myserver.com/myiso.iso'})
            resp = self.request('/vms/test-vm/storages/hdx', req, 'PUT')
            self.assertEquals(200, resp.status)
            cd_info = json.loads(resp.read())
            self.assertEquals('http://myserver.com/myiso.iso', cd_info['path'])

            # Test GET
            devs = json.loads(self.request('/vms/test-vm/storages').read())
            self.assertEquals(3, len(devs))

            # Detach storage cdrom
            resp = self.request('/vms/test-vm/storages/hdx', '{}', 'DELETE')
            self.assertEquals(204, resp.status)

            # Test GET
            devs = json.loads(self.request('/vms/test-vm/storages').read())
            self.assertEquals(2, len(devs))

    def test_vm_iface(self):

        with RollbackContext() as rollback:
            # Create a template as a base for our VMs
            req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
            resp = self.request('/templates', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the template
            rollback.prependDefer(self.request,
                                  '/templates/test', '{}', 'DELETE')

            # Create a VM with default args
            req = json.dumps({'name': 'test-vm',
                              'template': '/templates/test'})
            resp = self.request('/vms', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the VM
            rollback.prependDefer(self.request,
                                  '/vms/test-vm', '{}', 'DELETE')

            # Create a network
            req = json.dumps({'name': 'test-network',
                              'connection': 'nat',
                              'net': '127.0.1.0/24'})
            resp = self.request('/networks', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the network
            rollback.prependDefer(self.request,
                                  '/networks/test-network', '{}', 'DELETE')

            ifaces = json.loads(self.request('/vms/test-vm/ifaces').read())
            self.assertEquals(1, len(ifaces))

            for iface in ifaces:
                res = json.loads(self.request('/vms/test-vm/ifaces/%s' %
                                              iface['mac']).read())
                self.assertEquals('default', res['network'])
                self.assertEquals(17, len(res['mac']))
                self.assertEquals('virtio', res['model'])

            # attach network interface to vm
            req = json.dumps({"type": "network",
                              "network": "test-network",
                              "model": "virtio"})
            resp = self.request('/vms/test-vm/ifaces', req, 'POST')
            self.assertEquals(201, resp.status)
            iface = json.loads(resp.read())

            self.assertEquals('test-network', iface['network'])
            self.assertEquals(17, len(iface['mac']))
            self.assertEquals('virtio', iface['model'])
            self.assertEquals('network', iface['type'])

            # detach network interface from vm
            resp = self.request('/vms/test-vm/ifaces/%s' % iface['mac'],
                                '{}', 'DELETE')
            self.assertEquals(204, resp.status)

    def test_vm_customise_storage(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso',
                                          'disks': [{'size': 1}]})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create alternate storage
        req = json.dumps({'name': 'alt',
                          'capacity': 1024,
                          'allocated': 512,
                          'path': '/tmp',
                          'type': 'dir'})
        resp = self.request('/storagepools', req, 'POST')
        self.assertEquals(201, resp.status)
        resp = self.request('/storagepools/alt/activate', req, 'POST')
        self.assertEquals(200, resp.status)

        # Create a VM
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test',
                          'storagepool': '/storagepools/alt'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)
        vm_info = json.loads(resp.read())

        # Test template not changed after vm customise its pool
        t = json.loads(self.request('/templates/test').read())
        self.assertEquals(t['storagepool'], '/storagepools/default')

        # Verify the volume was created
        vol_uri = '/storagepools/alt/storagevolumes/%s-0.img' % vm_info['uuid']
        resp = self.request(vol_uri)
        vol = json.loads(resp.read())
        self.assertEquals(1 << 30, vol['capacity'])

        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Verify the volume was deleted
        self.assertHTTPStatus(404, vol_uri)

    def test_scsi_fc_storage(self):
        # Create scsi fc pool
        req = json.dumps({'name': 'scsi_fc_pool',
                          'type': 'scsi',
                          'source': {'adapter_name': 'scsi_host3'}})
        resp = self.request('/storagepools', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create template with this pool
        req = json.dumps({'name': 'test_fc_pool', 'cdrom': '/nonexistent.iso',
                          'storagepool': '/storagepools/scsi_fc_pool'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Test create vms using lun of this pool
        ### activate the storage pool
        resp = self.request('/storagepools/scsi_fc_pool/activate', '{}',
                            'POST')

        ### Get scsi pool luns and choose one
        resp = self.request('/storagepools/scsi_fc_pool/storagevolumes')
        luns = json.loads(resp.read())
        lun_name = random.choice(luns).get('name')

        ### Create vm in scsi pool without volumes: Error
        req = json.dumps({'template': '/templates/test_fc_pool'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)

        ### Create vm in scsi pool
        req = json.dumps({'name': 'test-vm',
                          'template': '/templates/test_fc_pool',
                          'volumes': [lun_name]})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)

        # Start the VM
        resp = self.request('/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('running', vm['state'])

        # Force stop the VM
        resp = self.request('/vms/test-vm/stop', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('shutoff', vm['state'])

        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_template_customise_storage(self):
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso',
                          'disks': [{'size': 1}]})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Update a Template with non-existent pool fails with 400
        req = json.dumps({'storagepool': '/storagepools/alt'})
        resp = self.request('/templates/test', req, 'PUT')
        self.assertEquals(400, resp.status)

        # Create alternate storage
        req = json.dumps({'name': 'alt',
                          'capacity': 1024,
                          'allocated': 512,
                          'path': '/tmp',
                          'type': 'dir'})
        resp = self.request('/storagepools', req, 'POST')
        self.assertEquals(201, resp.status)

        req = json.dumps({'storagepool': '/storagepools/alt'})
        resp = self.request('/templates/test', req, 'PUT')
        self.assertEquals(200, resp.status)

        # Create a VM on inactive pool fails with 400
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)

        resp = self.request('/storagepools/alt/activate', req, 'POST')
        self.assertEquals(200, resp.status)

        # Create a VM
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        vm = json.loads(resp.read())
        self.assertEquals(201, resp.status)

        # Verify the volume was created
        vol_uri = '/storagepools/alt/storagevolumes/%s-0.img' % vm['uuid']
        resp = self.request(vol_uri)
        vol = json.loads(resp.read())
        self.assertEquals(1073741824, vol['capacity'])

        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Verify the volume was deleted
        self.assertHTTPStatus(404, vol_uri)

    def test_template_customise_network(self):
        with RollbackContext() as rollback:
            tmpl = {'name': 'test', 'cdrom': '/nonexistent.iso',
                    'disks': [{'size': 1}]}
            req = json.dumps(tmpl)
            resp = self.request('/templates', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the template
            rollback.prependDefer(self.request,
                                  '/templates/test', '{}', 'DELETE')
            tmpl_res = json.loads(resp.read())
            self.assertTrue(type(tmpl_res['networks']) is list)
            self.assertEquals("default", tmpl_res['networks'][0])

            tmpl['name'] = "failed_tmpl"
            # Create a Template with non-array network fails with 400
            tmpl['networks'] = "test-network"
            req = json.dumps(tmpl)
            resp = self.request('/templates', req, 'POST')
            self.assertEquals(400, resp.status)

            # Create a Template with non-existent network fails with 400
            tmpl['networks'] = ["test-network"]
            req = json.dumps(tmpl)
            resp = self.request('/templates', req, 'POST')
            self.assertEquals(400, resp.status)

            # Create a network
            req = json.dumps({'name': 'test-network',
                              'connection': 'nat',
                              'net': '127.0.1.0/24'})
            resp = self.request('/networks', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the network
            rollback.prependDefer(self.request,
                                  '/networks/test-network', '{}', 'DELETE')

            tmpl['name'] = "test"
            # Update a Template with non-array network fails with 400
            tmpl['networks'] = "bad-network"
            req = json.dumps(tmpl)
            resp = self.request('/templates/test', req, 'PUT')
            self.assertEquals(400, resp.status)
            # Update a Template with non-existent network fails with 400
            tmpl['networks'] = ["bad-network"]
            req = json.dumps(tmpl)
            resp = self.request('/templates/test', req, 'PUT')
            self.assertEquals(400, resp.status)

            # Update a Template with existent network, successful
            tmpl['networks'] = ["default", "test-network"]
            req = json.dumps(tmpl)
            resp = self.request('/templates/test', req, 'PUT')
            self.assertEquals(200, resp.status)
            tmpl_res = json.loads(resp.read())
            self.assertTrue(type(tmpl_res['networks']) is list)
            self.assertEquals(tmpl['networks'], tmpl_res['networks'])

    def test_unnamed_vms(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create 5 unnamed vms from this template
        for i in xrange(1, 6):
            req = json.dumps({'template': '/templates/test'})
            vm = json.loads(self.request('/vms', req, 'POST').read())
            self.assertEquals('test-vm-%i' % i, vm['name'])
        count = len(json.loads(self.request('/vms').read()))
        self.assertEquals(5, count)

    def test_create_vm_without_template(self):
        req = json.dumps({'name': 'vm-without-template'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)
        resp = json.loads(resp.read())
        self.assertIn(u"KCHVM0016E:", resp['reason'])

    def test_create_vm_with_bad_template_uri(self):
        req = json.dumps({'name': 'vm-bad-template',
                          'template': '/mytemplate'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)
        resp = json.loads(resp.read())
        self.assertIn(u"KCHVM0012E", resp['reason'])

    def test_get_storagepools(self):
        storagepools = json.loads(self.request('/storagepools').read())
        self.assertEquals(2, len(storagepools))
        self.assertEquals('default', storagepools[0]['name'])
        self.assertEquals('active', storagepools[0]['state'])
        self.assertEquals('kimchi_isos', storagepools[1]['name'])
        self.assertEquals('kimchi-iso', storagepools[1]['type'])

        # Now add a couple of StoragePools to the mock model
        for i in xrange(5):
            name = 'kīмсhī-storagepool-%i' % i
            req = json.dumps({'name': name,
                              'capacity': 1024,
                              'allocated': 512,
                              'path': '/var/lib/libvirt/images/%i' % i,
                              'type': 'dir'})
            resp = self.request('/storagepools', req, 'POST')
            self.assertEquals(201, resp.status)

        req = json.dumps({'name': 'kīмсhī-storagepool-1',
                          'capacity': 1024,
                          'allocated': 512,
                          'path': '/var/lib/libvirt/images/%i' % i,
                          'type': 'dir'})
        resp = self.request('/storagepools', req, 'POST')
        self.assertEquals(400, resp.status)

        # Reserved pool return 400
        req = json.dumps({'name': 'kimchi_isos',
                          'capacity': 1024,
                          'allocated': 512,
                          'path': '/var/lib/libvirt/images/%i' % i,
                          'type': 'dir'})
        resp = request(host, port, '/storagepools', req, 'POST')
        self.assertEquals(400, resp.status)

        storagepools = json.loads(self.request('/storagepools').read())
        self.assertEquals(7, len(storagepools))

        resp = self.request('/storagepools/kīмсhī-storagepool-1')
        storagepool = json.loads(resp.read())
        self.assertEquals('kīмсhī-storagepool-1',
                          storagepool['name'].encode("utf-8"))
        self.assertEquals('inactive', storagepool['state'])
        self.assertIn('source', storagepool)

    def test_storagepool_action(self):
        # Create a storage pool
        req = json.dumps({'name': 'test-pool',
                          'capacity': 1024,
                          'allocated': 512,
                          'path': '/var/lib/libvirt/images/',
                          'type': 'dir'})
        resp = self.request('/storagepools', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the storage pool
        storagepool = json.loads(
            self.request('/storagepools/test-pool').read())
        self.assertEquals('inactive', storagepool['state'])
        if storagepool['type'] == 'dir':
            self.assertEquals(True, storagepool['autostart'])
        else:
            self.assertEquals(False, storagepool['autostart'])

        # activate the storage pool
        resp = self.request('/storagepools/test-pool/activate', '{}', 'POST')
        storagepool = json.loads(
            self.request('/storagepools/test-pool').read())
        self.assertEquals('active', storagepool['state'])

        # Deactivate the storage pool
        resp = self.request('/storagepools/test-pool/deactivate', '{}', 'POST')
        storagepool = json.loads(
            self.request('/storagepools/test-pool').read())
        self.assertEquals('inactive', storagepool['state'])

        # Set autostart flag of the storage pool
        for autostart in [True, False]:
            t = {'autostart': autostart}
            req = json.dumps(t)
            resp = self.request('/storagepools/test-pool', req, 'PUT')
            storagepool = json.loads(
                self.request('/storagepools/test-pool').read())
            self.assertEquals(autostart, storagepool['autostart'])

        # Delete the storage pool
        resp = self.request('/storagepools/test-pool', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_get_storagevolumes(self):
        # Now add a StoragePool to the mock model
        self._create_pool('pool-1')

        # Test storagevolumes can't be listed with inactive pool
        resp = self.request('/storagepools/pool-1/storagevolumes')
        self.assertEquals(400, resp.status)

        resp = self.request('/storagepools/pool-1/activate', '{}', 'POST')
        self.assertEquals(200, resp.status)
        nr_vols = json.loads(
            self.request('/storagepools/pool-1').read())['nr_volumes']
        self.assertEquals(0, nr_vols)

        # Now add a couple of storage volumes to the mock model
        for i in xrange(5):
            name = 'volume-%i' % i
            req = json.dumps({'name': name,
                              'capacity': 1024,
                              'allocation': 512,
                              'type': 'disk',
                              'format': 'raw'})
            resp = self.request('/storagepools/pool-1/storagevolumes',
                                req, 'POST')
            self.assertEquals(201, resp.status)

        nr_vols = json.loads(
            self.request('/storagepools/pool-1').read())['nr_volumes']
        self.assertEquals(5, nr_vols)
        resp = self.request('/storagepools/pool-1/storagevolumes')
        storagevolumes = json.loads(resp.read())
        self.assertEquals(5, len(storagevolumes))

        resp = self.request('/storagepools/pool-1/storagevolumes/volume-1')
        storagevolume = json.loads(resp.read())
        self.assertEquals('volume-1', storagevolume['name'])
        self.assertEquals('raw', storagevolume['format'])
        self.assertEquals('/var/lib/libvirt/images/volume-1',
                          storagevolume['path'])

        # Now remove the StoragePool from mock model
        self._delete_pool('pool-1')

    def test_storagevolume_action(self):
        self._create_pool('pool-2')

        # Create a storage volume can only be successful for active pool
        req = json.dumps({'name': 'test-volume',
                          'capacity': 1024,
                          'allocation': 512,
                          'type': 'disk',
                          'format': 'raw'})
        resp = self.request('/storagepools/pool-2/storagevolumes/',
                            req, 'POST')
        self.assertEquals(400, resp.status)
        resp = self.request('/storagepools/pool-2/activate', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/storagepools/pool-2/storagevolumes/',
                            req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the storage volume
        resp = self.request('/storagepools/pool-2/storagevolumes/test-volume')
        storagevolume = json.loads(resp.read())
        self.assertEquals('raw', storagevolume['format'])

        # Resize the storage volume
        req = json.dumps({'size': 768})
        uri = '/storagepools/pool-2/storagevolumes/test-volume/resize'
        resp = self.request(uri, req, 'POST')
        uri = '/storagepools/pool-2/storagevolumes/test-volume'
        storagevolume = json.loads(self.request(uri).read())
        self.assertEquals(768, storagevolume['capacity'])

        # Wipe the storage volume
        uri = '/storagepools/pool-2/storagevolumes/test-volume/wipe'
        resp = self.request(uri, '{}', 'POST')
        uri = '/storagepools/pool-2/storagevolumes/test-volume'
        storagevolume = json.loads(self.request(uri).read())
        self.assertEquals(0, storagevolume['allocation'])

        # Delete the storage volume
        resp = self.request('/storagepools/pool-2/storagevolumes/test-volume',
                            '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Now remove the StoragePool from mock model
        self._delete_pool('pool-2')

    def _create_pool(self, name):
        req = json.dumps({'name': name,
                          'capacity': 10240,
                          'allocated': 5120,
                          'path': '/var/lib/libvirt/images/',
                          'type': 'dir'})
        resp = self.request('/storagepools', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the storage pool
        storagepool = json.loads(self.request('/storagepools/%s'
                                              % name).read())
        self.assertEquals('inactive', storagepool['state'])
        return name

    def _delete_pool(self, name):
        # Delete the storage pool
        resp = self.request('/storagepools/%s' % name, '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_templates(self):
        def verify_template(t, res):
            for field in ('name', 'os_distro', 'os_version', 'memory',
                          'cpus', 'storagepool', 'graphics'):
                if field in t:
                    self.assertEquals(t[field], res[field])

        resp = self.request('/templates')
        self.assertEquals(200, resp.status)
        self.assertEquals(0, len(json.loads(resp.read())))

        # Create a template without cdrom fails with 400
        t = {'name': 'test', 'os_distro': 'ImagineOS',
             'os_version': '1.0', 'memory': 1024, 'cpus': 1,
             'storagepool': '/storagepools/alt'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(400, resp.status)

        # Create a template
        graphics = {'type': 'spice', 'listen': '127.0.0.1'}
        t = {'name': 'test', 'os_distro': 'ImagineOS',
             'os_version': '1.0', 'memory': 1024, 'cpus': 1,
             'storagepool': '/storagepools/alt', 'cdrom': '/nonexistent.iso',
             'graphics': graphics}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/test').read())
        verify_template(t, res)

        # clone a template
        resp = self.request('/templates/%s/clone' % t['name'], '{}', 'POST')
        self.assertEquals(303, resp.status)

        # Verify the clone template
        res = json.loads(self.request('/templates/%s-clone1' %
                                      t['name']).read())
        old_temp = t['name']
        t['name'] = res['name']
        verify_template(t, res)
        # Delete the clone template
        resp = self.request('/templates/%s' % t['name'], '{}', 'DELETE')
        self.assertEquals(204, resp.status)
        t['name'] = old_temp

        # Create a template with same name fails with 400
        t = {'name': 'test', 'os_distro': 'ImagineOS',
             'os_version': '1.0', 'memory': 1024, 'cpus': 1,
             'storagepool': '/storagepools/default',
             'cdrom': '/nonexistent.iso'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(400, resp.status)

        # Update the template
        t['os_distro'] = 'Linux.ISO'
        t['os_version'] = '1.1'
        t['graphics'] = {'type': 'vnc', 'listen': '0.0.0.0'}
        req = json.dumps(t)
        resp = self.request('/templates/%s' % t['name'], req, 'PUT')
        self.assertEquals(200, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/test').read())
        verify_template(t, res)

        # Update the template with ipv6 address as listen
        t['graphics'] = {'type': 'vnc', 'listen': 'fe00::0'}
        req = json.dumps(t)
        resp = self.request('/templates/%s' % t['name'], req, 'PUT')
        self.assertEquals(200, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/test').read())
        verify_template(t, res)

        # Update the template with integer values
        t['memory'] = 512
        t['cpus'] = 2
        req = json.dumps(t)
        resp = self.request('/templates/%s' % t['name'], req, 'PUT')
        self.assertEquals(200, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/%s' % t['name']).read())
        verify_template(t, res)

        # Update the template name
        oldname = t['name']
        t['name'] = "test1"
        req = json.dumps(t)
        resp = self.request('/templates/%s' % oldname, req, 'PUT')
        self.assertEquals(303, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/%s' % t['name']).read())
        verify_template(t, res)

        # Try to change template name to empty string
        t = {"name": "test1"}
        tmpl_name = t['name']
        t['name'] = '   '
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)
        # Get the right template name back.
        t['name'] = tmpl_name

        # Try to change template memory to a non-number value
        t['memory'] = 'invalid-value'
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Try to clean up template memory value
        t['memory'] = '    '
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Try to change template cpus to a non-number value
        t['cpus'] = 'invalid-value'
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Try to change template graphics type to invalid value
        t['graphics'] = {'type': 'invalid'}
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Try to change template graphics type to invalid listen
        t['graphics'] = {'type': 'vnc', 'listen': 'invalid'}
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Try to clean up template cpus value
        t['cpus'] = '    '
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Test nonexistent fields, specify a field 'foo' isn't in the Template
        t['foo'] = "bar"
        req = json.dumps(t)
        resp = self.request('/templates/%s' % oldname, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Delete the template
        resp = self.request('/templates/%s' % tmpl_name, '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_template_integrity(self):

        path = '/tmp/kimchi-iso/'
        if not os.path.exists(path):
            os.makedirs(path)
        iso = path + 'ubuntu12.04.iso'
        iso_gen.construct_fake_iso(iso, True, '12.04', 'ubuntu')

        req = json.dumps({'name': 'test-network',
                          'connection': 'nat',
                          'net': '127.0.1.0/24'})
        resp = request(host, port, '/networks', req, 'POST')
        self.assertEquals(201, resp.status)

        t = {'name': 'test', 'memory': 1024, 'cpus': 1,
             'networks': ['test-network'], 'cdrom': iso,
             'disks': [{'volume': iso}]}

        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        shutil.rmtree(path)
        # Delete the network
        resp = request(host, port, '/networks/test-network', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/test').read())
        self.assertEquals(res['invalid']['cdrom'], [iso])
        self.assertEquals(res['invalid']['networks'], ['test-network'])
        self.assertEquals(res['invalid']['disks'], [iso])

        # Delete the template
        resp = request(host, port, '/templates/test', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_iso_scan_shallow(self):
        # fake environment preparation
        self._create_pool('pool-3')
        self.request('/storagepools/pool-3/activate', '{}', 'POST')
        params = {'name': 'fedora.iso',
                  'capacity': 1024,
                  'type': 'file',
                  'format': 'iso'}
        model.storagevolumes_create('pool-3', params)

        storagevolume = json.loads(self.request(
            '/storagepools/kimchi_isos/storagevolumes/').read())[0]
        self.assertEquals('pool-3-fedora.iso', storagevolume['name'])
        self.assertEquals('iso', storagevolume['format'])
        self.assertEquals('/var/lib/libvirt/images/fedora.iso',
                          storagevolume['path'])
        self.assertEquals(1024 << 20, storagevolume['capacity'])
        self.assertEquals(1024 << 20, storagevolume['allocation'])
        self.assertEquals('17', storagevolume['os_version'])
        self.assertEquals('fedora', storagevolume['os_distro'])
        self.assertEquals(True, storagevolume['bootable'])

        # Create a template
        # In real model os distro/version can be omitted
        # as we will scan the iso
        req = json.dumps({'name': 'test',
                          'cdrom': storagevolume['path'],
                          'os_distro': storagevolume['os_distro'],
                          'os_version': storagevolume['os_version']})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the template
        t = json.loads(self.request('/templates/test').read())
        self.assertEquals('test', t['name'])
        self.assertEquals('fedora', t['os_distro'])
        self.assertEquals('17', t['os_version'])
        self.assertEquals(1024, t['memory'])

        # Deactivate or destroy scan pool return 405
        resp = self.request('/storagepools/kimchi_isos/storagevolumes'
                            '/deactivate', '{}', 'POST')
        self.assertEquals(405, resp.status)

        resp = self.request('/storagepools/kimchi_isos/storagevolumes',
                            '{}', 'DELETE')
        self.assertEquals(405, resp.status)

        # Delete the template
        resp = self.request('/templates/%s' % t['name'], '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        self._delete_pool('pool-3')

    def test_screenshot_refresh(self):
        # Create a VM
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
        self.request('/templates', req, 'POST')
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        self.request('/vms', req, 'POST')

        # Test screenshot for shut-off state vm
        resp = self.request('/vms/test-vm/screenshot')
        self.assertEquals(404, resp.status)

        # Test screenshot for running vm
        self.request('/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        resp = self.request(vm['screenshot'], method='HEAD')
        self.assertEquals(200, resp.status)
        self.assertTrue(resp.getheader('Content-type').startswith('image'))

        # Test screenshot sub-resource redirect
        resp = self.request('/vms/test-vm/screenshot')
        self.assertEquals(200, resp.status)
        self.assertEquals('image/png', resp.getheader('content-type'))
        lastMod1 = resp.getheader('last-modified')

        # Take another screenshot instantly and compare the last Modified date
        resp = self.request('/vms/test-vm/screenshot')
        lastMod2 = resp.getheader('last-modified')
        self.assertEquals(lastMod2, lastMod1)

        resp = self.request('/vms/test-vm/screenshot', '{}', 'DELETE')
        self.assertEquals(405, resp.status)

        # No screenshot after stopped the VM
        self.request('/vms/test-vm/stop', '{}', 'POST')
        resp = self.request('/vms/test-vm/screenshot')
        self.assertEquals(404, resp.status)

        # Picture link not available after VM deleted
        self.request('/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        img_lnk = vm['screenshot']
        self.request('/vms/test-vm', '{}', 'DELETE')
        resp = self.request(img_lnk)
        self.assertEquals(404, resp.status)

    def test_interfaces(self):
        resp = self.request('/interfaces').read()
        self.assertIn('name', resp)
        interfaces = json.loads(resp)
        for interface in interfaces:
            self.assertIn('name', interface)
            self.assertIn('type', interface)
            self.assertIn('ipaddr', interface)
            self.assertIn('netmask', interface)
            self.assertIn('status', interface)

        ident = "eth1"
        resp = self.request('/interfaces/%s' % ident).read()
        interface = json.loads(resp)
        self.assertEquals(interface['name'], ident)
        self.assertEquals(interface['type'], "nic")
        self.assertEquals(interface['ipaddr'], "192.168.0.101")
        self.assertEquals(interface['netmask'], "255.255.255.0")
        self.assertEquals(interface['status'], "active")

    def test_get_networks(self):
        networks = json.loads(request(host, port, '/networks').read())
        self.assertEquals(1, len(networks))
        self.assertEquals('default', networks[0]['name'])
        self.assertEquals([], networks[0]['vms'])

        # Now add a couple of Networks to the mock model
        for i in xrange(5):
            name = 'network-%i' % i
            req = json.dumps({'name': name,
                              'connection': 'nat',
                              'subnet': '127.0.10%i.0/24' % i})

            resp = request(host, port, '/networks', req, 'POST')
            self.assertEquals(201, resp.status)
            network = json.loads(resp.read())
            self.assertEquals([], network["vms"])

        networks = json.loads(request(host, port, '/networks').read())
        self.assertEquals(6, len(networks))

        network = json.loads(request(host, port,
                                     '/networks/network-1').read())
        self.assertEquals('network-1', network['name'])
        self.assertEquals('inactive', network['state'])
        # Delete the network
        for i in xrange(5):
            resp = request(host, port, '/networks/network-%i' % i,
                           '{}', 'DELETE')
            self.assertEquals(204, resp.status)

    def test_network_action(self):
        # Create a network
        req = json.dumps({'name': 'test-network',
                          'connection': 'nat',
                          'net': '127.0.1.0/24'})
        resp = request(host, port, '/networks', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the network
        network = json.loads(request(host, port,
                                     '/networks/test-network').read())
        self.assertEquals('inactive', network['state'])

        # activate the network
        resp = request(host, port,
                       '/networks/test-network/activate', '{}', 'POST')
        network = json.loads(request(host, port,
                                     '/networks/test-network').read())
        self.assertEquals('active', network['state'])

        # Deactivate the network
        resp = request(host, port,
                       '/networks/test-network/deactivate', '{}', 'POST')
        network = json.loads(request(host, port,
                                     '/networks/test-network').read())
        self.assertEquals('inactive', network['state'])

        # Delete the network
        resp = request(host, port, '/networks/test-network', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def _wait_task(self, taskid, timeout=5):
        for i in range(0, timeout):
            task = json.loads(self.request('/tasks/%s' % taskid).read())
            if task['status'] == 'running':
                time.sleep(1)

    def test_tasks(self):
        model.add_task('', self._async_op)
        model.add_task('', self._except_op)
        model.add_task('', self._intermid_op)
        tasks = json.loads(self.request('/tasks').read())
        self.assertEquals(3, len(tasks))
        self._wait_task('2')
        foo2 = json.loads(self.request('/tasks/%s' % '2').read())
        self.assertEquals('failed', foo2['status'])
        self._wait_task('3')
        foo3 = json.loads(self.request('/tasks/%s' % '3').read())
        self.assertEquals('in progress', foo3['message'])
        self.assertEquals('running', foo3['status'])

    def test_config(self):
        resp = self.request('/config').read()
        conf = json.loads(resp)
        self.assertEquals(port, conf['http_port'])

    def test_capabilities(self):
        resp = self.request('/config/capabilities').read()
        conf = json.loads(resp)
        self.assertIn('libvirt_stream_protocols', conf)
        self.assertIn('qemu_stream', conf)
        self.assertIn('screenshot', conf)
        self.assertIn('system_report_tool', conf)

    def test_auth_unprotected(self):
        hdrs = {'AUTHORIZATION': ''}
        uris = ['/js/kimchi.min.js',
                '/css/theme-default.min.css',
                '/libs/jquery-1.10.0.min.js',
                '/images/icon-vm.png',
                '/kimchi-ui.html',
                '/login-window.html',
                '/logout']
        for uri in uris:
            resp = self.request(uri, None, 'HEAD', hdrs)
            self.assertEquals(200, resp.status)

        user, pw = fake_user.items()[0]
        req = json.dumps({'userid': user, 'password': pw})
        resp = self.request('/login', req, 'POST', hdrs)
        self.assertEquals(200, resp.status)

    def test_auth_protected(self):
        hdrs = {'AUTHORIZATION': ''}
        uris = ['/vms',
                '/vms/doesnotexist',
                '/tasks']
        for uri in uris:
            resp = self.request(uri, None, 'GET', hdrs)
            self.assertEquals(401, resp.status)

    def test_auth_bad_creds(self):
        # Test HTTPBA
        hdrs = {'AUTHORIZATION': "Basic " + base64.b64encode("nouser:badpass")}
        resp = self.request('/vms', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)

        # Test REST API
        hdrs = {'AUTHORIZATION': ''}
        req = json.dumps({'userid': 'nouser', 'password': 'badpass'})
        resp = self.request('/login', req, 'POST', hdrs)
        self.assertEquals(401, resp.status)

    def test_auth_browser_no_httpba(self):
        # Kimchi detects REST requests from the browser by looking for a
        # specific header
        hdrs = {"X-Requested-With": "XMLHttpRequest"}

        # Try our request (Note that request() will add a valid HTTPBA header)
        resp = self.request('/vms', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)
        self.assertEquals(None, resp.getheader('WWW-Authenticate'))

    def test_auth_session(self):
        hdrs = {'AUTHORIZATION': '',
                'Content-Type': 'application/json',
                'Accept': 'application/json'}

        # Test we are logged out
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)

        # Execute a login call
        user, pw = fake_user.items()[0]
        req = json.dumps({'userid': user, 'password': pw})
        resp = self.request('/login', req, 'POST', hdrs)
        self.assertEquals(200, resp.status)
        cookie = resp.getheader('set-cookie')
        hdrs['Cookie'] = cookie

        # Test we are logged in with the cookie
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(200, resp.status)

        # Execute a logout call
        resp = self.request('/logout', '{}', 'POST', hdrs)
        self.assertEquals(200, resp.status)
        del hdrs['Cookie']

        # Test we are logged out
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)

    def test_distros(self):
        resp = self.request('/config/distros').read()
        distros = json.loads(resp)
        for distro in distros:
            self.assertIn('name', distro)
            self.assertIn('os_distro', distro)
            self.assertIn('os_version', distro)
            self.assertIn('path', distro)

        ident = "fedora-19"
        resp = self.request('/config/distros/%s' % ident).read()
        distro = json.loads(resp)
        self.assertEquals(distro['name'], ident)
        self.assertEquals(distro['os_distro'], "fedora")
        self.assertEquals(distro['os_version'], "19")
        self.assertIn('path', distro)

    def test_debugreports(self):
        resp = request(host, port, '/debugreports')
        self.assertEquals(200, resp.status)

    def _report_delete(self, name):
        request(host, port, '/debugreports/%s' % name, '{}', 'DELETE')

    def test_create_debugreport(self):
        req = json.dumps({'name': 'report1'})
        with RollbackContext() as rollback:
            resp = request(host, port, '/debugreports', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            self._wait_task(task['id'])
            rollback.prependDefer(self._report_delete, 'report1')
            resp = request(host, port, '/debugreports/report1')
            debugreport = json.loads(resp.read())
            self.assertEquals("report1", debugreport['name'])
            self.assertEquals(200, resp.status)

    def test_debugreport_download(self):
        req = json.dumps({'name': 'report1'})
        with RollbackContext() as rollback:
            resp = request(host, port, '/debugreports', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            self._wait_task(task['id'], 20)
            rollback.prependDefer(self._report_delete, 'report1')
            resp = request(host, port, '/debugreports/report1')
            debugreport = json.loads(resp.read())
            self.assertEquals("report1", debugreport['name'])
            self.assertEquals(200, resp.status)
            resp = request(host, port, '/debugreports/report1/content')
            self.assertEquals(200, resp.status)

    def test_host(self):
        resp = self.request('/host').read()
        info = json.loads(resp)
        self.assertEquals('Red Hat Enterprise Linux Server', info['os_distro'])
        self.assertEquals('6.4', info['os_version'])
        self.assertEquals('Santiago', info['os_codename'])
        self.assertEquals('Intel(R) Core(TM) i5 CPU       M 560  @ 2.67GHz',
                          info['cpu'])
        self.assertEquals(6114058240, info['memory'])

    def test_hoststats(self):
        resp = self.request('/host/stats').read()
        stats = json.loads(resp)
        cpu_utilization = stats['cpu_utilization']
        self.assertIsInstance(cpu_utilization, float)
        self.assertGreaterEqual(cpu_utilization, 0.0)
        self.assertTrue(cpu_utilization <= 100.0)

        memory_stats = stats['memory']
        self.assertIn('total', memory_stats)
        self.assertIn('free', memory_stats)
        self.assertIn('cached', memory_stats)
        self.assertIn('buffers', memory_stats)
        self.assertIn('avail', memory_stats)

        self.assertIn('disk_read_rate', stats)
        self.assertIn('disk_write_rate', stats)

        self.assertIn('net_recv_rate', stats)
        self.assertIn('net_sent_rate', stats)

    def test_packages_update(self):
        resp = self.request('/host/packagesupdate', None, 'GET')
        pkgs = json.loads(resp.read())
        self.assertEquals(3, len(pkgs))

        for p in pkgs:
            name = p['package_name']
            resp = self.request('/host/packagesupdate/' + name, None, 'GET')
            info = json.loads(resp.read())
            self.assertIn('package_name', info.keys())
            self.assertIn('repository', info.keys())
            self.assertIn('arch', info.keys())
            self.assertIn('version', info.keys())

        resp = self.request('/host/swupdate', '{}', 'POST')
        task = json.loads(resp.read())
        task_params = [u'id', u'message', u'status', u'target_uri']
        self.assertEquals(sorted(task_params), sorted(task.keys()))

        resp = self.request('/tasks/' + task[u'id'], None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'running')
        time.sleep(6)
        resp = self.request('/tasks/' + task[u'id'], None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'finished')
        self.assertIn(u'All packages updated', task_info['message'])

    def test_get_param(self):
        req = json.dumps({'name': 'test', 'cdrom': '/nonexistent.iso'})
        self.request('/templates', req, 'POST')

        # Create a VM
        req = json.dumps({'name': 'test-vm1', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)
        req = json.dumps({'name': 'test-vm2', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(201, resp.status)

        resp = request(host, port, '/vms')
        self.assertEquals(200, resp.status)
        res = json.loads(resp.read())
        self.assertEquals(2, len(res))

        resp = request(host, port, '/vms?name=test-vm1')
        self.assertEquals(200, resp.status)
        res = json.loads(resp.read())
        self.assertEquals(1, len(res))
        self.assertEquals('test-vm1', res[0]['name'])

    def test_repositories(self):
        def verify_repo(t, res):
            for field in ('repo_id', 'repo_name', 'baseurl', 'is_mirror',
                          'url_args', 'enabled', 'gpgcheck', 'gpgkey'):
                if field in t.keys():
                    self.assertEquals(t[field], res[field])

        base_uri = '/host/repositories'
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

        # Verify the repositorie
        res = json.loads(self.request('%s/fedora-fake' % base_uri).read())
        verify_repo(repo, res)

        # Update the repository
        repo['baseurl'] = 'http://www.fedora.org/update'
        req = json.dumps(repo)
        resp = self.request('%s/fedora-fake' % base_uri, req, 'PUT')

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
        self.request = partial(https_request, host, ssl_port)
        model.reset()
