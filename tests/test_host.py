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
import platform
import psutil
import tempfile
import time
import unittest

from functools import partial

from kimchi.mockmodel import MockModel
from utils import get_free_port, patch_auth, request, run_server, wait_task

test_server = None
model = None
host = None
ssl_port = None
tmpfile = None


def setUpModule():
    global test_server, model, host, ssl_port, tmpfile

    patch_auth()
    tmpfile = tempfile.mktemp()
    model = MockModel(tmpfile)
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink(tmpfile)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)

    def test_hostinfo(self):
        resp = self.request('/host').read()
        info = json.loads(resp)
        keys = ['os_distro', 'os_version', 'os_codename', 'cpu_model',
                'memory', 'cpus']
        self.assertEquals(sorted(keys), sorted(info.keys()))

        distro, version, codename = platform.linux_distribution()
        self.assertEquals(distro, info['os_distro'])
        self.assertEquals(version, info['os_version'])
        self.assertEquals(unicode(codename, "utf-8"), info['os_codename'])
        self.assertEquals(psutil.TOTAL_PHYMEM, info['memory'])

    def test_hoststats(self):
        time.sleep(1)
        stats_keys = ['cpu_utilization', 'memory', 'disk_read_rate',
                      'disk_write_rate', 'net_recv_rate', 'net_sent_rate']
        resp = self.request('/host/stats').read()
        stats = json.loads(resp)
        self.assertEquals(sorted(stats_keys), sorted(stats.keys()))

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

        resp = self.request('/host/stats/history').read()
        history = json.loads(resp)
        self.assertEquals(sorted(stats_keys), sorted(history.keys()))

    def test_host_actions(self):
        def _task_lookup(taskid):
            return json.loads(self.request('/tasks/%s' % taskid).read())

        resp = self.request('/host/shutdown', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/host/reboot', '{}', 'POST')
        self.assertEquals(200, resp.status)

        # Test system update
        resp = self.request('/host/packagesupdate', None, 'GET')
        pkgs = json.loads(resp.read())
        self.assertEquals(3, len(pkgs))

        pkg_keys = ['package_name', 'repository', 'arch', 'version']
        for p in pkgs:
            name = p['package_name']
            resp = self.request('/host/packagesupdate/' + name, None, 'GET')
            info = json.loads(resp.read())
            self.assertEquals(sorted(pkg_keys), sorted(info.keys()))

        resp = self.request('/host/swupdate', '{}', 'POST')
        task = json.loads(resp.read())
        task_params = [u'id', u'message', u'status', u'target_uri']
        self.assertEquals(sorted(task_params), sorted(task.keys()))

        resp = self.request('/tasks/' + task[u'id'], None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'running')
        wait_task(_task_lookup, task_info['id'])
        resp = self.request('/tasks/' + task[u'id'], None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'finished')
        self.assertIn(u'All packages updated', task_info['message'])
        pkgs = model.packagesupdate_get_list()
        self.assertEquals(0, len(pkgs))

    def test_host_partitions(self):
        resp = self.request('/host/partitions')
        self.assertEquals(200, resp.status)
        partitions = json.loads(resp.read())

        keys = ['name', 'path', 'type', 'fstype', 'size', 'mountpoint',
                'available']
        for item in partitions:
            resp = self.request('/host/partitions/%s' % item['name'])
            info = json.loads(resp.read())
            self.assertEquals(sorted(info.keys()), sorted(keys))

    def test_host_devices(self):
        def asset_devices_type(devices, dev_type):
            for dev in devices:
                self.assertEquals(dev['device_type'], dev_type)

        resp = self.request('/host/devices?_cap=scsi_host')
        nodedevs = json.loads(resp.read())
        # Mockmodel brings 3 preconfigured scsi fc_host
        self.assertEquals(3, len(nodedevs))

        nodedev = json.loads(self.request('/host/devices/scsi_host2').read())
        # Mockmodel generates random wwpn and wwnn
        self.assertEquals('scsi_host2', nodedev['name'])
        self.assertEquals('fc_host', nodedev['adapter']['type'])
        self.assertEquals(16, len(nodedev['adapter']['wwpn']))
        self.assertEquals(16, len(nodedev['adapter']['wwnn']))

        devs = json.loads(self.request('/host/devices').read())
        dev_names = [dev['name'] for dev in devs]
        for dev_type in ('pci', 'usb_device', 'scsi'):
            resp = self.request('/host/devices?_cap=%s' % dev_type)
            devsByType = json.loads(resp.read())
            names = [dev['name'] for dev in devsByType]
            self.assertTrue(set(names) <= set(dev_names))
            asset_devices_type(devsByType, dev_type)

        resp = self.request('/host/devices?_passthrough=true')
        passthru_devs = [dev['name'] for dev in json.loads(resp.read())]
        self.assertTrue(set(passthru_devs) <= set(dev_names))

        for dev_type in ('pci', 'usb_device', 'scsi'):
            resp = self.request('/host/devices?_cap=%s&_passthrough=true' %
                                dev_type)
            filteredDevs = json.loads(resp.read())
            filteredNames = [dev['name'] for dev in filteredDevs]
            self.assertTrue(set(filteredNames) <= set(dev_names))
            asset_devices_type(filteredDevs, dev_type)

        for dev in passthru_devs:
            resp = self.request('/host/devices?_passthrough_affected_by=%s' %
                                dev)
            affected_devs = [dev['name'] for dev in json.loads(resp.read())]
            self.assertTrue(set(affected_devs) <= set(dev_names))
