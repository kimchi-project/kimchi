#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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
from utils import get_free_port, patch_auth, request, run_server
from utils import wait_task
from kimchi.control.base import Collection, Resource


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

    def test_collection(self):
        c = Collection(model)

        # The base Collection is always empty
        cherrypy.request.method = 'GET'
        self.assertEquals('[]', c.index())

        # POST and DELETE raise HTTP:405 by default
        for method in ('POST', 'DELETE'):
            cherrypy.request.method = method
            try:
                c.index()
            except cherrypy.HTTPError, e:
                self.assertEquals(405, e.code)
            else:
                self.fail("Expected exception not raised")

    def test_resource(self):
        r = Resource(model)

        # Test the base Resource representation
        cherrypy.request.method = 'GET'
        self.assertEquals('{}', r.index())

        # POST and DELETE raise HTTP:405 by default
        for method in ('POST', 'DELETE'):
            cherrypy.request.method = method
            try:
                r.index()
            except cherrypy.HTTPError, e:
                self.assertEquals(405, e.code)
            else:
                self.fail("Expected exception not raised")

    def test_template_cpu_info(self):
        template = self._create_default_template()
        # GET of cpu_info will be {}
        cpu_info = template['cpu_info']
        self.assertEquals(cpu_info, {})
        self.assertEquals(cpu_info.get('topology'), None)

        # Update topology
        # GET of cpu_info will contain 'topology'
        cpu_info_data = {'cpu_info': {'topology': {'sockets': 1,
                                                   'cores': 1,
                                                   'threads': 1}}}
        _, resp_code = self._send_url_request('PUT', '/templates/test',
                                              cpu_info_data)
        self.assertEquals(200, resp_code)

        updated_template, resp_code = \
            self._send_url_request('GET', '/templates/test')
        self.assertEquals(200, resp_code)
        self.assertEquals(updated_template['cpu_info'],
                          cpu_info_data['cpu_info'])

    def test_template_update_disk_type(self):
        def _get_default_disk_data(disk_type):
            return {'disks': [{'index': 0, 'format': disk_type, 'size': 10}]}

        template = self._create_default_template()
        # Default template is created with 1 disk without any declared
        # type.
        disk_data = template['disks']
        self.assertEquals(disk_data, [{'index': 0, 'size': 10}])

        # For all supported types, edit the template and check if
        # the change was made.
        disk_types = ['bochs', 'cloop', 'cow', 'dmg', 'qcow', 'qcow2',
                      'qed', 'raw', 'vmdk', 'vpc']
        for disk_type in disk_types:
            disk_data = _get_default_disk_data(disk_type)
            _, resp_code = self._send_url_request('PUT', '/templates/test',
                                                  disk_data)
            self.assertEquals(200, resp_code)

            updated_template, resp_code = \
                self._send_url_request('GET', '/templates/test')
            self.assertEquals(200, resp_code)
            self.assertEquals(updated_template['disks'], disk_data['disks'])

        # Check Bad Request when type is invalid
        bad_disk_data = _get_default_disk_data('invalid_disk_type')
        _, resp_code = self._send_url_request('PUT', '/templates/test',
                                              bad_disk_data)
        self.assertEquals(400, resp_code)

    def _create_default_template(self):
        params = {'name': 'test', 'cdrom': fake_iso}
        template, resp_code = self._send_url_request('POST', '/templates',
                                                     params)
        self.assertEquals(201, resp_code)
        return template

    def _send_url_request(self, method, url, data=None):
        req = None
        if data:
            req = json.dumps(data)
        resp = request(host, ssl_port, url, req, method)
        rsp_body = resp.read()
        return json.loads(rsp_body), resp.status

    def test_screenshot_refresh(self):
        # Create a VM
        req = json.dumps({'name': 'test', 'cdrom': fake_iso})
        request(host, ssl_port, '/templates', req, 'POST')
        req = json.dumps({'name': 'test-vm', 'template': '/templates/test'})
        request(host, ssl_port, '/vms', req, 'POST')

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
            request(host, ssl_port, '/vms', req, 'POST')

        vms = [u'abc', u'bca', u'cab', u'xba']
        for vm in vms:
            add_vm(vm)

        vms.append(u'test')
        self.assertEqual(model.vms_get_list(), sorted(vms))

    def test_vm_info(self):
        model.templates_create({'name': u'test',
                                'cdrom': fake_iso})
        model.vms_create({'name': u'test-vm', 'template': '/templates/test'})
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
        self.assertEquals(1024, info['memory'])
        self.assertEquals(1, info['cpus'])
        self.assertEquals('images/icon-vm.png', info['icon'])
        self.assertEquals(stats_keys, set(info['stats'].keys()))
        self.assertEquals('vnc', info['graphics']['type'])
        self.assertEquals('127.0.0.1', info['graphics']['listen'])

    def test_packages_update(self):
        pkgs = model.packagesupdate_get_list()
        self.assertEquals(3, len(pkgs))

        for pkg_name in pkgs:
            pkgupdate = model.packageupdate_lookup(pkg_name)
            self.assertIn('package_name', pkgupdate.keys())
            self.assertIn('repository', pkgupdate.keys())
            self.assertIn('arch', pkgupdate.keys())
            self.assertIn('version', pkgupdate.keys())

        task = model.host_swupdate()
        task_params = [u'id', u'message', u'status', u'target_uri']
        self.assertEquals(sorted(task_params), sorted(task.keys()))
        wait_task(model.task_lookup, task['id'])
