# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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
import re
import time
import unittest
import urllib2
import urlparse

from functools import partial

import iso_gen
import kimchi.mockmodel
import kimchi.server
from kimchi.osinfo import get_template_default
from kimchi.rollbackcontext import RollbackContext
from kimchi.utils import add_task
from utils import get_free_port, patch_auth, request
from utils import run_server, wait_task


test_server = None
model = None
host = None
port = None
ssl_port = None
cherrypy_port = None
fake_iso = '/tmp/fake.iso'


def setUpModule():
    global test_server, model, host, port, ssl_port, cherrypy_port

    patch_auth()
    model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)

    # Create fake ISO to do the tests
    iso_gen.construct_fake_iso(fake_iso, True, '12.04', 'ubuntu')
    iso_gen.construct_fake_iso("/var/lib/libvirt/images/fedora.iso", True,
                               "17", "fedora")


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')
    os.unlink(fake_iso)
    os.unlink("/var/lib/libvirt/images/fedora.iso")


class RestTests(unittest.TestCase):
    def _async_op(self, cb, opaque):
        time.sleep(1)
        cb('success', True)

    def _except_op(self, cb, opaque):
        time.sleep(1)
        raise Exception("Oops, this is an exception handle test."
                        " You can ignore it safely")
        cb('success', True)

    def _intermid_op(self, cb, opaque):
        time.sleep(1)
        cb('in progress')

    def setUp(self):
        self.request = partial(request, host, ssl_port)
        model.reset()

    def assertHTTPStatus(self, code, *args):
        resp = self.request(*args)
        self.assertEquals(code, resp.status)

    def test_get_vms(self):
        vms = json.loads(self.request('/vms').read())
        # test_rest.py uses MockModel() which connects to libvirt URI
        # test:///default. By default this driver already has one VM created
        self.assertEquals(1, len(vms))

        # Create a template as a base for our VMs
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        test_users = ['root']
        test_groups = ['wheel']
        # Now add a couple of VMs to the mock model
        for i in xrange(10):
            name = 'vm-%i' % i
            req = json.dumps({'name': name, 'template': '/templates/test',
                             'users': test_users, 'groups': test_groups})
            resp = self.request('/vms', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])

        vms = json.loads(self.request('/vms').read())
        self.assertEquals(11, len(vms))

        vm = json.loads(self.request('/vms/vm-1').read())
        self.assertEquals('vm-1', vm['name'])
        self.assertEquals('shutoff', vm['state'])
        self.assertEquals([], vm['users'])
        self.assertEquals([], vm['groups'])

    def test_edit_vm(self):
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        req = json.dumps({'name': 'vm-1', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        vm = json.loads(self.request('/vms/vm-1').read())
        self.assertEquals('vm-1', vm['name'])

        resp = self.request('/vms/vm-1/start', '{}', 'POST')
        self.assertEquals(200, resp.status)

        req = json.dumps({'unsupported-attr': 'attr'})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'name': 'new-vm'})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'cpus': 3})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(200, resp.status)

        # Check if there is support to memory hotplug, once vm is running
        resp = self.request('/config/capabilities').read()
        conf = json.loads(resp)
        req = json.dumps({'memory': 2048})
        resp = self.request('/vms/vm-1', req, 'PUT')
        if conf['mem_hotplug_support']:
            self.assertEquals(200, resp.status)
        else:
            self.assertEquals(400, resp.status)

        req = json.dumps({"graphics": {'passwd': "abcdef"}})
        resp = self.request('/vms/vm-1', req, 'PUT')
        info = json.loads(resp.read())
        self.assertEquals('abcdef', info["graphics"]["passwd"])
        self.assertEquals(None, info["graphics"]["passwdValidTo"])

        resp = self.request('/vms/vm-1/poweroff', '{}', 'POST')
        self.assertEquals(200, resp.status)

        req = json.dumps({"graphics": {'passwd': "123456",
                                       'passwdValidTo': 20}})
        resp = self.request('/vms/vm-1', req, 'PUT')
        info = json.loads(resp.read())
        self.assertEquals('123456', info["graphics"]["passwd"])
        self.assertGreaterEqual(20, info["graphics"]["passwdValidTo"])

        req = json.dumps({'name': 12})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'name': ''})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'cpus': -2})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'cpus': 'four'})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'memory': 100})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'memory': 'ten gigas'})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        req = json.dumps({'name': 'new-name', 'cpus': 5, 'UUID': 'notallowed'})
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(400, resp.status)

        params = {'name': u'∨м-црdαtеd', 'cpus': 5, 'memory': 3072}
        req = json.dumps(params)
        resp = self.request('/vms/vm-1', req, 'PUT')
        self.assertEquals(303, resp.status)
        vm = json.loads(self.request('/vms/∨м-црdαtеd', req).read())
        for key in params.keys():
            self.assertEquals(params[key], vm[key])

        # change only VM users - groups are not changed (default is empty)
        resp = self.request('/users', '{}', 'GET')
        users = json.loads(resp.read())
        req = json.dumps({'users': users})
        resp = self.request('/vms/∨м-црdαtеd', req, 'PUT')
        self.assertEquals(200, resp.status)
        info = json.loads(self.request('/vms/∨м-црdαtеd', '{}').read())
        self.assertEquals(users, info['users'])

        # change only VM groups - users are not changed (default is empty)
        resp = self.request('/groups', '{}', 'GET')
        groups = json.loads(resp.read())
        req = json.dumps({'groups': groups})
        resp = self.request('/vms/∨м-црdαtеd', req, 'PUT')
        self.assertEquals(200, resp.status)
        info = json.loads(self.request('/vms/∨м-црdαtеd', '{}').read())
        self.assertEquals(groups, info['groups'])

        # change VM users (wrong value) and groups
        # when an error occurs, everything fails and nothing is changed
        req = json.dumps({'users': ['userdoesnotexist'], 'groups': []})
        resp = self.request('/vms/∨м-црdαtеd', req, 'PUT')
        self.assertEquals(400, resp.status)

        # change VM users and groups (wrong value)
        # when an error occurs, everything fails and nothing is changed
        req = json.dumps({'users': [], 'groups': ['groupdoesnotexist']})
        resp = self.request('/vms/∨м-црdαtеd', req, 'PUT')
        self.assertEquals(400, resp.status)

    def test_vm_lifecycle(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'disks': [{'size': 1}],
                          'icon': 'images/icon-debian.png',
                          'cdrom': fake_iso})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create a VM
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        self.assertEquals(202, resp.status)

        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('shutoff', vm['state'])
        self.assertEquals('images/icon-debian.png', vm['icon'])

        # Verify the volume was created
        vol_uri = '/storagepools/default-pool/storagevolumes/%s-0.img'
        resp = self.request(vol_uri % vm['uuid'])
        vol = json.loads(resp.read())
        self.assertEquals(1 << 30, vol['capacity'])
        self.assertEquals(['test-vm'], vol['used_by'])

        # Start the VM
        resp = self.request('/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('running', vm['state'])

        # Test screenshot
        resp = self.request(vm['screenshot'], method='HEAD')
        self.assertEquals(200, resp.status)
        self.assertTrue(resp.getheader('Content-type').startswith('image'))

        # Clone a running VM
        resp = self.request('/vms/test-vm/clone', '{}', 'POST')
        self.assertEquals(400, resp.status)

        # Force poweroff the VM
        resp = self.request('/vms/test-vm/poweroff', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('shutoff', vm['state'])

        # Test create VM with same name fails with 400
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(400, resp.status)

        # Clone a VM
        resp = self.request('/vms/test-vm/clone', '{}', 'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        task = json.loads(self.request('/tasks/%s' % task['id'], '{}').read())
        self.assertEquals('finished', task['status'])
        clone_vm_name = task['target_uri'].split('/')[-2]
        self.assertTrue(re.match(u'test-vm-clone-\d+', clone_vm_name))

        resp = self.request('/vms/test-vm', '{}')
        original_vm_info = json.loads(resp.read())
        resp = self.request('/vms/%s' % clone_vm_name, '{}')
        self.assertEquals(200, resp.status)
        clone_vm_info = json.loads(resp.read())

        self.assertNotEqual(original_vm_info['name'], clone_vm_info['name'])
        del original_vm_info['name']
        del clone_vm_info['name']

        self.assertNotEqual(original_vm_info['uuid'], clone_vm_info['uuid'])
        del original_vm_info['uuid']
        del clone_vm_info['uuid']

        self.assertEquals(original_vm_info, clone_vm_info)

        # Create a snapshot on a stopped VM
        params = {'name': 'test-snap'}
        resp = self.request('/vms/test-vm/snapshots', json.dumps(params),
                            'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        task = json.loads(self.request('/tasks/%s' % task['id']).read())
        self.assertEquals('finished', task['status'])

        # Look up a non-existing snapshot
        resp = self.request('/vms/test-vm/snapshots/snap404', '{}', 'GET')
        self.assertEquals(404, resp.status)

        # Look up a snapshot
        resp = self.request('/vms/test-vm/snapshots/%s' % params['name'], '{}',
                            'GET')
        self.assertEquals(200, resp.status)
        snap = json.loads(resp.read())
        self.assertTrue(int(time.time()) >= int(snap['created']))
        self.assertEquals(params['name'], snap['name'])
        self.assertEquals(u'', snap['parent'])
        self.assertEquals(u'shutoff', snap['state'])

        resp = self.request('/vms/test-vm/snapshots', '{}', 'GET')
        self.assertEquals(200, resp.status)
        snaps = json.loads(resp.read())
        self.assertEquals(1, len(snaps))

        # Look up current snapshot (the one created above)
        resp = self.request('/vms/test-vm/snapshots/current', '{}', 'GET')
        self.assertEquals(200, resp.status)
        snap = json.loads(resp.read())
        self.assertEquals(params['name'], snap['name'])

        resp = self.request('/vms/test-vm/snapshots', '{}', 'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        snap_name = task['target_uri'].split('/')[-1]
        wait_task(self._task_lookup, task['id'])
        resp = self.request('/tasks/%s' % task['id'], '{}', 'GET')
        task = json.loads(resp.read())
        self.assertEquals('finished', task['status'])

        resp = self.request('/vms/test-vm/snapshots', '{}', 'GET')
        self.assertEquals(200, resp.status)
        snaps = json.loads(resp.read())
        self.assertEquals(2, len(snaps))

        # Look up current snapshot (the one created above)
        resp = self.request('/vms/test-vm/snapshots/current', '{}', 'GET')
        self.assertEquals(200, resp.status)
        snap = json.loads(resp.read())
        self.assertEquals(snap_name, snap['name'])

        # Revert to snapshot
        resp = self.request('/vms/test-vm/snapshots/%s/revert' %
                            params['name'], '{}', 'POST')
        self.assertEquals(200, resp.status)
        snap = json.loads(resp.read())
        resp = self.request('/vms/test-vm', '{}', 'GET')
        self.assertEquals(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEquals(vm['state'], snap['state'])
        resp = self.request('/vms/test-vm/snapshots/current', '{}', 'GET')
        self.assertEquals(200, resp.status)
        current_snap = json.loads(resp.read())
        self.assertEquals(snap, current_snap)

        # Delete a snapshot
        resp = self.request('/vms/test-vm/snapshots/%s' % params['name'],
                            '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Suspend the VM
        resp = self.request('/vms/test-vm', '{}', 'GET')
        self.assertEquals(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEquals(vm['state'], 'shutoff')
        resp = self.request('/vms/test-vm/suspend', '{}', 'POST')
        self.assertEquals(400, resp.status)
        resp = self.request('/vms/test-vm/start', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/vms/test-vm', '{}', 'GET')
        self.assertEquals(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEquals(vm['state'], 'running')
        resp = self.request('/vms/test-vm/suspend', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/vms/test-vm', '{}', 'GET')
        self.assertEquals(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEquals(vm['state'], 'paused')

        # Resume the VM
        resp = self.request('/vms/test-vm/resume', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/vms/test-vm', '{}', 'GET')
        self.assertEquals(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEquals(vm['state'], 'running')

        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Delete the Template
        resp = self.request('/templates/test', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Verify the volume was deleted
        self.assertHTTPStatus(404, vol_uri % vm['uuid'])

    def test_vm_graphics(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create a VM with default args
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('127.0.0.1', vm['graphics']['listen'])
        self.assertEquals('vnc', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Create a VM with specified graphics type and listen
        graphics = {'type': 'vnc', 'listen': '127.0.0.1'}
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test',
                          'graphics': graphics})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
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
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
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
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        # Verify the VM
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('127.0.0.1', vm['graphics']['listen'])
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
            req = json.dumps({'name': 'test', 'cdrom': fake_iso})
            resp = self.request('/templates', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the template
            rollback.prependDefer(self.request,
                                  '/templates/test', '{}', 'DELETE')

            # Create a VM with default args
            req = json.dumps({'name': 'test-vm',
                              'template': '/templates/test'})
            resp = self.request('/vms', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
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

            # Create temp storage pool
            req = json.dumps({'name': 'tmp',
                              'capacity': 1024,
                              'allocated': 512,
                              'path': '/tmp',
                              'type': 'dir'})
            resp = self.request('/storagepools', req, 'POST')
            self.assertEquals(201, resp.status)
            resp = self.request('/storagepools/tmp/activate', req, 'POST')
            self.assertEquals(200, resp.status)

            # 'name' is required for this type of volume
            req = json.dumps({'capacity': 1024,
                              'allocation': 512,
                              'type': 'disk',
                              'format': 'raw'})
            resp = self.request('/storagepools/tmp/storagevolumes',
                                req, 'POST')
            self.assertEquals(400, resp.status)
            req = json.dumps({'name': "attach-volume",
                              'capacity': 1024,
                              'allocation': 512,
                              'type': 'disk',
                              'format': 'raw'})
            resp = self.request('/storagepools/tmp/storagevolumes',
                                req, 'POST')
            self.assertEquals(202, resp.status)
            time.sleep(1)

            # Attach cdrom with both path and volume specified
            open('/tmp/existent.iso', 'w').close()
            req = json.dumps({'dev': 'hdx',
                              'type': 'cdrom',
                              'pool': 'tmp',
                              'vol': 'attach-volume',
                              'path': '/tmp/existent.iso'})
            resp = self.request('/vms/test-vm/storages', req, 'POST')
            self.assertEquals(400, resp.status)

            # Attach disk with both path and volume specified
            req = json.dumps({'dev': 'hdx',
                              'type': 'disk',
                              'pool': 'tmp',
                              'vol': 'attach-volume',
                              'path': '/tmp/existent.iso'})
            resp = self.request('/vms/test-vm/storages', req, 'POST')
            self.assertEquals(400, resp.status)

            # Attach disk with only pool specified
            req = json.dumps({'dev': 'hdx',
                              'type': 'cdrom',
                              'pool': 'tmp'})
            resp = self.request('/vms/test-vm/storages', req, 'POST')
            self.assertEquals(400, resp.status)

            # Attach disk with pool and vol specified
            req = json.dumps({'type': 'disk',
                              'pool': 'tmp',
                              'vol': 'attach-volume'})
            resp = self.request('/vms/test-vm/storages', req, 'POST')
            self.assertEquals(201, resp.status)
            cd_info = json.loads(resp.read())
            self.assertEquals('disk', cd_info['type'])

            # Attach a cdrom with existent dev name
            req = json.dumps({'type': 'cdrom',
                              'path': '/tmp/existent.iso'})
            resp = self.request('/vms/test-vm/storages', req, 'POST')
            self.assertEquals(201, resp.status)
            cd_info = json.loads(resp.read())
            cd_dev = cd_info['dev']
            self.assertEquals('cdrom', cd_info['type'])
            self.assertEquals('/tmp/existent.iso', cd_info['path'])
            # Delete the file and cdrom
            rollback.prependDefer(self.request,
                                  '/vms/test-vm/storages/hdx', '{}', 'DELETE')
            os.remove('/tmp/existent.iso')

            # Change path of storage cdrom
            cdrom = u'http://fedora.mirrors.tds.net/pub/fedora/releases/20/'\
                    'Live/x86_64/Fedora-Live-Desktop-x86_64-20-1.iso'
            req = json.dumps({'path': cdrom})
            resp = self.request('/vms/test-vm/storages/' + cd_dev, req, 'PUT')
            self.assertEquals(200, resp.status)
            cd_info = json.loads(resp.read())
            self.assertEquals(urlparse.urlparse(cdrom).path,
                              urlparse.urlparse(cd_info['path']).path)

            # Test GET
            devs = json.loads(self.request('/vms/test-vm/storages').read())
            self.assertEquals(4, len(devs))

            # Detach storage cdrom
            resp = self.request('/vms/test-vm/storages/' + cd_dev,
                                '{}', 'DELETE')
            self.assertEquals(204, resp.status)

            # Test GET
            devs = json.loads(self.request('/vms/test-vm/storages').read())
            self.assertEquals(3, len(devs))
            resp = self.request('/storagepools/tmp/deactivate', {}, 'POST')
            self.assertEquals(200, resp.status)
            resp = self.request('/storagepools/tmp', {}, 'DELETE')
            self.assertEquals(204, resp.status)

    def test_vm_iface(self):

        with RollbackContext() as rollback:
            # Create a template as a base for our VMs
            req = json.dumps({'name': 'test', 'cdrom': fake_iso})
            resp = self.request('/templates', req, 'POST')
            self.assertEquals(201, resp.status)
            # Delete the template
            rollback.prependDefer(self.request,
                                  '/templates/test', '{}', 'DELETE')

            # Create a VM with default args
            req = json.dumps({'name': 'test-vm',
                              'template': '/templates/test'})
            resp = self.request('/vms', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
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
                self.assertEquals(get_template_default('old', 'nic_model'),
                                  res['model'])

            # try to attach an interface without specifying 'model'
            req = json.dumps({'type': 'network'})
            resp = self.request('/vms/test-vm/ifaces', req, 'POST')
            self.assertEquals(400, resp.status)

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

            # update vm interface
            newMacAddr = '54:50:e3:44:8a:af'
            req = json.dumps({"network": "default", "model": "virtio",
                             "type": "network", "mac": newMacAddr})
            resp = self.request('/vms/test-vm/ifaces/%s' % iface['mac'],
                                req, 'PUT')
            self.assertEquals(303, resp.status)
            iface = json.loads(self.request('/vms/test-vm/ifaces/%s' %
                                            newMacAddr).read())
            self.assertEquals(newMacAddr, iface['mac'])

            # detach network interface from vm
            resp = self.request('/vms/test-vm/ifaces/%s' % iface['mac'],
                                '{}', 'DELETE')
            self.assertEquals(204, resp.status)

    def test_vm_customise_storage(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'cdrom': fake_iso,
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
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        resp = self.request('/vms/test-vm', {}, 'GET')
        vm_info = json.loads(resp.read())

        # Test template not changed after vm customise its pool
        t = json.loads(self.request('/templates/test').read())
        self.assertEquals(t['storagepool'], '/storagepools/default-pool')

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
                          'source': {'adapter_name': 'scsi_host2'}})
        resp = self.request('/storagepools', req, 'POST')
        self.assertEquals(201, resp.status)

        # Test create vms using lun of this pool
        # activate the storage pool
        resp = self.request('/storagepools/scsi_fc_pool/activate', '{}',
                            'POST')

        # Create template fails because SCSI volume is missing
        tmpl_params = {'name': 'test_fc_pool', 'cdrom': fake_iso,
                       'storagepool': '/storagepools/scsi_fc_pool'}
        req = json.dumps(tmpl_params)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(400, resp.status)

        # Choose SCSI volume to create template
        resp = self.request('/storagepools/scsi_fc_pool/storagevolumes')
        lun_name = json.loads(resp.read())[0]['name']

        tmpl_params['disks'] = [{'index': 0, 'volume': lun_name}]
        req = json.dumps(tmpl_params)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create vm in scsi pool
        req = json.dumps({'name': 'test-vm',
                          'template': '/templates/test_fc_pool'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        # Start the VM
        resp = self.request('/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('running', vm['state'])

        # Force poweroff the VM
        resp = self.request('/vms/test-vm/poweroff', '{}', 'POST')
        vm = json.loads(self.request('/vms/test-vm').read())
        self.assertEquals('shutoff', vm['state'])

        # Delete the VM
        resp = self.request('/vms/test-vm', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

    def test_unnamed_vms(self):
        # Create a Template
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create 5 unnamed vms from this template
        for i in xrange(1, 6):
            req = json.dumps({'template': '/templates/test'})
            task = json.loads(self.request('/vms', req, 'POST').read())
            wait_task(self._task_lookup, task['id'])
            resp = self.request('/vms/test-vm-%i' % i, {}, 'GET')
            self.assertEquals(resp.status, 200)
        count = len(json.loads(self.request('/vms').read()))
        self.assertEquals(6, count)

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

    def test_create_vm_with_img_based_template(self):
        resp = json.loads(
            self.request('/storagepools/default-pool/storagevolumes').read())
        self.assertEquals(0, len(resp))

        # Create a Template
        mock_base = '/tmp/mock.img'
        open(mock_base, 'w').close()
        req = json.dumps({'name': 'test', 'disks': [{'base': mock_base}]})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        req = json.dumps({'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        self.assertEquals(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        # Test storage volume created with backing store of base file
        resp = json.loads(
            self.request('/storagepools/default-pool/storagevolumes').read())
        self.assertEquals(1, len(resp))

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

    def test_iso_scan_shallow(self):
        # fake environment preparation
        self._create_pool('pool-3')
        self.request('/storagepools/pool-3/activate', '{}', 'POST')
        params = {'name': 'fedora.iso',
                  'capacity': 1073741824,  # 1 GiB
                  'type': 'file',
                  'format': 'iso'}
        task_info = model.storagevolumes_create('pool-3', params)
        wait_task(self._task_lookup, task_info['id'])

        storagevolume = json.loads(self.request(
            '/storagepools/kimchi_isos/storagevolumes/').read())[0]
        self.assertEquals('fedora.iso', storagevolume['name'])
        self.assertEquals('iso', storagevolume['format'])
        self.assertEquals('/var/lib/libvirt/images/fedora.iso',
                          storagevolume['path'])
        self.assertEquals(1073741824, storagevolume['capacity'])  # 1 GiB
        self.assertEquals(0, storagevolume['allocation'])
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
        self.assertEquals(get_template_default('old', 'memory'), t['memory'])

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

        resp = self.request('/storagepools/pool-3/deactivate', '{}', 'POST')
        self.assertEquals(200, resp.status)
        self._delete_pool('pool-3')

    def test_screenshot_refresh(self):
        # Create a VM
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        resp = self.request('/templates', req, 'POST')
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = self.request('/vms', req, 'POST')
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        # Test screenshot for shut-off state vm
        resp = self.request('/vms/test-vm/screenshot')
        self.assertEquals(404, resp.status)

        # Test screenshot for running vm
        resp = self.request('/vms/test-vm/start', '{}', 'POST')
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
        self.request('/vms/test-vm/poweroff', '{}', 'POST')
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
        keys = ['name', 'type', 'ipaddr', 'netmask', 'status']
        for interface in interfaces:
            self.assertEquals(sorted(keys), sorted(interface.keys()))

    def _task_lookup(self, taskid):
        return json.loads(self.request('/tasks/%s' % taskid).read())

    def test_tasks(self):
        id1 = add_task('/tasks/1', self._async_op, model.objstore)
        id2 = add_task('/tasks/2', self._except_op, model.objstore)
        id3 = add_task('/tasks/3', self._intermid_op, model.objstore)

        target_uri = urllib2.quote('^/tasks/*', safe="")
        filter_data = 'status=running&target_uri=%s' % target_uri
        tasks = json.loads(self.request('/tasks?%s' % filter_data).read())
        self.assertEquals(3, len(tasks))

        tasks = json.loads(self.request('/tasks').read())
        tasks_ids = [int(t['id']) for t in tasks]
        self.assertEquals(set([id1, id2, id3]) - set(tasks_ids), set([]))
        wait_task(self._task_lookup, id2)
        foo2 = json.loads(self.request('/tasks/%s' % id2).read())
        keys = ['id', 'status', 'message', 'target_uri']
        self.assertEquals(sorted(keys), sorted(foo2.keys()))
        self.assertEquals('failed', foo2['status'])
        wait_task(self._task_lookup, id3)
        foo3 = json.loads(self.request('/tasks/%s' % id3).read())
        self.assertEquals('in progress', foo3['message'])
        self.assertEquals('running', foo3['status'])

    def test_config(self):
        resp = self.request('/config').read()
        conf = json.loads(resp)
        keys = ["display_proxy_port", "version"]
        self.assertEquals(keys, sorted(conf.keys()))

    def test_capabilities(self):
        resp = self.request('/config/capabilities').read()
        conf = json.loads(resp)

        keys = [u'libvirt_stream_protocols', u'qemu_stream', u'qemu_spice',
                u'screenshot', u'system_report_tool', u'update_tool',
                u'repo_mngt_tool', u'federation', u'kernel_vfio', u'auth',
                u'nm_running', u'mem_hotplug_support']
        self.assertEquals(sorted(keys), sorted(conf.keys()))

    def test_peers(self):
        resp = self.request('/peers').read()
        self.assertEquals([], json.loads(resp))

    def test_distros(self):
        resp = self.request('/config/distros').read()
        distros = json.loads(resp)
        for distro in distros:
            self.assertIn('name', distro)
            self.assertIn('os_distro', distro)
            self.assertIn('os_version', distro)
            self.assertIn('path', distro)

        # Test in X86
        ident = "Fedora 20"
        resp = self.request('/config/distros/%s' % urllib2.quote(ident)).read()
        distro = json.loads(resp)
        if os.uname()[4] in ['x86_64', 'amd64']:
            self.assertEquals(distro['name'], ident)
            self.assertEquals(distro['os_distro'], "fedora")
            self.assertEquals(distro['os_version'], "20")
            self.assertEquals(distro['os_arch'], "x86_64")
            self.assertIn('path', distro)
        else:
            # Distro not found error
            self.assertIn('KCHDISTRO0001E', distro.get('reason'))

        # Test in PPC
        ident = "Fedora 20 (PPC64)"
        resp = self.request('/config/distros/%s' % urllib2.quote(ident)).read()
        distro = json.loads(resp)
        if os.uname()[4] == 'ppc64':
            self.assertEquals(distro['name'], ident)
            self.assertEquals(distro['os_distro'], "fedora")
            self.assertEquals(distro['os_version'], "20")
            self.assertEquals(distro['os_arch'], "ppc64")
            self.assertIn('path', distro)
        else:
            # Distro not found error
            self.assertIn('KCHDISTRO0001E', distro.get('reason'))

    def test_debugreports(self):
        resp = request(host, ssl_port, '/debugreports')
        self.assertEquals(200, resp.status)

    def _report_delete(self, name):
        request(host, ssl_port, '/debugreports/%s' % name, '{}', 'DELETE')

    def test_create_debugreport(self):
        req = json.dumps({'name': 'report1'})
        with RollbackContext() as rollback:
            resp = request(host, ssl_port, '/debugreports', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            wait_task(self._task_lookup, task['id'])
            rollback.prependDefer(self._report_delete, 'report2')
            resp = request(host, ssl_port, '/debugreports/report1')
            debugreport = json.loads(resp.read())
            self.assertEquals("report1", debugreport['name'])
            self.assertEquals(200, resp.status)
            req = json.dumps({'name': 'report2'})
            resp = request(host, ssl_port, '/debugreports/report1',
                           req, 'PUT')
            self.assertEquals(303, resp.status)

    def test_debugreport_download(self):
        req = json.dumps({'name': 'report1'})
        with RollbackContext() as rollback:
            resp = request(host, ssl_port, '/debugreports', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            wait_task(self._task_lookup, task['id'], 20)
            rollback.prependDefer(self._report_delete, 'report1')
            resp = request(host, ssl_port, '/debugreports/report1')
            debugreport = json.loads(resp.read())
            self.assertEquals("report1", debugreport['name'])
            self.assertEquals(200, resp.status)
            resp = request(host, ssl_port, '/debugreports/report1/content')
            self.assertEquals(200, resp.status)
            resp = request(host, ssl_port, '/debugreports/report1')
            debugre = json.loads(resp.read())
            resp = request(host, ssl_port, debugre['uri'])
            self.assertEquals(200, resp.status)

    def test_repositories(self):
        def verify_repo(t, res):
            for field in ('repo_id', 'enabled', 'baseurl', 'config'):
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

        # Verify the repository
        res = json.loads(self.request('%s/fedora-fake' % base_uri).read())
        verify_repo(repo, res)

        # Update the repository
        params = {}
        params['baseurl'] = repo['baseurl'] = 'http://www.fedoraproject.org'
        resp = self.request('%s/fedora-fake' % base_uri, json.dumps(params),
                            'PUT')

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
        self.request = partial(request, host, ssl_port)
        model.reset()
