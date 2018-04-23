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

import cherrypy
import json
import os
import time
import unittest

from tests.utils import patch_auth, request, run_server
from tests.utils import wait_task

from wok.exception import InvalidOperation
from wok.plugins.kimchi.osinfo import get_template_default

import iso_gen

test_server = None
model = None
fake_iso = None


def setUpModule():
    global model, test_server, fake_iso
    cherrypy.request.headers = {'Accept': 'application/json'}
    patch_auth()
    test_server = run_server(test_mode=True)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model
    fake_iso = '/tmp/fake.iso'
    iso_gen.construct_fake_iso(fake_iso, True, '12.04', 'ubuntu')


def tearDownModule():
    test_server.stop()
    os.unlink(fake_iso)


class MockModelTests(unittest.TestCase):
    def setUp(self):
        model.reset()

    def test_screenshot_refresh(self):
        # Create a VM
        req = json.dumps({'name': 'test',
                          'source_media': {'type': 'disk', 'path': fake_iso}})
        request('/plugins/kimchi/templates', req, 'POST')
        req = json.dumps({'name': 'test-vm',
                          'template': '/plugins/kimchi/templates/test'})
        resp = request('/plugins/kimchi/vms', req, 'POST')
        task = json.loads(resp.read())
        wait_task(model.task_lookup, task['id'])

        # Test screenshot refresh for running vm
        request('/plugins/kimchi/vms/test-vm/start', '{}',
                'POST')
        resp = request('/plugins/kimchi/vms/test-vm/screenshot')
        self.assertEquals(200, resp.status)
        self.assertEquals('image/png', resp.getheader('content-type'))
        resp1 = request('/plugins/kimchi/vms/test-vm')
        rspBody = resp1.read()
        testvm_Data = json.loads(rspBody)
        screenshotURL = '/' + testvm_Data['screenshot']
        time.sleep(5)
        resp2 = request(screenshotURL)
        self.assertEquals(200, resp2.status)
        self.assertEquals(resp2.getheader('content-type'),
                          resp.getheader('content-type'))
        self.assertEquals(resp2.getheader('content-length'),
                          resp.getheader('content-length'))
        self.assertEquals(resp2.getheader('last-modified'),
                          resp.getheader('last-modified'))

    def test_vm_list_sorted(self):
        req = json.dumps({'name': 'test',
                          'source_media': {'type': 'disk', 'path': fake_iso}})
        request('/plugins/kimchi/templates', req, 'POST')

        def add_vm(name):
            # Create a VM
            req = json.dumps({'name': name,
                              'template': '/plugins/kimchi/templates/test'})
            task = json.loads(request('/plugins/kimchi/vms',
                              req, 'POST').read())
            wait_task(model.task_lookup, task['id'])

        vms = [u'abc', u'bca', u'cab', u'xba']
        for vm in vms:
            add_vm(vm)

        vms.append(u'test')
        self.assertEqual(model.vms_get_list(), sorted(vms))

    def test_memory_window_changes(self):
        model.templates_create({'name': u'test',
                                'source_media': {'type': 'disk',
                                                 'path': fake_iso}})
        task = model.vms_create({'name': u'test-vm',
                                 'template': '/plugins/kimchi/templates/test'})
        wait_task(model.task_lookup, task['id'])

        info = model.device_lookup('pci_0000_1a_00_0')
        model.vmhostdevs_update_mmio_guest(u'test-vm', True)
        model._attach_device(u'test-vm',
                             model._get_pci_device_xml(info, 0, False))

    def test_hotplug_3D_card(self):
        model.templates_create({'name': u'test',
                                'source_media': {'type': 'disk',
                                                 'path': fake_iso}})
        task = model.vms_create({'name': u'test-vm',
                                 'template': '/plugins/kimchi/templates/test'})
        wait_task(model.task_lookup, task['id'])
        model.vm_start(u'test-vm')

        # attach the 3D cards found to a running guest
        all_devices = model.devices_get_list()
        for device in all_devices:
            device_info = model.device_lookup(device)
            if model.device_is_device_3D_controller(device_info):
                try:
                    model.vmhostdevs_create(u'test-vm', {'name': device})

                # expect the error: KCHVMHDEV0006E
                except InvalidOperation as e:
                    self.assertEqual(e.message[:14], u'KCHVMHDEV0006E')

    def test_vm_info(self):
        model.templates_create({'name': u'test',
                                'source_media': {'type': 'disk',
                                                 'path': fake_iso}})
        task = model.vms_create({'name': u'test-vm',
                                 'template': '/plugins/kimchi/templates/test'})
        wait_task(model.task_lookup, task['id'])
        vms = model.vms_get_list()
        self.assertEquals(2, len(vms))
        self.assertIn(u'test-vm', vms)

        keys = set(('name', 'state', 'stats', 'uuid', 'memory', 'cpu_info',
                    'screenshot', 'icon', 'graphics', 'users', 'groups',
                    'access', 'persistent', 'bootorder', 'bootmenu', 'title',
                    'description', 'autostart'))

        stats_keys = set(('cpu_utilization', 'mem_utilization',
                          'net_throughput', 'net_throughput_peak',
                          'io_throughput', 'io_throughput_peak'))

        info = model.vm_lookup(u'test-vm')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('shutoff', info['state'])
        self.assertEquals('test-vm', info['name'])
        self.assertEquals(get_template_default('old', 'memory'),
                          info['memory'])
        self.assertEquals(1, info['cpu_info']['vcpus'])
        self.assertEquals(1, info['cpu_info']['maxvcpus'])
        self.assertEquals('plugins/kimchi/images/icon-vm.png', info['icon'])
        self.assertEquals(stats_keys, set(info['stats'].keys()))
        self.assertEquals('vnc', info['graphics']['type'])
        self.assertEquals('127.0.0.1', info['graphics']['listen'])
