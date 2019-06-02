# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM Corp, 2013-2017
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
import urllib
from functools import partial

import cherrypy
import iso_gen
from wok.asynctask import AsyncTask
from wok.plugins.kimchi.osinfo import get_template_default
from wok.rollbackcontext import RollbackContext

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server
from tests.utils import wait_task


test_server = None
model = None
fake_iso = '/tmp/fake.iso'

DISKS = [
    {
        'size': 10,
        'format': 'qcow2',
        'index': 0,
        'pool': {'name': '/plugins/kimchi/storagepools/default-pool'},
    }
]


def setUpModule():
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=True)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model

    # Create fake ISO to do the tests
    iso_gen.construct_fake_iso(fake_iso, True, '12.04', 'ubuntu')
    iso_gen.construct_fake_iso(
        '/var/lib/libvirt/images/fedora.iso', True, '17', 'fedora'
    )


def tearDownModule():
    test_server.stop()
    os.unlink(fake_iso)
    os.unlink('/var/lib/libvirt/images/fedora.iso')


class RestTests(unittest.TestCase):
    def _async_op(self, cb, opaque):
        time.sleep(1)
        cb('success', True)

    def _except_op(self, cb, opaque):
        time.sleep(1)
        raise Exception(
            'Oops, this is an exception handle test.' ' You can ignore it safely'
        )
        cb('success', True)

    def _intermid_op(self, cb, opaque):
        time.sleep(1)
        cb('in progress')

    def setUp(self):
        self.request = partial(request)
        model.reset()

    def assertHTTPStatus(self, code, *args):
        resp = self.request(*args)
        self.assertEqual(code, resp.status)

    def test_get_vms(self):
        vms = json.loads(self.request('/plugins/kimchi/vms').read())
        # test_rest.py uses MockModel() which connects to libvirt URI
        # test:///default. By default this driver already has one VM created
        self.assertEqual(1, len(vms))

        # Create a template as a base for our VMs
        req = json.dumps(
            {'name': 'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        test_users = ['root']
        test_groups = ['wheel']
        # Now add a couple of VMs to the mock model
        for i in range(10):
            name = 'vm-%i' % i
            req = json.dumps(
                {
                    'name': name,
                    'template': '/plugins/kimchi/templates/test',
                    'users': test_users,
                    'groups': test_groups,
                }
            )
            resp = self.request('/plugins/kimchi/vms', req, 'POST')
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])

        vms = json.loads(self.request('/plugins/kimchi/vms').read())
        self.assertEqual(11, len(vms))

        vm = json.loads(self.request('/plugins/kimchi/vms/vm-1').read())
        self.assertEqual('vm-1', vm['name'])
        self.assertEqual('shutoff', vm['state'])
        self.assertEqual([], vm['users'])
        self.assertEqual([], vm['groups'])

    def test_edit_vm_cpuhotplug(self):
        req = json.dumps(
            {
                'name': 'template_cpuhotplug',
                'source_media': {'type': 'disk', 'path': fake_iso},
            }
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        req = json.dumps(
            {
                'name': 'vm-cpuhotplug',
                'template': '/plugins/kimchi/templates/template_cpuhotplug',
            }
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        req = json.dumps({'cpu_info': {'maxvcpus': 5, 'vcpus': 1}})
        resp = self.request('/plugins/kimchi/vms/vm-cpuhotplug', req, 'PUT')
        self.assertEqual(200, resp.status)

        resp = self.request(
            '/plugins/kimchi/vms/vm-cpuhotplug/start', '{}', 'POST')
        self.assertEqual(200, resp.status)

        req = json.dumps({'cpu_info': {'vcpus': 5}})
        resp = self.request('/plugins/kimchi/vms/vm-cpuhotplug', req, 'PUT')
        self.assertEqual(200, resp.status)

    def test_edit_vm(self):
        req = json.dumps(
            {'name': 'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        req = json.dumps(
            {'name': 'vm-1', 'template': '/plugins/kimchi/templates/test'})
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        vm = json.loads(self.request('/plugins/kimchi/vms/vm-1').read())
        self.assertEqual('vm-1', vm['name'])

        req = json.dumps({'cpu_info': {'maxvcpus': 5, 'vcpus': 3}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(200, resp.status)

        # Test max memory
        req = json.dumps({'memory': {'maxmemory': 23}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps({'memory': {'maxmemory': 'maxmem 80'}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        # Check if there is support to memory hotplug
        resp = self.request('/plugins/kimchi/config/capabilities').read()
        conf = json.loads(resp)
        if os.uname()[4] != 's390x' and conf['mem_hotplug_support']:
            req = json.dumps({'memory': {'maxmemory': 3072}})
            resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
            self.assertEqual(200, resp.status)

        resp = self.request('/plugins/kimchi/vms/vm-1/start', '{}', 'POST')
        self.assertEqual(200, resp.status)

        req = json.dumps({'unsupported-attr': 'attr'})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps({'name': 'new-vm'})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        # Test memory hotplug
        req = json.dumps({'memory': {'current': 2048}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        if conf['mem_hotplug_support']:
            self.assertEqual(200, resp.status)
        else:
            self.assertEqual(400, resp.status)

        req = json.dumps({'graphics': {'passwd': 'abcdef'}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(200, resp.status)
        info = json.loads(resp.read())
        self.assertEqual('abcdef', info['graphics']['passwd'])
        self.assertEqual(None, info['graphics']['passwdValidTo'])

        resp = self.request('/plugins/kimchi/vms/vm-1/poweroff', '{}', 'POST')
        self.assertEqual(200, resp.status)

        req = json.dumps(
            {'graphics': {'passwd': '123456', 'passwdValidTo': 20}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        info = json.loads(resp.read())
        self.assertEqual('123456', info['graphics']['passwd'])
        self.assertGreaterEqual(20, info['graphics']['passwdValidTo'])

        req = json.dumps({'name': 12})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps({'name': ''})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps({'cpu_info': {'vcpus': -2}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps({'cpu_info': {'vcpus': 'four'}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps({'memory': {'current': 100}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps({'memory': {'current': 'ten gigas'}})
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        req = json.dumps(
            {'name': 'new-name', 'cpu_info': {'vcpus': 5}, 'UUID': 'notallowed'}
        )
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(400, resp.status)

        vm = json.loads(self.request('/plugins/kimchi/vms/vm-1', req).read())

        # The maxmemory will be automatically increased when the amount of
        # memory value is greater than the current maxmemory value
        params = {
            'name': '∨м-црdαtеd',
            'cpu_info': {'vcpus': 5},
            'memory': {'current': 3072},
        }
        req = json.dumps(params)
        resp = self.request('/plugins/kimchi/vms/vm-1', req, 'PUT')
        self.assertEqual(303, resp.status)
        quoted_uri = urllib.parse.quote('/plugins/kimchi/vms/∨м-црdαtеd')
        vm_updated = json.loads(self.request(quoted_uri, req).read())
        # Memory was hot plugged
        vm['name'] = '∨м-црdαtеd'
        vm['cpu_info'].update(params['cpu_info'])
        vm['memory']['current'] = 3072
        vm['memory']['maxmemory'] = 3072

        for key in params.keys():
            self.assertEqual(vm[key], vm_updated[key])

        # change only VM users - groups are not changed (default is empty)
        resp = self.request('/plugins/kimchi/users', '{}', 'GET')
        users = json.loads(resp.read())
        req = json.dumps({'users': users})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(200, resp.status)
        info = json.loads(self.request(quoted_uri, '{}').read())
        self.assertEqual(users, info['users'])

        # change only VM groups - users are not changed (default is empty)
        resp = self.request('/plugins/kimchi/groups', '{}', 'GET')
        groups = json.loads(resp.read())
        req = json.dumps({'groups': groups})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(200, resp.status)
        info = json.loads(self.request(quoted_uri, '{}').read())
        self.assertEqual(groups, info['groups'])

        # change VM users (wrong value) and groups
        # when an error occurs, everything fails and nothing is changed
        req = json.dumps({'users': ['userdoesnotexist'], 'groups': []})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(400, resp.status)

        # change VM users and groups (wrong value)
        # when an error occurs, everything fails and nothing is changed
        req = json.dumps({'users': [], 'groups': ['groupdoesnotexist']})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(400, resp.status)

        # change bootorder
        b_order = ['hd', 'network', 'cdrom']
        req = json.dumps({'bootorder': b_order})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(200, resp.status)
        self.assertEqual(json.loads(resp.read())['bootorder'], b_order)

        req = json.dumps({'bootorder': ['bla']})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(400, resp.status)

        # change vm graphics type
        req = json.dumps({'graphics': {'type': 'spice'}})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(json.loads(resp.read())['graphics']['type'], 'spice')

        # try to add a invalid type
        req = json.dumps({'graphics': {'type': 'test'}})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(400, resp.status)

        # set vm autostart tests (powered off)
        resp = self.request(f'{quoted_uri}/start', '{}', 'POST')
        self.assertEqual(200, resp.status)
        req = json.dumps({'autostart': True})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(200, resp.status)
        resp = self.request(quoted_uri, '{}', 'GET').read()
        self.assertEqual(json.loads(resp)['autostart'], True)

        # set vm autostart tests (running)
        resp = self.request(f'{quoted_uri}/poweroff', '{}', 'POST')
        self.assertEqual(200, resp.status)
        req = json.dumps({'autostart': False})
        resp = self.request(quoted_uri, req, 'PUT')
        self.assertEqual(200, resp.status)
        resp = self.request(quoted_uri, '{}', 'GET').read()
        self.assertEqual(json.loads(resp)['autostart'], False)

    def test_vm_lifecycle(self):
        # Create a Template
        req = json.dumps(
            {
                'name': 'test',
                'source_media': {'type': 'disk', 'path': fake_iso},
                'disks': DISKS,
                'icon': 'plugins/kimchi/images/icon-debian.png',
            }
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        # Create a VM
        req = json.dumps(
            {'name': 'test-vm', 'template': '/plugins/kimchi/templates/test'}
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        self.assertEqual(202, resp.status)

        # Verify the VM
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('shutoff', vm['state'])
        self.assertEqual('plugins/kimchi/images/icon-debian.png', vm['icon'])

        # Verify the volume was created
        vol_uri = (
            '/plugins/kimchi/storagepools/default-pool/storagevolumes/' + '%s-0.img'
        )
        resp = self.request(vol_uri % vm['uuid'])
        vol = json.loads(resp.read())
        self.assertEqual(10 << 30, vol['capacity'])
        self.assertEqual(['test-vm'], vol['used_by'])

        # verify if poweroff command returns correct status
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # verify if shutdown command returns correct status
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/shutdown', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # verify if reset command returns correct status
        resp = self.request('/plugins/kimchi/vms/test-vm/reset', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # Start the VM
        resp = self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('running', vm['state'])

        # verify if start command returns correct status
        resp = self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # Test screenshot
        resp = self.request('/' + vm['screenshot'], method='HEAD')
        self.assertEqual(200, resp.status)
        self.assertTrue(resp.getheader('Content-type').startswith('image'))

        # Test Virt Viewer file
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/virtviewerfile', '{}', 'GET')
        self.assertEqual(200, resp.status)
        vvfilecontent = resp.read().decode('utf-8')
        self.assertEqual(
            vvfilecontent, '[virt-viewer]\ntype=vnc\nhost=127.0.0.1\nport=5999\n'
        )

        # Clone a running VM
        resp = self.request('/plugins/kimchi/vms/test-vm/clone', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # Create a snapshot on running vm VM
        params = {'name': 'test-snap2'}
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots', json.dumps(params), 'POST'
        )
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        task = json.loads(self.request(
            '/plugins/kimchi/tasks/%s' % task['id']).read())
        self.assertEqual('finished', task['status'])

        # Delete a snapshot
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/%s' % params['name'], '{}', 'DELETE'
        )
        self.assertEqual(204, resp.status)

        # Force poweroff the VM
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('shutoff', vm['state'])

        # Test create VM with same name fails with 400
        req = json.dumps(
            {'name': 'test-vm', 'template': '/plugins/kimchi/templates/test'}
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(400, resp.status)

        # Clone a VM
        resp = self.request('/plugins/kimchi/vms/test-vm/clone', '{}', 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        task = json.loads(
            self.request('/plugins/kimchi/tasks/%s' % task['id'], '{}').read()
        )
        self.assertEqual('finished', task['status'])
        clone_vm_name = task['target_uri'].split('/')[-2]
        self.assertTrue(re.match('test-vm-clone-\\d+', clone_vm_name))

        resp = self.request('/plugins/kimchi/vms/test-vm', '{}')
        original_vm_info = json.loads(resp.read())
        resp = self.request('/plugins/kimchi/vms/%s' % clone_vm_name, '{}')
        self.assertEqual(200, resp.status)
        clone_vm_info = json.loads(resp.read())

        self.assertNotEqual(original_vm_info['name'], clone_vm_info['name'])
        del original_vm_info['name']
        del clone_vm_info['name']

        self.assertNotEqual(original_vm_info['uuid'], clone_vm_info['uuid'])
        del original_vm_info['uuid']
        del clone_vm_info['uuid']

        self.assertEqual(original_vm_info, clone_vm_info)

        # Create a snapshot on a stopped VM
        params = {'name': 'test-snap'}
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots', json.dumps(params), 'POST'
        )
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        task = json.loads(self.request(
            '/plugins/kimchi/tasks/%s' % task['id']).read())
        self.assertEqual('finished', task['status'])

        # Look up a non-existing snapshot
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/snap404', '{}', 'GET'
        )
        self.assertEqual(404, resp.status)

        # Look up a snapshot
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/%s' % params['name'], '{}', 'GET'
        )
        self.assertEqual(200, resp.status)
        snap = json.loads(resp.read())
        self.assertTrue(int(time.time()) >= int(snap['created']))
        self.assertEqual(params['name'], snap['name'])
        self.assertEqual('', snap['parent'])
        self.assertEqual('shutoff', snap['state'])

        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots', '{}', 'GET')
        self.assertEqual(200, resp.status)
        snaps = json.loads(resp.read())
        self.assertEqual(1, len(snaps))

        # Look up current snapshot (the one created above)
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/current', '{}', 'GET'
        )
        self.assertEqual(200, resp.status)
        snap = json.loads(resp.read())
        self.assertEqual(params['name'], snap['name'])

        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots', '{}', 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        snap_name = task['target_uri'].split('/')[-1]
        wait_task(self._task_lookup, task['id'])
        resp = self.request('/plugins/kimchi/tasks/%s' %
                            task['id'], '{}', 'GET')
        task = json.loads(resp.read())
        self.assertEqual('finished', task['status'])

        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots', '{}', 'GET')
        self.assertEqual(200, resp.status)
        snaps = json.loads(resp.read())
        self.assertEqual(2, len(snaps))

        # Look up current snapshot (the one created above)
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/current', '{}', 'GET'
        )
        self.assertEqual(200, resp.status)
        snap = json.loads(resp.read())
        self.assertEqual(snap_name, snap['name'])

        # Revert to snapshot
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/%s/revert' % params['name'],
            '{}',
            'POST',
        )
        self.assertEqual(200, resp.status)
        snap = json.loads(resp.read())
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'GET')
        self.assertEqual(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEqual(vm['state'], snap['state'])
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/current', '{}', 'GET'
        )
        self.assertEqual(200, resp.status)
        current_snap = json.loads(resp.read())
        self.assertEqual(snap, current_snap)

        # Delete a snapshot
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/snapshots/%s' % params['name'], '{}', 'DELETE'
        )
        self.assertEqual(204, resp.status)

        # Suspend the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'GET')
        self.assertEqual(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEqual(vm['state'], 'shutoff')
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/suspend', '{}', 'POST')
        self.assertEqual(400, resp.status)
        resp = self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        self.assertEqual(200, resp.status)
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'GET')
        self.assertEqual(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEqual(vm['state'], 'running')
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/suspend', '{}', 'POST')
        self.assertEqual(200, resp.status)
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'GET')
        self.assertEqual(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEqual(vm['state'], 'paused')

        # Resume the VM
        resp = self.request('/plugins/kimchi/vms/test-vm/resume', '{}', 'POST')
        self.assertEqual(200, resp.status)
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'GET')
        self.assertEqual(200, resp.status)
        vm = json.loads(resp.read())
        self.assertEqual(vm['state'], 'running')

        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Delete the Template
        resp = self.request('/plugins/kimchi/templates/test', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Verify the volume was deleted
        self.assertHTTPStatus(404, vol_uri % vm['uuid'])

    def test_vm_netboot(self):
        # Create a Template
        req = json.dumps(
            {'name': 'tnetboot', 'source_media': {'type': 'netboot'}})
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        # Create a VM
        req = json.dumps(
            {'name': 'test-vm', 'template': '/plugins/kimchi/templates/tnetboot'}
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        self.assertEqual(202, resp.status)

        # Verify the VM
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('shutoff', vm['state'])
        self.assertEqual('plugins/kimchi/images/icon-vm.png', vm['icon'])

        # verify if poweroff command returns correct status
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # verify if shutdown command returns correct status
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/shutdown', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # verify if reset command returns correct status
        resp = self.request('/plugins/kimchi/vms/test-vm/reset', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # Start the VM
        resp = self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('running', vm['state'])

        # verify if start command returns correct status
        resp = self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        self.assertEqual(400, resp.status)

        # Force poweroff the VM
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('shutoff', vm['state'])

        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Delete the Template
        resp = self.request(
            '/plugins/kimchi/templates/tnetboot', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

    def test_vm_graphics(self):
        # Create a Template
        req = json.dumps(
            {'name': 'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        # Create a VM with default args
        req = json.dumps(
            {'name': 'test-vm', 'template': '/plugins/kimchi/templates/test'}
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        # Verify the VM
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('127.0.0.1', vm['graphics']['listen'])
        self.assertEqual('vnc', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Create a VM with specified graphics type and listen
        graphics = {'type': 'vnc', 'listen': '127.0.0.1'}
        req = json.dumps(
            {
                'name': 'test-vm',
                'template': '/plugins/kimchi/templates/test',
                'graphics': graphics,
            }
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        # Verify the VM
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('127.0.0.1', vm['graphics']['listen'])
        self.assertEqual('vnc', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Create a VM with listen as ipv6 address
        graphics = {'type': 'spice', 'listen': 'fe00::0'}
        req = json.dumps(
            {
                'name': 'test-vm',
                'template': '/plugins/kimchi/templates/test',
                'graphics': graphics,
            }
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        # Verify the VM
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('fe00::0', vm['graphics']['listen'])
        self.assertEqual('spice', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Create a VM with specified graphics type and default listen
        graphics = {'type': 'spice'}
        req = json.dumps(
            {
                'name': 'test-vm',
                'template': '/plugins/kimchi/templates/test',
                'graphics': graphics,
            }
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        # Verify the VM
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('127.0.0.1', vm['graphics']['listen'])
        self.assertEqual('spice', vm['graphics']['type'])
        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Try to create a VM with invalid graphics type
        graphics = {'type': 'invalid'}
        req = json.dumps(
            {
                'name': 'test-vm',
                'template': '/plugins/kimchi/templates/test',
                'graphics': graphics,
            }
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(400, resp.status)

        # Try to create a VM with invalid graphics listen
        graphics = {'type': 'spice', 'listen': 'invalid'}
        req = json.dumps(
            {
                'name': 'test-vm',
                'template': '/plugins/kimchi/templates/test',
                'graphics': graphics,
            }
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(400, resp.status)

        # Delete the Template
        resp = self.request('/plugins/kimchi/templates/test', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

    def test_vm_storage_devices(self):

        with RollbackContext() as rollback:
            # Create a template as a base for our VMs
            req = json.dumps(
                {'name': 'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
            )
            resp = self.request('/plugins/kimchi/templates', req, 'POST')
            self.assertEqual(201, resp.status)
            # Delete the template
            rollback.prependDefer(
                self.request, '/plugins/kimchi/templates/test', '{}', 'DELETE'
            )

            # Create a VM with default args
            req = json.dumps(
                {'name': 'test-vm', 'template': '/plugins/kimchi/templates/test'}
            )
            resp = self.request('/plugins/kimchi/vms', req, 'POST')
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
            # Delete the VM
            rollback.prependDefer(
                self.request, '/plugins/kimchi/vms/test-vm', '{}', 'DELETE'
            )

            # Check storage devices
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages', '{}', 'GET')
            devices = json.loads(resp.read())
            self.assertEqual(2, len(devices))
            dev_types = []
            for d in devices:
                self.assertIn('type', d.keys())
                self.assertIn('dev', d.keys())
                self.assertIn('path', d.keys())
                dev_types.append(d['type'])

            self.assertEqual(['cdrom', 'disk'], sorted(dev_types))

            # Attach cdrom with nonexistent iso
            req = json.dumps(
                {'dev': 'hdx', 'type': 'cdrom', 'path': '/tmp/nonexistent.iso'}
            )
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages', req, 'POST')
            self.assertEqual(400, resp.status)

            # Create temp storage pool
            req = json.dumps(
                {
                    'name': 'tmp',
                    'capacity': 1024,
                    'allocated': 512,
                    'path': '/tmp',
                    'type': 'dir',
                }
            )
            resp = self.request('/plugins/kimchi/storagepools', req, 'POST')
            self.assertEqual(201, resp.status)
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp/activate', req, 'POST'
            )
            self.assertEqual(200, resp.status)

            # 'name' is required for this type of volume
            open('/tmp/attach-volume', 'w').close()
            req = json.dumps(
                {'capacity': 1024, 'allocation': 512,
                    'type': 'disk', 'format': 'raw'}
            )
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp/storagevolumes', req, 'POST'
            )
            self.assertEqual(400, resp.status)
            req = json.dumps(
                {
                    'name': 'attach-volume',
                    'capacity': 1024,
                    'allocation': 512,
                    'type': 'disk',
                    'format': 'raw',
                }
            )
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp/storagevolumes', req, 'POST'
            )
            self.assertEqual(202, resp.status)
            time.sleep(1)

            # Attach cdrom with both path and volume specified
            open('/tmp/existent.iso', 'w').close()
            req = json.dumps(
                {
                    'dev': 'hdx',
                    'type': 'cdrom',
                    'pool': 'tmp',
                    'vol': 'attach-volume',
                    'path': '/tmp/existent.iso',
                }
            )
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages', req, 'POST')
            self.assertEqual(400, resp.status)

            # Attach disk with both path and volume specified
            req = json.dumps(
                {
                    'dev': 'hdx',
                    'type': 'disk',
                    'pool': 'tmp',
                    'vol': 'attach-volume',
                    'path': '/tmp/existent.iso',
                }
            )
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages', req, 'POST')
            self.assertEqual(400, resp.status)

            # Attach disk with only pool specified
            req = json.dumps({'dev': 'hdx', 'type': 'cdrom', 'pool': 'tmp'})
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages', req, 'POST')
            self.assertEqual(400, resp.status)

            # Attach disk with pool and vol specified
            req = json.dumps(
                {'type': 'disk', 'pool': 'tmp', 'vol': 'attach-volume'})
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages', req, 'POST')
            self.assertEqual(201, resp.status)
            cd_info = json.loads(resp.read())
            self.assertEqual('disk', cd_info['type'])

            # Attach a cdrom with existent dev name
            req = json.dumps({'type': 'cdrom', 'path': '/tmp/existent.iso'})
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages', req, 'POST')
            self.assertEqual(201, resp.status)
            cd_info = json.loads(resp.read())
            cd_dev = cd_info['dev']
            self.assertEqual('cdrom', cd_info['type'])
            self.assertEqual('/tmp/existent.iso', cd_info['path'])
            # Delete the file and cdrom
            rollback.prependDefer(
                self.request,
                '/plugins/kimchi/vms/test-vm/storages/hdx',
                '{}',
                'DELETE'
            )
            os.remove('/tmp/existent.iso')
            os.remove('/tmp/attach-volume')

            # Change path of storage cdrom
            cdrom = 'http://mirrors.kernel.org/fedora/releases/29/Everything' \
                    '/x86_64/iso/Fedora-Everything-netinst-x86_64-29-1.2.iso'
            req = json.dumps({'path': cdrom})
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages/' + cd_dev, req, 'PUT'
            )

            if not os.uname()[4] == 's390x':
                self.assertEqual(200, resp.status)
                cd_info = json.loads(resp.read())
                self.assertEqual(
                    urllib.parse.urlparse(cdrom).path,
                    urllib.parse.urlparse(cd_info['path']).path,
                )

            # Test GET
            devs = json.loads(
                self.request('/plugins/kimchi/vms/test-vm/storages').read()
            )
            self.assertEqual(4, len(devs))

            # Detach storage cdrom
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/storages/' + cd_dev, '{}', 'DELETE'
            )
            self.assertEqual(204, resp.status)

            # Test GET
            devs = json.loads(
                self.request('/plugins/kimchi/vms/test-vm/storages').read()
            )

            self.assertEqual(3, len(devs))
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp/deactivate', '{}', 'POST'
            )
            self.assertEqual(200, resp.status)

            # cannot delete storagepool with volumes associate to guests
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp', '{}', 'DELETE')
            self.assertEqual(400, resp.status)

            # activate pool
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp/activate', '{}', 'POST'
            )
            self.assertEqual(200, resp.status)

            # delete volumes
            if not os.uname()[4] == 's390x':
                uri = '/plugins/kimchi/vms/test-vm/storages/hdd'
            else:
                uri = '/plugins/kimchi/vms/test-vm/storages/vdb'
            resp = self.request(uri, '{}', 'DELETE')
            self.assertEqual(204, resp.status)

            # deactive and delete storage pool
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp/deactivate', '{}', 'POST'
            )
            self.assertEqual(200, resp.status)
            # Pool is associated with VM test (create above)
            resp = self.request(
                '/plugins/kimchi/storagepools/tmp', '{}', 'DELETE')
            self.assertEqual(204, resp.status)

    def test_vm_iface(self):

        with RollbackContext() as rollback:
            # Create a template as a base for our VMs
            req = json.dumps(
                {'name': 'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
            )
            resp = self.request('/plugins/kimchi/templates', req, 'POST')
            self.assertEqual(201, resp.status)
            # Delete the template
            rollback.prependDefer(
                self.request, '/plugins/kimchi/templates/test', '{}', 'DELETE'
            )

            # Create a VM with default args
            req = json.dumps(
                {'name': 'test-vm', 'template': '/plugins/kimchi/templates/test'}
            )
            resp = self.request('/plugins/kimchi/vms', req, 'POST')
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
            # Delete the VM
            rollback.prependDefer(
                self.request, '/plugins/kimchi/vms/test-vm', '{}', 'DELETE'
            )

            # Create a network
            req = json.dumps(
                {'name': 'test-network', 'connection': 'nat', 'net': '127.0.1.0/24'}
            )
            resp = self.request('/plugins/kimchi/networks', req, 'POST')
            self.assertEqual(201, resp.status)
            # Delete the network
            rollback.prependDefer(
                self.request, '/plugins/kimchi/networks/test-network', '{}', 'DELETE'
            )

            ifaces = json.loads(
                self.request('/plugins/kimchi/vms/test-vm/ifaces').read()
            )
            if not os.uname()[4] == 's390x':
                self.assertEqual(1, len(ifaces))

            for iface in ifaces:
                res = json.loads(
                    self.request(
                        '/plugins/kimchi/vms/test-vm/ifaces/%s' % iface['mac']
                    ).read()
                )
                self.assertEqual('default', res['network'])
                self.assertEqual(17, len(res['mac']))
                self.assertEqual(get_template_default(
                    'old', 'nic_model'), res['model'])
                self.assertTrue('ips' in res)

            # try to attach an interface without specifying 'model'
            req = json.dumps({'type': 'network'})
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/ifaces', req, 'POST')
            self.assertEqual(400, resp.status)

            # try to attach an interface of type "macvtap" without source
            if os.uname()[4] == 's390x':
                req = json.dumps({'type': 'macvtap'})
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces', req, 'POST')
                self.assertEqual(400, resp.status)

                # try to attach an interface of type "ovs" without source
                req = json.dumps({'type': 'ovs'})
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces', req, 'POST')
                self.assertEqual(400, resp.status)

            # attach network interface to vm
            req = json.dumps(
                {'type': 'network', 'network': 'test-network', 'model': 'virtio'}
            )
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/ifaces', req, 'POST')
            self.assertEqual(201, resp.status)
            iface = json.loads(resp.read())

            self.assertEqual('test-network', iface['network'])
            self.assertEqual(17, len(iface['mac']))
            self.assertEqual('virtio', iface['model'])
            self.assertEqual('network', iface['type'])

            # update vm interface
            newMacAddr = '54:50:e3:44:8a:af'
            req = json.dumps(
                {
                    'network': 'default',
                    'model': 'virtio',
                    'type': 'network',
                    'mac': newMacAddr,
                }
            )
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/ifaces/%s' % iface['mac'], req, 'PUT'
            )
            self.assertEqual(303, resp.status)
            iface = json.loads(
                self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces/%s' % newMacAddr
                ).read()
            )
            self.assertEqual(newMacAddr, iface['mac'])

            # Start the VM
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
            vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
            self.assertEqual('running', vm['state'])

            # Check for an IP address
            iface = json.loads(
                self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces/%s' % newMacAddr
                ).read()
            )
            self.assertTrue(len(iface['ips']) > 0)

            # Force poweroff the VM
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST')
            vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
            self.assertEqual('shutoff', vm['state'])

            # detach network interface from vm
            resp = self.request(
                '/plugins/kimchi/vms/test-vm/ifaces/%s' % iface['mac'], '{}', 'DELETE'
            )
            self.assertEqual(204, resp.status)

            if os.uname()[4] == 's390x':
                # attach macvtap interface to vm
                req = json.dumps({'type': 'macvtap', 'source': 'test-network'})
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces', req, 'POST')
                self.assertEqual(201, resp.status)
                iface = json.loads(resp.read())

                self.assertEqual('test-network', iface['source'])
                self.assertEqual('macvtap', iface['type'])

                # Start the VM
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
                vm = json.loads(self.request(
                    '/plugins/kimchi/vms/test-vm').read())
                self.assertEqual('running', vm['state'])

                # Force poweroff the VM
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST'
                )
                vm = json.loads(self.request(
                    '/plugins/kimchi/vms/test-vm').read())
                self.assertEqual('shutoff', vm['state'])

                # detach network interface from vm
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces/%s' % iface['mac'],
                    '{}',
                    'DELETE',
                )
                self.assertEqual(204, resp.status)

                # attach ovs interface to vm
                req = json.dumps({'type': 'ovs', 'source': 'test-network'})
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces', req, 'POST')
                self.assertEqual(201, resp.status)
                iface = json.loads(resp.read())

                self.assertEqual('test-network', iface['source'])
                self.assertEqual('ovs', iface['type'])

                # Start the VM
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
                vm = json.loads(self.request(
                    '/plugins/kimchi/vms/test-vm').read())
                self.assertEqual('running', vm['state'])

                # Force poweroff the VM
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST'
                )
                vm = json.loads(self.request(
                    '/plugins/kimchi/vms/test-vm').read())
                self.assertEqual('shutoff', vm['state'])

                # detach ovs interface from vm
                resp = self.request(
                    '/plugins/kimchi/vms/test-vm/ifaces/%s' % iface['mac'],
                    '{}',
                    'DELETE',
                )
                self.assertEqual(204, resp.status)

    def test_vm_customise_storage(self):
        # Create a Template
        req = json.dumps(
            {
                'name': 'test',
                'disks': DISKS,
                'source_media': {'type': 'disk', 'path': fake_iso},
            }
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        # Create alternate storage
        req = json.dumps(
            {
                'name': 'alt',
                'capacity': 1024,
                'allocated': 512,
                'path': '/tmp',
                'type': 'dir',
            }
        )
        resp = self.request('/plugins/kimchi/storagepools', req, 'POST')
        self.assertEqual(201, resp.status)
        resp = self.request(
            '/plugins/kimchi/storagepools/alt/activate', req, 'POST')
        self.assertEqual(200, resp.status)

        # Create a VM
        req = json.dumps(
            {
                'name': 'test-vm',
                'template': '/plugins/kimchi/templates/test',
                'storagepool': '/plugins/kimchi/storagepools/alt',
            }
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'GET')
        vm_info = json.loads(resp.read())

        # Test template not changed after vm customise its pool
        t = json.loads(self.request('/plugins/kimchi/templates/test').read())
        self.assertEqual(
            t['disks'][0]['pool']['name'], '/plugins/kimchi/storagepools/default-pool'
        )

        # Verify the volume was created
        vol_uri = (
            '/plugins/kimchi/storagepools/alt/storagevolumes/%s-0.img' % vm_info['uuid']
        )
        resp = self.request(vol_uri)
        vol = json.loads(resp.read())
        self.assertEqual(10 << 30, vol['capacity'])

        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        # Verify the volume was deleted
        self.assertHTTPStatus(404, vol_uri)

    def test_scsi_fc_storage(self):
        # Create scsi fc pool
        req = json.dumps(
            {
                'name': 'scsi_fc_pool',
                'type': 'scsi',
                'source': {'adapter_name': 'scsi_host2'},
            }
        )
        resp = self.request('/plugins/kimchi/storagepools', req, 'POST')
        self.assertEqual(201, resp.status)

        # Test create vms using lun of this pool
        # activate the storage pool
        resp = self.request(
            '/plugins/kimchi/storagepools/scsi_fc_pool/activate', '{}', 'POST'
        )

        # Create template fails because SCSI volume is missing
        tmpl_params = {
            'name': 'test_fc_pool',
            'source_media': {'type': 'disk', 'path': fake_iso},
            'disks': [{'pool': {'name': '/plugins/kimchi/storagepools/scsi_fc_pool'}}],
        }

        req = json.dumps(tmpl_params)
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(400, resp.status)

        # Choose SCSI volume to create template
        resp = self.request(
            '/plugins/kimchi/storagepools/scsi_fc_pool/storagevolumes')
        lun_name = json.loads(resp.read())[0]['name']
        pool_name = tmpl_params['disks'][0]['pool']['name']
        tmpl_params['disks'] = [
            {
                'index': 0,
                'volume': lun_name,
                'pool': {'name': pool_name},
                'format': 'raw',
            }
        ]
        req = json.dumps(tmpl_params)
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        # Create vm in scsi pool
        req = json.dumps(
            {'name': 'test-vm', 'template': '/plugins/kimchi/templates/test_fc_pool'}
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        # Start the VM
        resp = self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('running', vm['state'])

        # Force poweroff the VM
        resp = self.request(
            '/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        self.assertEqual('shutoff', vm['state'])

        # Delete the VM
        resp = self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        self.assertEqual(204, resp.status)

    def test_unnamed_vms(self):
        # Create a Template
        req = json.dumps(
            {'name': 'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        # Create 5 unnamed vms from this template
        for i in range(1, 6):
            req = json.dumps({'template': '/plugins/kimchi/templates/test'})
            task = json.loads(self.request(
                '/plugins/kimchi/vms', req, 'POST').read())
            wait_task(self._task_lookup, task['id'])
            resp = self.request(
                '/plugins/kimchi/vms/test-vm-%i' % i, '{}', 'GET')
            self.assertEqual(resp.status, 200)
        count = len(json.loads(self.request('/plugins/kimchi/vms').read()))
        self.assertEqual(6, count)

    def test_create_vm_without_template(self):
        req = json.dumps({'name': 'vm-without-template'})
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(400, resp.status)
        resp = json.loads(resp.read())
        self.assertIn('KCHVM0016E:', resp['reason'])

    def test_create_vm_with_bad_template_uri(self):
        req = json.dumps({'name': 'vm-bad-template',
                          'template': '/mytemplate'})
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(400, resp.status)
        resp = json.loads(resp.read())
        self.assertIn('KCHVM0012E', resp['reason'])

    def test_vm_migrate(self):
        with RollbackContext() as rollback:
            req = json.dumps(
                {
                    'name': 'test-migrate',
                    'source_media': {'type': 'disk', 'path': fake_iso},
                }
            )
            resp = self.request('/plugins/kimchi/templates', req, 'POST')
            self.assertEqual(201, resp.status)
            rollback.prependDefer(
                self.request, '/plugins/kimchi/templates/test-migrate', '{}', 'DELETE'
            )

            req = json.dumps(
                {
                    'name': 'test-vm-migrate',
                    'template': '/plugins/kimchi/templates/test-migrate',
                }
            )
            resp = self.request('/plugins/kimchi/vms', req, 'POST')
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
            rollback.prependDefer(
                self.request, '/plugins/kimchi/vms/test-vm', '{}', 'DELETE'
            )

            params = {'remote_host': 'destination_host'}
            resp = self.request(
                '/plugins/kimchi/vms/test-vm-migrate/migrate',
                json.dumps(params),
                'POST',
            )
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
            task = json.loads(
                self.request('/plugins/kimchi/tasks/%s' % task['id']).read()
            )
            self.assertEqual('finished', task['status'])

            params = {'remote_host': 'rdma_host', 'enable_rdma': True}
            resp = self.request(
                '/plugins/kimchi/vms/test-vm-migrate/migrate',
                json.dumps(params),
                'POST',
            )
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
            task = json.loads(
                self.request('/plugins/kimchi/tasks/%s' % task['id']).read()
            )
            self.assertEqual('finished', task['status'])

    def test_create_vm_with_img_based_template(self):
        resp = json.loads(
            self.request(
                '/plugins/kimchi/storagepools/default-pool/storagevolumes'
            ).read()
        )
        self.assertEqual(0, len(resp))

        # Create a Template
        mock_base = '/tmp/mock.img'
        os.system('qemu-img create -f qcow2 %s 10M' % mock_base)
        req = json.dumps(
            {'name': 'test', 'source_media': {'type': 'disk', 'path': mock_base}}
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        req = json.dumps({'template': '/plugins/kimchi/templates/test'})
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        self.assertEqual(202, resp.status)
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        # Test storage volume created with backing store of base file
        resp = json.loads(
            self.request(
                '/plugins/kimchi/storagepools/default-pool/storagevolumes'
            ).read()
        )
        self.assertEqual(1, len(resp))

    def _create_pool(self, name):
        req = json.dumps(
            {
                'name': name,
                'capacity': 10240,
                'allocated': 5120,
                'path': '/var/lib/libvirt/images/',
                'type': 'dir',
            }
        )
        resp = self.request('/plugins/kimchi/storagepools', req, 'POST')
        self.assertEqual(201, resp.status)

        # Verify the storage pool
        storagepool = json.loads(
            self.request('/plugins/kimchi/storagepools/%s' % name).read()
        )
        self.assertEqual('inactive', storagepool['state'])
        return name

    def _delete_pool(self, name):
        # Delete the storage pool
        resp = self.request('/plugins/kimchi/storagepools/%s' %
                            name, '{}', 'DELETE')
        self.assertEqual(204, resp.status)

    def test_iso_scan_shallow(self):
        # fake environment preparation
        self._create_pool('pool-3')
        self.request(
            '/plugins/kimchi/storagepools/pool-3/activate', '{}', 'POST')
        params = {
            'name': 'fedora.iso',
            'capacity': 1073741824,  # 1 GiB
            'type': 'file',
            'format': 'iso',
        }
        task_info = model.storagevolumes_create('pool-3', params)
        wait_task(self._task_lookup, task_info['id'])

        storagevolume = json.loads(
            self.request(
                '/plugins/kimchi/storagepools/kimchi_isos/storagevolumes/'
            ).read()
        )[0]
        self.assertEqual('fedora.iso', storagevolume['name'])
        self.assertEqual('iso', storagevolume['format'])
        self.assertEqual('/var/lib/libvirt/images/fedora.iso',
                         storagevolume['path'])
        self.assertEqual(1073741824, storagevolume['capacity'])  # 1 GiB
        self.assertEqual(0, storagevolume['allocation'])
        self.assertEqual('17', storagevolume['os_version'])
        self.assertEqual('fedora', storagevolume['os_distro'])
        self.assertEqual(True, storagevolume['bootable'])
        self.assertEqual(True, storagevolume['has_permission'])

        # Create a template
        # In real model os distro/version can be omitted
        # as we will scan the iso
        req = json.dumps(
            {
                'name': 'test',
                'source_media': {'type': 'disk', 'path': storagevolume['path']},
                'os_distro': storagevolume['os_distro'],
                'os_version': storagevolume['os_version'],
            }
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        self.assertEqual(201, resp.status)

        # Verify the template
        t = json.loads(self.request('/plugins/kimchi/templates/test').read())
        self.assertEqual('test', t['name'])
        self.assertEqual('fedora', t['os_distro'])
        self.assertEqual('17', t['os_version'])
        self.assertEqual(get_template_default('old', 'memory'), t['memory'])

        # Deactivate or destroy scan pool return 405
        resp = self.request(
            '/plugins/kimchi/storagepools/kimchi_isos/storagevolumes' '/deactivate',
            '{}',
            'POST',
        )
        self.assertEqual(405, resp.status)

        resp = self.request(
            '/plugins/kimchi/storagepools/kimchi_isos/storagevolumes', '{}', 'DELETE'
        )
        self.assertEqual(405, resp.status)

        # Delete the template
        resp = self.request('/plugins/kimchi/templates/%s' %
                            t['name'], '{}', 'DELETE')
        self.assertEqual(204, resp.status)

        resp = self.request(
            '/plugins/kimchi/storagepools/pool-3/deactivate', '{}', 'POST'
        )
        self.assertEqual(200, resp.status)
        self._delete_pool('pool-3')

    def test_screenshot_refresh(self):
        # Create a VM
        req = json.dumps(
            {'name': 'test', 'source_media': {'type': 'disk', 'path': fake_iso}}
        )
        resp = self.request('/plugins/kimchi/templates', req, 'POST')
        req = json.dumps(
            {'name': 'test-vm', 'template': '/plugins/kimchi/templates/test'}
        )
        resp = self.request('/plugins/kimchi/vms', req, 'POST')
        task = json.loads(resp.read())
        wait_task(self._task_lookup, task['id'])

        # Test screenshot for shut-off state vm
        resp = self.request('/plugins/kimchi/vms/test-vm/screenshot')
        self.assertEqual(404, resp.status)

        # Test screenshot for running vm
        resp = self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())

        resp = self.request('/' + vm['screenshot'], method='HEAD')
        self.assertEqual(200, resp.status)
        self.assertTrue(resp.getheader('Content-type').startswith('image'))

        # Test screenshot sub-resource redirect
        resp = self.request('/plugins/kimchi/vms/test-vm/screenshot')
        self.assertEqual(200, resp.status)
        self.assertEqual('image/png', resp.getheader('content-type'))
        lastMod1 = resp.getheader('last-modified')

        # Take another screenshot instantly and compare the last Modified date
        resp = self.request('/plugins/kimchi/vms/test-vm/screenshot')
        lastMod2 = resp.getheader('last-modified')
        self.assertEqual(lastMod2, lastMod1)

        resp = self.request(
            '/plugins/kimchi/vms/test-vm/screenshot', '{}', 'DELETE')
        self.assertEqual(405, resp.status)

        # No screenshot after stopped the VM
        self.request('/plugins/kimchi/vms/test-vm/poweroff', '{}', 'POST')
        resp = self.request('/plugins/kimchi/vms/test-vm/screenshot')
        self.assertEqual(404, resp.status)

        # Picture link not available after VM deleted
        self.request('/plugins/kimchi/vms/test-vm/start', '{}', 'POST')
        vm = json.loads(self.request('/plugins/kimchi/vms/test-vm').read())
        img_lnk = vm['screenshot']
        self.request('/plugins/kimchi/vms/test-vm', '{}', 'DELETE')
        resp = self.request('/' + img_lnk)
        self.assertEqual(404, resp.status)

    def test_interfaces(self):
        resp = self.request('/plugins/kimchi/interfaces').read()
        interfaces = json.loads(resp.decode('utf-8'))
        keys = ['name', 'type', 'ipaddr', 'netmask', 'status', 'module']
        for interface in interfaces:
            self.assertEqual(sorted(keys), sorted(interface.keys()))

    def _task_lookup(self, taskid):
        return json.loads(self.request('/plugins/kimchi/tasks/%s' % taskid).read())

    def test_tasks(self):
        id1 = AsyncTask('/plugins/kimchi/tasks/1', self._async_op).id
        id2 = AsyncTask('/plugins/kimchi/tasks/2', self._except_op).id
        id3 = AsyncTask('/plugins/kimchi/tasks/3', self._intermid_op).id

        target_uri = urllib.parse.quote('^/plugins/kimchi/tasks/*', safe='')
        filter_data = 'status=running&target_uri=%s' % target_uri
        tasks = json.loads(
            self.request('/plugins/kimchi/tasks?%s' % filter_data).read()
        )
        self.assertLessEqual(3, len(tasks))

        tasks = json.loads(self.request('/plugins/kimchi/tasks').read())
        tasks_ids = [t['id'] for t in tasks]
        self.assertEqual(set([id1, id2, id3]) - set(tasks_ids), set([]))
        wait_task(self._task_lookup, id2)
        foo2 = json.loads(self.request(
            '/plugins/kimchi/tasks/%s' % id2).read())
        keys = ['id', 'status', 'message', 'target_uri']
        self.assertEqual(sorted(keys), sorted(foo2.keys()))
        self.assertEqual('failed', foo2['status'])
        wait_task(self._task_lookup, id3)
        foo3 = json.loads(self.request(
            '/plugins/kimchi/tasks/%s' % id3).read())
        self.assertEqual('in progress', foo3['message'])
        self.assertEqual('running', foo3['status'])

    def test_config(self):
        resp = self.request('/plugins/kimchi/config').read()
        conf = json.loads(resp)
        keys = ["version", "with_spice_web_client"]
        self.assertEqual(keys, sorted(conf.keys()))

    def test_capabilities(self):
        resp = self.request('/plugins/kimchi/config/capabilities').read()
        conf = json.loads(resp)

        keys = [
            'libvirt_stream_protocols',
            'qemu_stream',
            'qemu_spice',
            'screenshot',
            'kernel_vfio',
            'nm_running',
            'mem_hotplug_support',
            'libvirtd_running',
        ]
        self.assertEqual(sorted(keys), sorted(conf.keys()))

    def test_distros(self):
        resp = self.request('/plugins/kimchi/config/distros').read()
        distros = json.loads(resp)
        for distro in distros:
            self.assertIn('name', distro)
            self.assertIn('os_distro', distro)
            self.assertIn('os_version', distro)
            self.assertIn('path', distro)

        # Test in X86
        ident = 'Fedora 29'
        resp = self.request(
            '/plugins/kimchi/config/distros/%s' % urllib.parse.quote(ident)
        ).read()
        distro = json.loads(resp)
        if os.uname()[4] in ['x86_64', 'amd64']:
            self.assertEqual(distro['name'], ident)
            self.assertEqual(distro['os_distro'], 'fedora')
            self.assertEqual(distro['os_version'], '29')
            self.assertEqual(distro['os_arch'], 'x86_64')
            self.assertIn('path', distro)
        else:
            # Distro not found error
            if distro.get('reason'):
                self.assertIn('KCHDISTRO0001E', distro.get('reason'))

        # Test in PPC
        ident = 'Fedora 24 LE'
        resp = self.request(
            '/plugins/kimchi/config/distros/%s' % urllib.parse.quote(ident)
        ).read()
        distro = json.loads(resp)
        if os.uname()[4] == 'ppc64':
            self.assertEqual(distro['name'], ident)
            self.assertEqual(distro['os_distro'], 'fedora')
            self.assertEqual(distro['os_version'], '24')
            self.assertEqual(distro['os_arch'], 'ppc64le')
            self.assertIn('path', distro)
        else:
            # Distro not found error
            if distro.get('reason'):
                self.assertIn('KCHDISTRO0001E', distro.get('reason'))

    def test_ovsbridges(self):
        resp = self.request('/plugins/kimchi/ovsbridges')
        self.assertEqual(200, resp.status)


class HttpsRestTests(RestTests):
    """
    Run all of the same tests as above, but use https instead
    """

    def setUp(self):
        self.request = partial(request)
        model.reset()
