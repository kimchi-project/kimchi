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
import json
import time
import os
from functools import partial

import kimchi.mockmodel
import kimchi.server
from utils import *
from kimchi.asynctask import AsyncTask

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

        resp = self.request("/",
                       headers={'Accept': 'application/json, text/html'})
        self.assertValidJSON(resp.read())

        resp = self.request("/",
                       headers={'Accept': 'text/html, application/json'})
        self.assertValidJSON(resp.read())

        h = {'Accept': 'text/plain'}
        self.assertHTTPStatus(406, "/", None, 'GET', h)

    def test_get_vms(self):
        vms = json.loads(self.request('/vms').read())
        self.assertEquals(0, len(vms))

        # Create a template as a base for our VMs
        req = json.dumps({'name': 'test'})
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

    def test_vm_lifecycle(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'disks': [{'size': 1}],
                          'icon': 'images/icon-debian.png'})
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

        # Verify the volume was deleted
        self.assertHTTPStatus(404, vol_uri)

    def test_vm_customise_storage(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'disks': [{'size': 1}]})
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

    def test_template_customise_storage(self):
        req = json.dumps({'name': 'test',
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

    def test_unnamed_vms(self):
        # Create a Template
        req = json.dumps({'name': 'test'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create 5 unnamed vms from this template
        for i in xrange(1, 6):
            req = json.dumps({'template': '/templates/test'})
            vm = json.loads(self.request('/vms', req, 'POST').read())
            self.assertEquals('test-vm-%i' % i, vm['name'])
        count = len(json.loads(self.request('/vms').read()))
        self.assertEquals(5, count)

    def test_get_storagepools(self):
        storagepools = json.loads(self.request('/storagepools').read())
        self.assertEquals(2, len(storagepools))
        self.assertEquals('default', storagepools[0]['name'])
        self.assertEquals('active', storagepools[0]['state'])
        self.assertEquals('kimchi_isos', storagepools[1]['name'])
        self.assertEquals('kimchi-iso', storagepools[1]['type'])

        # Now add a couple of StoragePools to the mock model
        for i in xrange(5):
            name = 'storagepool-%i' % i
            req = json.dumps({'name': name,
                              'capacity': 1024,
                              'allocated': 512,
                              'path': '/var/lib/libvirt/images/%i' % i,
                              'type': 'dir'})
            resp = self.request('/storagepools', req, 'POST')
            self.assertEquals(201, resp.status)

        req = json.dumps({'name': 'storagepool-1',
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

        resp = self.request('/storagepools/storagepool-1')
        storagepool = json.loads(resp.read())
        self.assertEquals('storagepool-1', storagepool['name'])
        self.assertEquals('inactive', storagepool['state'])

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
        storagepool = json.loads(self.request('/storagepools/test-pool').read())
        self.assertEquals('inactive', storagepool['state'])
        if storagepool['type'] == 'dir':
            self.assertEquals(True, storagepool['autostart'])
        else:
            self.assertEquals(False, storagepool['autostart'])

        # activate the storage pool
        resp = self.request('/storagepools/test-pool/activate', '{}', 'POST')
        storagepool = json.loads(self.request('/storagepools/test-pool').read())
        self.assertEquals('active', storagepool['state'])

        # Deactivate the storage pool
        resp = self.request('/storagepools/test-pool/deactivate', '{}', 'POST')
        storagepool = json.loads(self.request('/storagepools/test-pool').read())
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
        nr_vols = json.loads(self.request('/storagepools/pool-1').read())['nr_volumes']
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

        nr_vols = json.loads(self.request('/storagepools/pool-1').read())['nr_volumes']
        self.assertEquals(5, nr_vols)
        resp = self.request('/storagepools/pool-1/storagevolumes')
        storagevolumes = json.loads(resp.read())
        self.assertEquals(5, len(storagevolumes))

        resp = self.request('/storagepools/pool-1/storagevolumes/volume-1')
        storagevolume = json.loads(resp.read())
        self.assertEquals('volume-1', storagevolume['name'])
        self.assertEquals('raw', storagevolume['format'])
        self.assertEquals('/var/lib/libvirt/images/volume-1', storagevolume['path'])

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
        resp = self.request('/storagepools/pool-2/storagevolumes/', req, 'POST')
        self.assertEquals(400, resp.status)
        resp = self.request('/storagepools/pool-2/activate', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/storagepools/pool-2/storagevolumes/', req, 'POST')
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
        storagepool = json.loads(self.request('/storagepools/%s' % name).read())
        self.assertEquals('inactive', storagepool['state'])
        return name

    def _delete_pool(self, name):
        # Delete the storage pool
        resp = self.request('/storagepools/%s' % name, '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_templates(self):
        def verify_template(t, res):
            for field in ('name', 'os_distro',
                    'os_version', 'memory', 'cpus', 'storagepool'):
                self.assertEquals(t[field], res[field])

        resp = self.request('/templates')
        self.assertEquals(200, resp.status)
        self.assertEquals(0, len(json.loads(resp.read())))

        # Create a template
        t = {'name': 'test', 'os_distro': 'ImagineOS',
             'os_version': '1.0', 'memory': '1024', 'cpus': '1',
             'storagepool': '/storagepools/alt'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/test').read())
        verify_template(t, res)

        # Create a template with same name fails with 400
        t = {'name': 'test', 'os_distro': 'ImagineOS',
             'os_version': '1.0', 'memory': '1024', 'cpus': '1',
             'storagepool': '/storagepools/default'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(400, resp.status)

        # Update the template
        t['os_distro'] = 'Linux.ISO'
        t['os_version'] = '1.1'
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

        # Try to clean up template cpus value
        t['cpus'] = '    '
        req = json.dumps(t)
        resp = self.request('/templates/%s' % tmpl_name, req, 'PUT')
        self.assertEquals(400, resp.status)

        # Test unallowed fields, specify a field 'foo' isn't in the Template
        t['foo'] = "bar"
        req = json.dumps(t)
        resp = self.request('/templates/%s' % oldname, req, 'PUT')
        self.assertEquals(405, resp.status)

        # Delete the template
        resp = self.request('/templates/%s' % tmpl_name, '{}', 'DELETE')
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
        self.assertEquals('/var/lib/libvirt/images/fedora.iso',storagevolume['path'])
        self.assertEquals(1024 << 20, storagevolume['capacity'])
        self.assertEquals(1024 << 20, storagevolume['allocation'])
        self.assertEquals('17', storagevolume['os_version'])
        self.assertEquals('fedora',storagevolume['os_distro'])
        self.assertEquals(True,storagevolume['bootable'])

        # Create a template
        # In real model os distro/version can be omitted as we will scan the iso
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
        resp = self.request('/storagepools/kimchi_isos/storagevolumes/deactivate',
                            '{}', 'POST')
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
        req = json.dumps({'name': 'test'})
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
         resp = request(host, port, '/debugreports/%s' % name, '{}', 'DELETE')

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

    def test_hoststats(self):
        resp = self.request('/host/stats').read()
        stats = json.loads(resp)
        cpu_utilization = stats['cpu_utilization']
        self.assertIsInstance(cpu_utilization, float)
        self.assertGreaterEqual(cpu_utilization, 0.0)
        self.assertLessEqual(cpu_utilization, 100.0)

class HttpsRestTests(RestTests):
    """
    Run all of the same tests as above, but use https instead
    """
    def setUp(self):
        self.request = partial(https_request, host, ssl_port)
        model.reset()
