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

import cherrypy
import json
import os
import time
import unittest


import kimchi.mockmodel
from utils import get_free_port, patch_auth, request, run_server, wait_task
from kimchi.osinfo import get_template_default


test_server = None
model = None
host = None
port = None
ssl_port = None
fake_iso = None


def setUpModule():
    global host, port, ssl_port, model, test_server, fake_iso
    cherrypy.request.headers = {'Accept': 'application/json'}
    model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
    patch_auth()
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    host = '127.0.0.1'
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             model=model)
    fake_iso = '/tmp/fake.iso'
    open(fake_iso, 'w').close()


def tearDown():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')
    os.unlink(fake_iso)


class MockModelTests(unittest.TestCase):
    def setUp(self):
        model.reset()

    def test_screenshot_refresh(self):
        # Create a VM
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        request(host, ssl_port, '/templates', req, 'POST')
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        resp = request(host, ssl_port, '/vms', req, 'POST')
        task = json.loads(resp.read())
        wait_task(model.task_lookup, task['id'])

        # Test screenshot refresh for running vm
        request(host, ssl_port, '/vms/test-vm/start', '{}', 'POST')
        resp = request(host, ssl_port, '/vms/test-vm/screenshot')
        self.assertEquals(200, resp.status)
        self.assertEquals('image/png', resp.getheader('content-type'))
        resp1 = request(host, ssl_port, '/vms/test-vm')
        rspBody = resp1.read()
        testvm_Data = json.loads(rspBody)
        screenshotURL = testvm_Data['screenshot']
        time.sleep(5)
        resp2 = request(host, ssl_port, screenshotURL)
        self.assertEquals(200, resp2.status)
        self.assertEquals(resp2.getheader('content-type'),
                          resp.getheader('content-type'))
        self.assertEquals(resp2.getheader('content-length'),
                          resp.getheader('content-length'))
        self.assertEquals(resp2.getheader('last-modified'),
                          resp.getheader('last-modified'))

    def test_vm_list_sorted(self):
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        request(host, ssl_port, '/templates', req, 'POST')

        def add_vm(name):
            # Create a VM
            req = json.dumps({'name': name, 'template': '/templates/test'})
            task = json.loads(request(host, ssl_port, '/vms', req,
                              'POST').read())
            wait_task(model.task_lookup, task['id'])

        vms = [u'abc', u'bca', u'cab', u'xba']
        for vm in vms:
            add_vm(vm)

        vms.append(u'test')
        self.assertEqual(model.vms_get_list(), sorted(vms))

    def test_vm_info(self):
        model.templates_create({'name': u'test',
                                'cdrom': fake_iso})
        task = model.vms_create({'name': u'test-vm',
                                 'template': '/templates/test'})
        wait_task(model.task_lookup, task['id'])
        vms = model.vms_get_list()
        self.assertEquals(2, len(vms))
        self.assertIn(u'test-vm', vms)

        keys = set(('name', 'state', 'stats', 'uuid', 'memory', 'cpus',
                    'screenshot', 'icon', 'graphics', 'users', 'groups',
                    'access', 'persistent'))

        stats_keys = set(('cpu_utilization',
                          'net_throughput', 'net_throughput_peak',
                          'io_throughput', 'io_throughput_peak'))

        info = model.vm_lookup(u'test-vm')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('shutoff', info['state'])
        self.assertEquals('test-vm', info['name'])
        self.assertEquals(get_template_default('old', 'memory'),
                          info['memory'])
        self.assertEquals(1, info['cpus'])
        self.assertEquals('images/icon-vm.png', info['icon'])
        self.assertEquals(stats_keys, set(info['stats'].keys()))
        self.assertEquals('vnc', info['graphics']['type'])
        self.assertEquals('127.0.0.1', info['graphics']['listen'])
