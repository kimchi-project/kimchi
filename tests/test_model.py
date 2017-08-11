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

import __builtin__ as builtins

import base64
import grp
import libvirt
import json
import lxml.etree as ET
import mock
import os
import platform
import pwd
import re
import shutil
import time
import unittest

from lxml import objectify

import tests.utils as utils

import wok.objectstore
from wok.asynctask import AsyncTask
from wok.basemodel import Singleton
from wok.config import config, PluginPaths
from wok.exception import InvalidOperation
from wok.exception import InvalidParameter, NotFoundError, OperationFailed
from wok.rollbackcontext import RollbackContext
from wok.utils import convert_data_size
from wok.xmlutils.utils import xpath_get_text

from wok.plugins.kimchi import network as netinfo
from wok.plugins.kimchi import osinfo
from wok.plugins.kimchi.config import kimchiPaths as paths
from wok.plugins.kimchi.model import model
from wok.plugins.kimchi.model.libvirtconnection import LibvirtConnection
from wok.plugins.kimchi.model.virtviewerfile import FirewallManager
from wok.plugins.kimchi.model.virtviewerfile import VMVirtViewerFileModel
from wok.plugins.kimchi.model.vms import VMModel

import iso_gen


invalid_repository_urls = ['www.fedora.org',       # missing protocol
                           '://www.fedora.org',    # missing protocol
                           'http://www.fedora',    # invalid domain name
                           'file:///home/foobar']  # invalid path

TMP_DIR = '/var/lib/kimchi/tests/'
UBUNTU_ISO = TMP_DIR + 'ubuntu14.04.iso'
NON_NUMA_XML = """
<domain type='kvm'>
  <name>non-numa-kimchi-test</name>
  <maxMemory slots='2' unit='GiB'>4</maxMemory>
  <memory unit='GiB'>1</memory>
  <os>
    <type arch='ppc64'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
  </features>
</domain>"""


def setUpModule():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    iso_gen.construct_fake_iso(UBUNTU_ISO, True, '14.04', 'ubuntu')

    # Some FeatureTests functions depend on server to validate their result.
    # As CapabilitiesModel is a Singleton class it will get the first result
    # from FeatureTests which may be wrong when using the Model instance
    # directly - the case of this test_model.py
    # So clean Singleton instances to make sure to get the right result when
    # running the following tests.
    Singleton._instances = {}


def tearDownModule():
    shutil.rmtree(TMP_DIR)


def get_remote_iso_path():
    """
    Get a remote iso with the right arch from the distro files shipped
    with kimchi.
    """
    host_arch = os.uname()[4]
    remote_path = ''
    with open(os.path.join(PluginPaths('kimchi').conf_dir, 'distros.d',
              'fedora.json')) as fedora_isos:
        # Get a list of dicts
        json_isos_list = json.load(fedora_isos)
        for iso in json_isos_list:
            if (iso.get('os_arch')) == host_arch:
                remote_path = iso.get('path')
                break

    return remote_path


def _setDiskPoolDefault():
    osinfo.defaults['disks'][0]['pool'] = {
        'name': '/plugins/kimchi/storagepools/default'}


def _setDiskPoolDefaultTest():
    osinfo.defaults['disks'][0]['pool'] = {
        'name': '/plugins/kimchi/storagepools/default-pool'}


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/kimchi-store-test'

    def tearDown(self):
        # FIXME: Tests using 'test:///default' URI should be moved to
        # test_rest or test_mockmodel to avoid overriding problems
        LibvirtConnection._connections['test:///default'] = {}

        if os.path.isfile(self.tmp_store):
            os.unlink(self.tmp_store)

    def test_vm_info(self):
        inst = model.Model('test:///default', self.tmp_store)
        vms = inst.vms_get_list()
        self.assertEquals(1, len(vms))
        self.assertEquals('test', vms[0])

        keys = set(('name', 'state', 'stats', 'uuid', 'memory', 'cpu_info',
                    'screenshot', 'icon', 'graphics', 'users', 'groups',
                    'access', 'persistent', 'bootorder', 'bootmenu', 'title',
                    'description', 'autostart'))

        stats_keys = set(('cpu_utilization', 'mem_utilization',
                          'net_throughput', 'net_throughput_peak',
                          'io_throughput', 'io_throughput_peak'))
        info = inst.vm_lookup('test')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('running', info['state'])
        self.assertEquals('test', info['name'])
        self.assertEquals(2048, info['memory']['current'])
        self.assertEquals(2, info['cpu_info']['vcpus'])
        self.assertEquals(2, info['cpu_info']['maxvcpus'])
        self.assertEquals(None, info['icon'])
        self.assertEquals(stats_keys, set(info['stats'].keys()))
        self.assertRaises(NotFoundError, inst.vm_lookup, 'nosuchvm')
        self.assertEquals([], info['users'])
        self.assertEquals([], info['groups'])
        self.assertTrue(info['persistent'])

    @unittest.skipUnless(utils.running_as_root() and
                         os.uname()[4] != "s390x", 'Must be run as root')
    def test_vm_lifecycle(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            vol_params = {'name': u'test-vol', 'capacity': 1024}
            task = inst.storagevolumes_create(u'default', vol_params)
            rollback.prependDefer(inst.storagevolume_delete, u'default',
                                  vol_params['name'])
            inst.task_wait(task['id'])
            task = inst.task_lookup(task['id'])
            self.assertEquals('finished', task['status'])

            params = {'name': 'test',
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}

            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm',
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm-new')
            inst.task_wait(task['id'], 10)
            task = inst.task_lookup(task['id'])
            self.assertEquals('finished', task['status'])

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm' in vms)

            inst.vm_start('kimchi-vm')

            info = inst.vm_lookup('kimchi-vm')
            self.assertEquals('running', info['state'])

            task = inst.vmsnapshots_create(u'kimchi-vm')
            inst.task_wait(task['id'])
            task = inst.task_lookup(task['id'])
            self.assertEquals('finished', task['status'])
            snap_name = task['target_uri'].split('/')[-1]
            created_snaps = [snap_name]

            inst.vm_poweroff(u'kimchi-vm')
            vm = inst.vm_lookup(u'kimchi-vm')

            current_snap = inst.currentvmsnapshot_lookup(u'kimchi-vm')
            self.assertEquals(created_snaps[0], current_snap['name'])

            # this snapshot should be deleted when its VM is deleted
            params = {'name': u'mysnap'}
            task = inst.vmsnapshots_create(u'kimchi-vm', params)
            inst.task_wait(task['id'])
            task = inst.task_lookup(task['id'])
            self.assertEquals('finished', task['status'])
            created_snaps.append(params['name'])

            self.assertRaises(NotFoundError, inst.vmsnapshot_lookup,
                              u'kimchi-vm', u'foobar')

            snap = inst.vmsnapshot_lookup(u'kimchi-vm', params['name'])
            self.assertTrue(int(time.time()) >= int(snap['created']))
            self.assertEquals(vm['state'], snap['state'])
            self.assertEquals(params['name'], snap['name'])
            self.assertEquals(created_snaps[0], snap['parent'])

            snaps = inst.vmsnapshots_get_list(u'kimchi-vm')
            self.assertEquals(created_snaps, snaps)

            current_snap = inst.currentvmsnapshot_lookup(u'kimchi-vm')
            self.assertEquals(snap, current_snap)

            task = inst.vmsnapshots_create(u'kimchi-vm')
            snap_name = task['target_uri'].split('/')[-1]
            rollback.prependDefer(inst.vmsnapshot_delete,
                                  u'kimchi-vm-new', snap_name)
            inst.task_wait(task['id'])
            task = inst.task_lookup(task['id'])
            self.assertEquals('finished', task['status'])
            created_snaps.append(snap_name)

            snaps = inst.vmsnapshots_get_list(u'kimchi-vm')
            self.assertEquals(sorted(created_snaps, key=unicode.lower), snaps)

            snap = inst.vmsnapshot_lookup(u'kimchi-vm', snap_name)
            current_snap = inst.currentvmsnapshot_lookup(u'kimchi-vm')
            self.assertEquals(snap, current_snap)

            # update vm name
            inst.vm_update('kimchi-vm', {'name': u'kimchi-vm-new'})

            # Look up the first created snapshot from the renamed vm
            snap = inst.vmsnapshot_lookup(u'kimchi-vm-new', params['name'])

            # snapshot revert to the first created vm
            result = inst.vmsnapshot_revert(u'kimchi-vm-new', params['name'])
            self.assertEquals(result, ['kimchi-vm-new', snap['name']])

            vm = inst.vm_lookup(u'kimchi-vm-new')
            self.assertEquals(vm['state'], snap['state'])

            current_snap = inst.currentvmsnapshot_lookup(u'kimchi-vm-new')
            self.assertEquals(params['name'], current_snap['name'])

            # suspend and resume the VM
            info = inst.vm_lookup(u'kimchi-vm-new')
            self.assertEquals(info['state'], 'shutoff')
            self.assertRaises(InvalidOperation, inst.vm_suspend,
                              u'kimchi-vm-new')
            inst.vm_start(u'kimchi-vm-new')
            info = inst.vm_lookup(u'kimchi-vm-new')
            self.assertEquals(info['state'], 'running')
            inst.vm_suspend(u'kimchi-vm-new')
            info = inst.vm_lookup(u'kimchi-vm-new')
            self.assertEquals(info['state'], 'paused')
            self.assertRaises(InvalidParameter, inst.vm_update,
                              u'kimchi-vm-new', {'name': 'foo'})
            inst.vm_resume(u'kimchi-vm-new')
            info = inst.vm_lookup(u'kimchi-vm-new')
            self.assertEquals(info['state'], 'running')
            self.assertRaises(InvalidOperation, inst.vm_resume,
                              u'kimchi-vm-new')
            # leave the VM suspended to make sure a paused VM can be
            # deleted correctly
            inst.vm_suspend('kimchi-vm-new')

        vms = inst.vms_get_list()
        self.assertFalse('kimchi-vm-new' in vms)

    @unittest.skipUnless(utils.running_as_root() and
                         os.uname()[4] != "s390x", 'Must be run as root')
    def test_image_based_template(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            vol = 'base-vol.img'
            params = {'name': vol,
                      'capacity': 1073741824,  # 1 GiB
                      'allocation': 1048576,  # 1 MiB
                      'format': 'qcow2'}
            task_id = inst.storagevolumes_create('default', params)['id']
            rollback.prependDefer(inst.storagevolume_delete, 'default', vol)
            inst.task_wait(task_id)
            self.assertEquals('finished', inst.task_lookup(task_id)['status'])
            vol_path = inst.storagevolume_lookup('default', vol)['path']

            # Create template based on IMG file
            tmpl_name = "img-tmpl"
            tmpl_info = {"cpu_info": {"vcpus": 1}, "name": tmpl_name,
                         "graphics": {"type": "vnc", "listen": "127.0.0.1"},
                         "networks": ["default"], "memory": {'current': 1024},
                         "folder": [], "icon": "images/icon-vm.png",
                         "os_distro": "unknown", "os_version": "unknown",
                         "source_media": {'type': 'disk', 'path': vol_path}}

            inst.templates_create(tmpl_info)
            rollback.prependDefer(inst.template_delete, tmpl_name)

            # verify disk
            tmpl = inst.template_lookup(tmpl_name)
            self.assertEquals(vol_path, tmpl["disks"][0]["base"])

            params = {'name': 'kimchi-vm',
                      'template': '/plugins/kimchi/templates/img-tmpl'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm' in vms)

            inst.vm_start('kimchi-vm')
            rollback.prependDefer(inst.vm_poweroff, 'kimchi-vm')

            info = inst.vm_lookup('kimchi-vm')
            self.assertEquals('running', info['state'])

    @unittest.skipUnless(utils.running_as_root() and
                         os.uname()[4] != "s390x", 'Must be run as root')
    def test_vm_graphics(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        params = {'name': 'test',
                  'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
        inst.templates_create(params)
        with RollbackContext() as rollback:
            params = {'name': 'kimchi-graphics',
                      'template': '/plugins/kimchi/templates/test'}
            task1 = inst.vms_create(params)
            inst.task_wait(task1['id'])
            rollback.prependDefer(inst.vm_delete, 'kimchi-graphics')

            info = inst.vm_lookup('kimchi-graphics')
            self.assertEquals('vnc', info['graphics']['type'])
            self.assertEquals('127.0.0.1', info['graphics']['listen'])

            graphics = {'type': 'spice'}
            params = {'graphics': graphics}
            inst.vm_update('kimchi-graphics', params)

            info = inst.vm_lookup('kimchi-graphics')
            self.assertEquals('spice', info['graphics']['type'])
            self.assertEquals('127.0.0.1', info['graphics']['listen'])

        inst.template_delete('test')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_virtviewerfile_vmnotrunning(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        params = {'name': 'test',
                  'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
        inst.templates_create(params)

        vm_name = 'kìmchí-vñç'

        with RollbackContext() as rollback:
            params = {'name': vm_name.decode('utf-8'),
                      'template': '/plugins/kimchi/templates/test'}
            task1 = inst.vms_create(params)
            inst.task_wait(task1['id'])
            rollback.prependDefer(inst.vm_delete, vm_name.decode('utf-8'))

            error_msg = "KCHVM0083E"
            with self.assertRaisesRegexp(InvalidOperation, error_msg):
                vvmodel = VMVirtViewerFileModel(conn=inst.conn)
                vvmodel.lookup(vm_name.decode('utf-8'))

        inst.template_delete('test')

    @mock.patch('wok.plugins.kimchi.model.virtviewerfile._get_request_host')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'VMModel.get_graphics')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'FirewallManager.add_vm_graphics_port')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'VMVirtViewerFileModel.handleVMShutdownPowerOff')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'VMVirtViewerFileModel._check_if_vm_running')
    def test_vm_virtviewerfile_vnc(self, mock_vm_running, mock_handleVMOff,
                                   mock_add_port, mock_get_graphics,
                                   mock_get_host):

        mock_get_host.return_value = 'kimchi-test-host'
        mock_get_graphics.return_value = ['vnc', 'listen', '5999', None]
        mock_vm_running.return_value = True

        vvmodel = VMVirtViewerFileModel(conn=None)

        open_ = mock.mock_open(read_data='')
        with mock.patch.object(builtins, 'open', open_):
            vvfilepath = vvmodel.lookup('kimchi-vm')

        self.assertEqual(
            vvfilepath,
            'plugins/kimchi/data/virtviewerfiles/kimchi-vm-access.vv'
        )

        expected_write_content = "[virt-viewer]\ntype=vnc\n"\
            "host=kimchi-test-host\nport=5999\n"
        self.assertEqual(
            open_().write.mock_calls, [mock.call(expected_write_content)]
        )

        mock_get_graphics.assert_called_once_with('kimchi-vm', None)
        mock_vm_running.assert_called_once_with('kimchi-vm')
        mock_handleVMOff.assert_called_once_with('kimchi-vm')
        mock_add_port.assert_called_once_with('kimchi-vm', '5999')

    @mock.patch('wok.plugins.kimchi.model.virtviewerfile._get_request_host')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'VMModel.get_graphics')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'FirewallManager.add_vm_graphics_port')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'VMVirtViewerFileModel.handleVMShutdownPowerOff')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'VMVirtViewerFileModel._check_if_vm_running')
    def test_vm_virtviewerfile_spice_passwd(self, mock_vm_running,
                                            mock_handleVMOff,
                                            mock_add_port,
                                            mock_get_graphics,
                                            mock_get_host):

        mock_get_host.return_value = 'kimchi-test-host'
        mock_get_graphics.return_value = [
            'spice', 'listen', '6660', 'spicepasswd'
        ]
        mock_vm_running.return_value = True

        vvmodel = VMVirtViewerFileModel(conn=None)

        open_ = mock.mock_open(read_data='')
        with mock.patch.object(builtins, 'open', open_):
            vvfilepath = vvmodel.lookup('kimchi-vm')

        self.assertEqual(
            vvfilepath,
            'plugins/kimchi/data/virtviewerfiles/kimchi-vm-access.vv'
        )

        expected_write_content = "[virt-viewer]\ntype=spice\n"\
            "host=kimchi-test-host\nport=6660\npassword=spicepasswd\n"
        self.assertEqual(
            open_().write.mock_calls, [mock.call(expected_write_content)]
        )

        mock_get_graphics.assert_called_once_with('kimchi-vm', None)
        mock_vm_running.assert_called_once_with('kimchi-vm')
        mock_handleVMOff.assert_called_once_with('kimchi-vm')
        mock_add_port.assert_called_once_with('kimchi-vm', '6660')

    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.run_command')
    def test_firewall_provider_firewallcmd(self, mock_run_cmd):
        mock_run_cmd.side_effect = [
            ['', '', 0], ['', '', 0], ['', '', 0]
        ]

        fw_manager = FirewallManager()
        fw_manager.add_vm_graphics_port('vm-name', 5905)
        self.assertEqual(fw_manager.opened_ports, {'vm-name': 5905})

        fw_manager.remove_vm_graphics_port('vm-name')
        self.assertEqual(fw_manager.opened_ports, {})

        mock_run_cmd.assert_has_calls(
            [mock.call(['firewall-cmd', '--state', '-q']),
             mock.call(['firewall-cmd', '--add-port=5905/tcp']),
             mock.call(['firewall-cmd', '--remove-port=5905/tcp'])])

    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.run_command')
    def test_firewall_provider_ufw(self, mock_run_cmd):
        mock_run_cmd.side_effect = [
            ['', '', 1], ['', '', 0], ['', '', 0], ['', '', 0]
        ]

        fw_manager = FirewallManager()
        fw_manager.add_vm_graphics_port('vm-name', 5905)
        self.assertEqual(fw_manager.opened_ports, {'vm-name': 5905})

        fw_manager.remove_vm_graphics_port('vm-name')
        self.assertEqual(fw_manager.opened_ports, {})

        mock_run_cmd.assert_has_calls(
            [mock.call(['firewall-cmd', '--state', '-q']),
             mock.call(['ufw', 'status']),
             mock.call(['ufw', 'allow', '5905/tcp']),
             mock.call(['ufw', 'deny', '5905/tcp'])])

    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.run_command')
    def test_firewall_provider_iptables(self, mock_run_cmd):
        mock_run_cmd.side_effect = [
            ['', '', 1], ['', '', 1], ['', '', 0], ['', '', 0]
        ]

        fw_manager = FirewallManager()
        fw_manager.add_vm_graphics_port('vm-name', 5905)
        self.assertEqual(fw_manager.opened_ports, {'vm-name': 5905})

        fw_manager.remove_vm_graphics_port('vm-name')
        self.assertEqual(fw_manager.opened_ports, {})

        iptables_add = ['iptables', '-I', 'INPUT', '-p', 'tcp', '--dport',
                        5905, '-j', 'ACCEPT']

        iptables_del = ['iptables', '-D', 'INPUT', '-p', 'tcp', '--dport',
                        5905, '-j', 'ACCEPT']

        mock_run_cmd.assert_has_calls(
            [mock.call(['firewall-cmd', '--state', '-q']),
             mock.call(['ufw', 'status']),
             mock.call(iptables_add), mock.call(iptables_del)])

    @unittest.skipUnless(utils.running_as_root() and
                         os.uname()[4] != "s390x", 'Must be run as root')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'FirewallManager.remove_vm_graphics_port')
    @mock.patch('wok.plugins.kimchi.model.virtviewerfile.'
                'FirewallManager.add_vm_graphics_port')
    def test_vm_virtviewerfile_vmlifecycle(self, mock_add_port,
                                           mock_remove_port):

        inst = model.Model(objstore_loc=self.tmp_store)
        params = {'name': 'test',
                  'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
        inst.templates_create(params)

        vm_name = 'kìmçhí-vñç'

        with RollbackContext() as rollback:
            params = {'name': u'%s' % vm_name.decode('utf-8'),
                      'template': '/plugins/kimchi/templates/test'}
            task1 = inst.vms_create(params)
            inst.task_wait(task1['id'])
            rollback.prependDefer(inst.vm_delete, vm_name.decode('utf-8'))

            inst.vm_start(vm_name.decode('utf-8'))

            graphics_info = VMModel.get_graphics(vm_name.decode('utf-8'),
                                                 inst.conn)
            graphics_port = graphics_info[2]

            vvmodel = VMVirtViewerFileModel(conn=inst.conn)
            vvmodel.lookup(vm_name.decode('utf-8'))

            inst.vm_poweroff(vm_name.decode('utf-8'))
            time.sleep(5)

            mock_add_port.assert_called_once_with(vm_name.decode('utf-8'),
                                                  graphics_port)
            mock_remove_port.assert_called_once_with(
                base64.b64encode(vm_name)
            )

        inst.template_delete('test')

    @unittest.skipUnless(utils.running_as_root() and
                         os.uname()[4] != "s390x", "Must be run as root")
    def test_vm_serial(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        params = {'name': 'test',
                  'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
        inst.templates_create(params)
        with RollbackContext() as rollback:
            params = {'name': 'kimchi-serial',
                      'template': '/plugins/kimchi/templates/test'}
            task1 = inst.vms_create(params)
            inst.task_wait(task1['id'])
            rollback.prependDefer(inst.vm_delete, 'kimchi-serial')

            inst.vm_start('kimchi-serial')
            rollback.prependDefer(inst.vm_poweroff, 'kimchi-serial')

            with self.assertRaises(OperationFailed):
                inst.vm_serial('kimchi-serial')

        inst.template_delete('test')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_ifaces(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            params = {'name': 'test',
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            # Create a network
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)
            rollback.prependDefer(inst.network_delete, net_name)
            inst.network_activate(net_name)
            rollback.prependDefer(inst.network_deactivate, net_name)

            for vm_name in ['kimchi-ifaces', 'kimchi-ifaces-running']:
                params = {'name': vm_name,
                          'template': '/plugins/kimchi/templates/test'}
                task = inst.vms_create(params)
                inst.task_wait(task['id'])
                rollback.prependDefer(inst.vm_delete, vm_name)

                ifaces = inst.vmifaces_get_list(vm_name)
                if not os.uname()[4] == "s390x":
                    self.assertEquals(1, len(ifaces))

                    iface = inst.vmiface_lookup(vm_name, ifaces[0])
                    self.assertEquals(17, len(iface['mac']))
                    self.assertEquals("default", iface['network'])
                    self.assertIn("model", iface)

                # attach network interface to vm
                iface_args = {"type": "network",
                              "network": "test-network",
                              "model": "virtio"}
                mac = inst.vmifaces_create(vm_name, iface_args)
                # detach network interface from vm
                rollback.prependDefer(inst.vmiface_delete, vm_name, mac)
                self.assertEquals(17, len(mac))

                iface = inst.vmiface_lookup(vm_name, mac)
                self.assertEquals("network", iface["type"])
                self.assertEquals("test-network", iface['network'])
                self.assertEquals("virtio", iface["model"])

                # attach network interface to vm without providing model
                iface_args = {"type": "network",
                              "network": "test-network"}
                mac = inst.vmifaces_create(vm_name, iface_args)
                rollback.prependDefer(inst.vmiface_delete, vm_name, mac)

                iface = inst.vmiface_lookup(vm_name, mac)
                self.assertEquals("network", iface["type"])
                self.assertEquals("test-network", iface['network'])

                # update vm interface
                newMacAddr = '54:50:e3:44:8a:af'
                iface_args = {"mac": newMacAddr}
                inst.vmiface_update(vm_name, mac, iface_args)
                iface = inst.vmiface_lookup(vm_name, newMacAddr)
                self.assertEquals(newMacAddr, iface['mac'])

                # undo mac address change
                iface_args = {"mac": mac}
                inst.vmiface_update(vm_name, newMacAddr, iface_args)
                iface = inst.vmiface_lookup(vm_name, mac)
                self.assertEquals(mac, iface['mac'])

                if os.uname()[4] == "s390x":

                    # attach macvtap interface to vm
                    iface_args = {"type": "macvtap",
                                  "source": "test-network",
                                  "mode": "vepa"}
                    mac = inst.vmifaces_create(vm_name, iface_args)
                    rollback.prependDefer(inst.vmiface_delete, vm_name, mac)

                    iface = inst.vmiface_lookup(vm_name, mac)
                    self.assertEquals("macvtap", iface["type"])
                    self.assertEquals("test-network", iface['source'])
                    self.assertEquals("vepa", iface['mode'])

                    # attach ovs interface to vm
                    iface_args = {"type": "ovs",
                                  "source": "test-network"}
                    mac = inst.vmifaces_create(vm_name, iface_args)
                    rollback.prependDefer(inst.vmiface_delete, vm_name, mac)

                    iface = inst.vmiface_lookup(vm_name, mac)
                    self.assertEquals("ovs", iface["type"])
                    self.assertEquals("test-network", iface['source'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_netboot(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            params = {'name': 'test-netboot',
                      'source_media': {'type': 'netboot'}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test-netboot')

            params = {'name': 'kimchi-netboot-vm',
                      'template': '/plugins/kimchi/templates/test-netboot'}
            task = inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-netboot-vm')
            inst.task_wait(task['id'], 10)
            task = inst.task_lookup(task['id'])
            self.assertEquals('finished', task['status'])

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-netboot-vm' in vms)

            inst.vm_start('kimchi-netboot-vm')

            info = inst.vm_lookup('kimchi-netboot-vm')
            self.assertEquals('running', info['state'])

            inst.vm_poweroff(u'kimchi-netboot-vm')

        vms = inst.vms_get_list()
        self.assertFalse('kimchi-netboot-vm' in vms)

    @unittest.skipUnless(utils.running_as_root() and
                         os.uname()[4] != "s390x", 'Must be run as root')
    def test_vm_disk(self):
        disk_path = os.path.join(TMP_DIR, 'existent2.iso')
        open(disk_path, 'w').close()
        modern_disk_bus = osinfo.get_template_default('modern', 'disk_bus')

        def _attach_disk(expect_bus=modern_disk_bus):
            disk_args = {"type": "disk",
                         "pool": pool,
                         "vol": vol}
            disk = inst.vmstorages_create(vm_name, disk_args)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count + 1, len(storage_list))

            # Check the bus type to be 'virtio'
            disk_info = inst.vmstorage_lookup(vm_name, disk)
            self.assertEquals(u'disk', disk_info['type'])
            self.assertEquals(vol_path, disk_info['path'])
            self.assertEquals(expect_bus, disk_info['bus'])
            return disk

        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            path = os.path.join(TMP_DIR, 'kimchi-images')
            pool = 'test-pool'
            vol = 'test-volume.img'
            vol_path = "%s/%s" % (path, vol)
            if not os.path.exists(path):
                os.mkdir(path)
            rollback.prependDefer(shutil.rmtree, path)

            args = {'name': pool,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, pool)

            # Activate the pool before adding any volume
            inst.storagepool_activate(pool)
            rollback.prependDefer(inst.storagepool_deactivate, pool)

            params = {'name': vol,
                      'capacity': 1073741824,  # 1 GiB
                      'allocation': 536870912,  # 512 MiB
                      'format': 'qcow2'}
            task_id = inst.storagevolumes_create(pool, params)['id']
            rollback.prependDefer(inst.storagevolume_delete, pool, vol)
            inst.task_wait(task_id)

            vm_name = 'kimchi-cdrom'
            params = {'name': 'test', 'disks': [],
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            params = {'name': vm_name,
                      'template': '/plugins/kimchi/templates/test'}
            task1 = inst.vms_create(params)
            inst.task_wait(task1['id'])
            rollback.prependDefer(inst.vm_delete, vm_name)

            prev_count = len(inst.vmstorages_get_list(vm_name))
            self.assertEquals(1, prev_count)

            # Volume format with mismatched type raise error
            cdrom_args = {"type": "cdrom", "pool": pool, "vol": vol}
            self.assertRaises(InvalidParameter, inst.vmstorages_create,
                              vm_name, cdrom_args)

            # Cold plug and unplug a disk
            disk = _attach_disk()
            inst.vmstorage_delete(vm_name, disk)

            # Hot plug a disk
            inst.vm_start(vm_name)
            disk = _attach_disk()

            # VM disk still there after powered off
            inst.vm_poweroff(vm_name)
            disk_info = inst.vmstorage_lookup(vm_name, disk)
            self.assertEquals(u'disk', disk_info['type'])
            inst.vmstorage_delete(vm_name, disk)

            # Specifying pool and path at same time will fail
            disk_args = {"type": "disk",
                         "pool": pool,
                         "vol": vol,
                         "path": disk_path}
            self.assertRaises(
                InvalidParameter, inst.vmstorages_create, vm_name, disk_args)

            old_distro_iso = TMP_DIR + 'rhel4_8.iso'
            iso_gen.construct_fake_iso(old_distro_iso, True, '4.8', 'rhel')

            vm_name = 'kimchi-ide-bus-vm'
            params = {'name': 'old_distro_template', 'disks': [],
                      'source_media': {'type': 'disk', 'path': old_distro_iso}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'old_distro_template')
            params = {
                'name': vm_name,
                'template': '/plugins/kimchi/templates/old_distro_template'
            }
            task2 = inst.vms_create(params)
            inst.task_wait(task2['id'])
            rollback.prependDefer(inst.vm_delete, vm_name)

            # Need to check the right disk_bus for old distro
            disk = _attach_disk(osinfo.get_template_default('old', 'disk_bus'))
            inst.vmstorage_delete('kimchi-ide-bus-vm', disk)

            # Hot plug IDE bus disk does not work
            inst.vm_start(vm_name)
            self.assertRaises(InvalidOperation, _attach_disk)
            inst.vm_poweroff(vm_name)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_cdrom(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            vm_name = 'kimchi-cdrom'
            params = {'name': 'test', 'disks': [],
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            params = {'name': vm_name,
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, vm_name)

            prev_count = len(inst.vmstorages_get_list(vm_name))
            self.assertEquals(1, prev_count)

            # dummy .iso files
            iso_path = os.path.join(TMP_DIR, 'existent.iso')
            iso_path2 = os.path.join(TMP_DIR, 'existent2.iso')
            open(iso_path, 'w').close()
            rollback.prependDefer(os.remove, iso_path)
            open(iso_path2, 'w').close()
            rollback.prependDefer(os.remove, iso_path2)
            wrong_iso_path = '/nonexistent.iso'

            # Create a cdrom
            cdrom_args = {"type": "cdrom",
                          "path": iso_path}
            cdrom_dev = inst.vmstorages_create(vm_name, cdrom_args)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count + 1, len(storage_list))

            # Get cdrom info
            cd_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(u'cdrom', cd_info['type'])
            self.assertEquals(iso_path, cd_info['path'])

            # update path of existing cd with
            # non existent iso
            self.assertRaises(InvalidParameter, inst.vmstorage_update,
                              vm_name, cdrom_dev, {'path': wrong_iso_path})

            # Make sure CD ROM still exists after failure
            cd_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(u'cdrom', cd_info['type'])
            self.assertEquals(iso_path, cd_info['path'])

            # update path of existing cd with existent iso of shutoff vm
            inst.vmstorage_update(vm_name, cdrom_dev, {'path': iso_path2})
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(iso_path2, cdrom_info['path'])

            # update path of existing cd with existent iso of running vm
            inst.vm_start(vm_name)
            inst.vmstorage_update(vm_name, cdrom_dev, {'path': iso_path})
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(iso_path, cdrom_info['path'])

            # eject cdrom
            cdrom_dev = inst.vmstorage_update(vm_name, cdrom_dev, {'path': ''})
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals('', cdrom_info['path'])
            inst.vm_poweroff(vm_name)

            # removing non existent cdrom
            self.assertRaises(NotFoundError, inst.vmstorage_delete, vm_name,
                              "fakedev")

            # removing valid cdrom
            inst.vmstorage_delete(vm_name, cdrom_dev)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count, len(storage_list))

            # Create a new cdrom using a remote iso
            valid_remote_iso_path = get_remote_iso_path()
            cdrom_args = {"type": "cdrom",
                          "path": valid_remote_iso_path}
            cdrom_dev = inst.vmstorages_create(vm_name, cdrom_args)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count + 1, len(storage_list))

            # Update remote-backed cdrom with the same ISO
            inst.vmstorage_update(vm_name, cdrom_dev,
                                  {'path': valid_remote_iso_path})
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            cur_cdrom_path = re.sub(":80/", '/', cdrom_info['path'])
            self.assertEquals(valid_remote_iso_path, cur_cdrom_path)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_storage_provisioning(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [{'size': 1, 'pool': {
                      'name': '/plugins/kimchi/storagepools/default'}}],
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}

            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'test-vm-1',
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')

            vm_info = inst.vm_lookup(params['name'])
            disk_path = '%s/%s-0.img' % (
                inst.storagepool_lookup('default')['path'], vm_info['uuid'])
            self.assertTrue(os.access(disk_path, os.F_OK))
        self.assertFalse(os.access(disk_path, os.F_OK))

    def _create_template_conf_with_disk_format(self, vol_format):
        if vol_format is None:
            conf_file_data = "[main]\n\n[storage]\n\n[[disk.0]]\n" \
                             "#format = \n\n[graphics]\n\n[processor]\n"
        else:
            conf_file_data = "[main]\n\n[storage]\n\n[[disk.0]]\n" \
                             "format = %s\n\n[graphics]\n\n[processor]\n"\
                             % vol_format

        config_file = os.path.join(paths.sysconf_dir, 'template.conf')
        config_bkp_file = \
            os.path.join(paths.sysconf_dir, 'template.conf-unit_test_bkp')

        os.rename(config_file, config_bkp_file)

        with open(config_file, 'w') as f:
            f.write(conf_file_data)

        osinfo.defaults = osinfo._get_tmpl_defaults()

    def _restore_template_conf_file(self):
        config_file = os.path.join(paths.sysconf_dir, 'template.conf')
        config_bkp_file = \
            os.path.join(paths.sysconf_dir, 'template.conf-unit_test_bkp')
        os.rename(config_bkp_file, config_file)
        osinfo.defaults = osinfo._get_tmpl_defaults()

    def _get_disk_format_from_vm(self, vm, conn):
        dom = VMModel.get_vm(vm, conn)
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='disk']/driver/@type"
        return xpath_get_text(xml, xpath)[0]

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_get_default_vol_format_from_conf(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            self._create_template_conf_with_disk_format('vmdk')
            rollback.prependDefer(self._restore_template_conf_file)

            params = {'name': 'test', 'disks': [{'size': 1, 'pool': {
                      'name': '/plugins/kimchi/storagepools/default'}}],
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'test-vm-1',
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')

            created_disk_format = self._get_disk_format_from_vm(
                'test-vm-1', inst.conn
            )
            self.assertEqual(created_disk_format, 'vmdk')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_creates_user_defined_vol_format_instead_default(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        default_vol = 'vmdk'
        user_vol = 'raw'
        with RollbackContext() as rollback:
            self._create_template_conf_with_disk_format(default_vol)
            rollback.prependDefer(self._restore_template_conf_file)

            params = {'name': 'test', 'disks': [{
                'size': 1, 'format': user_vol,
                'pool': {'name': '/plugins/kimchi/storagepools/default'}}],
                'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}

            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'test-vm-1',
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')

            created_disk_format = self._get_disk_format_from_vm(
                'test-vm-1', inst.conn
            )
            self.assertEqual(created_disk_format, user_vol)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_uses_qcow2_format_if_no_user_or_default_defined(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            self._create_template_conf_with_disk_format(None)
            rollback.prependDefer(self._restore_template_conf_file)

            params = {'name': 'test', 'disks': [{'size': 1, 'pool': {
                      'name': '/plugins/kimchi/storagepools/default'}}],
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'test-vm-1',
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')

            created_disk_format = self._get_disk_format_from_vm(
                'test-vm-1', inst.conn
            )
            self.assertEqual(created_disk_format, 'qcow2')

    def test_vm_memory_hotplug(self):
        config.set("authentication", "method", "pam")
        inst = model.Model(None, objstore_loc=self.tmp_store)
        orig_params = {'name': 'test',
                       'memory': {'current': 1024,
                                  'maxmemory': 4096
                                  if os.uname()[4] != "s390x" else 2048},
                       'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
        inst.templates_create(orig_params)

        with RollbackContext() as rollback:
            params = {'name': 'kimchi-vm1',
                      'template': '/plugins/kimchi/templates/test'}
            task1 = inst.vms_create(params)
            inst.task_wait(task1['id'])
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_delete,
                                  'kimchi-vm1')
            # Start vm
            inst.vm_start('kimchi-vm1')
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_poweroff,
                                  'kimchi-vm1')

            # Hotplug memory, only available in Libvirt >= 1.2.14
            params = {'memory': {'current': 2048}}
            if inst.capabilities_lookup()['mem_hotplug_support']:
                inst.vm_update('kimchi-vm1', params)
                rollback.prependDefer(utils.rollback_wrapper, inst.vm_delete,
                                      'kimchi-vm1')
                params['memory']['maxmemory'] = 4096
                self.assertEquals(params['memory'],
                                  inst.vm_lookup('kimchi-vm1')['memory'])

                params['memory']['current'] = 4096
                del params['memory']['maxmemory']
                inst.vm_update('kimchi-vm1', params)
                vm = inst.vm_lookup('kimchi-vm1')
                self.assertEquals(4096, vm['memory']['current'])

                # Test memory devices
                conn = inst.conn.get()
                xml = conn.lookupByName('kimchi-vm1').XMLDesc()
                root = ET.fromstring(xml)
                devs = root.findall('./devices/memory/target/size')
                self.assertEquals(2, len(devs))
                totMemDevs = 0
                for size in devs:
                    totMemDevs += convert_data_size(size.text,
                                                    size.get('unit'),
                                                    'MiB')
                self.assertEquals(3072, totMemDevs)

                inst.vm_poweroff('kimchi-vm1')
                # Remove all devs:
                params = {'memory': {'current': 1024}}
                inst.vm_update('kimchi-vm1', params)
                xml = conn.lookupByName('kimchi-vm1').XMLDesc()
                root = ET.fromstring(xml)
                devs = root.findall('./devices/memory')
                self.assertEquals(0, len(devs))

                # Hotplug 1G DIMM , 512M , 256M and 256M
                inst.vm_start('kimchi-vm1')
                params = {'memory': {'current': 2048}}
                inst.vm_update('kimchi-vm1', params)
                params = {'memory': {'current': 2560}}
                inst.vm_update('kimchi-vm1', params)
                params = {'memory': {'current': 2816}}
                inst.vm_update('kimchi-vm1', params)
                params = {'memory': {'current': 3072}}
                inst.vm_update('kimchi-vm1', params)

                vm = inst.vm_lookup('kimchi-vm1')
                self.assertEquals(3072, vm['memory']['current'])

                xml = conn.lookupByName('kimchi-vm1').XMLDesc()
                root = ET.fromstring(xml)
                devs = root.findall('./devices/memory/target/size')
                self.assertEquals(4, len(devs))
                totMemDevs = 0
                for size in devs:
                    totMemDevs += convert_data_size(size.text,
                                                    size.get('unit'),
                                                    'MiB')
                self.assertEquals(2048, totMemDevs)

                inst.vm_poweroff('kimchi-vm1')
                # Remove 2x256M + 1x512M ... then sum 256M to virtual memory
                params = {'memory': {'current': 2304}}
                inst.vm_update('kimchi-vm1', params)
                xml = conn.lookupByName('kimchi-vm1').XMLDesc()
                root = ET.fromstring(xml)
                devs = root.findall('./devices/memory/target/size')
                self.assertEquals(1, len(devs))
                totMemDevs = 0
                for size in devs:
                    totMemDevs += convert_data_size(size.text,
                                                    size.get('unit'),
                                                    'MiB')
                self.assertEquals(1024, totMemDevs)
            else:
                self.assertRaises(InvalidOperation, inst.vm_update,
                                  'kimchi-vm1', params)

    msg = "Memory hotplug in non-numa guests only for PowerPC arch."

    @unittest.skipUnless(('ppc64' in os.uname()[4]), msg)
    def test_non_numa_vm_memory_hotplug(self):
        config.set("authentication", "method", "pam")
        inst = model.Model(None, objstore_loc=self.tmp_store)
        conn = inst.conn.get()
        vm = 'non-numa-kimchi-test'

        with RollbackContext() as rollback:
            conn.defineXML(NON_NUMA_XML)
            rollback.prependDefer(conn.lookupByName(vm).undefine)

            # Start vm
            inst.vm_start(vm)

            # Hotplug memory
            params = {'memory': {'current': 3072}}
            inst.vm_update(vm, params)
            self.assertEquals(params['memory']['current'],
                              inst.vm_lookup(vm)['memory']['current'])

            # Test number and size of memory device added
            root = ET.fromstring(conn.lookupByName(vm).XMLDesc())
            devs = root.findall('./devices/memory/target/size')
            self.assertEquals(1, len(devs))
            self.assertEquals(2048 << 10, int(devs[0].text))

            params = {'memory': {'current': 4096}}
            inst.vm_update(vm, params)
            self.assertEquals(params['memory']['current'],
                              inst.vm_lookup(vm)['memory']['current'])

            # Test number and size of memory device added
            root = ET.fromstring(conn.lookupByName(vm).XMLDesc())
            devs = root.findall('./devices/memory/target/size')
            self.assertEquals(2, len(devs))
            self.assertEquals(1024 << 10, int(devs[1].text))
            self.assertEquals(3072 << 10,
                              int(devs[0].text) + int(devs[1].text))

            # Stop vm and test persistence
            inst.vm_poweroff(vm)
            self.assertEquals(params['memory']['current'],
                              inst.vm_lookup(vm)['memory']['current'])

    def test_vm_edit(self):
        config.set("authentication", "method", "pam")
        inst = model.Model(None,
                           objstore_loc=self.tmp_store)

        # template disk format must be qcow2 because vmsnapshot
        # only supports this format
        orig_params = {
            'name': 'test', 'memory': {'current': 1024, 'maxmemory': 2048},
            'cpu_info': {'vcpus': 1},
            'source_media': {'type': 'disk', 'path': UBUNTU_ISO},
            'disks': [{'size': 1, 'format': 'qcow2', 'pool': {
                       'name': '/plugins/kimchi/storagepools/default'}}]}
        inst.templates_create(orig_params)

        with RollbackContext() as rollback:
            params_1 = {'name': 'kimchi-vm1',
                        'template': '/plugins/kimchi/templates/test'}
            params_2 = {'name': 'kimchi-vm2',
                        'template': '/plugins/kimchi/templates/test'}
            task1 = inst.vms_create(params_1)
            inst.task_wait(task1['id'])
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_delete,
                                  'kimchi-vm1')
            task2 = inst.vms_create(params_2)
            inst.task_wait(task2['id'])
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_delete,
                                  'kimchi-vm2')

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm1' in vms)

            # make sure "vm_update" works when the domain has a snapshot
            inst.vmsnapshots_create(u'kimchi-vm1')

            if os.uname()[4] != "s390x":
                # update vm graphics when vm is not running
                inst.vm_update(u'kimchi-vm1',
                               {"graphics": {"passwd": "123456"}})

                inst.vm_start('kimchi-vm1')
                rollback.prependDefer(utils.rollback_wrapper, inst.vm_poweroff,
                                      'kimchi-vm1')

                vm_info = inst.vm_lookup(u'kimchi-vm1')
                self.assertEquals('123456', vm_info['graphics']["passwd"])
                self.assertEquals(None, vm_info['graphics']["passwdValidTo"])

                # update vm graphics when vm is running
                inst.vm_update(u'kimchi-vm1',
                               {"graphics": {"passwd": "abcdef",
                                             "passwdValidTo": 20}})
                vm_info = inst.vm_lookup(u'kimchi-vm1')
                self.assertEquals('abcdef', vm_info['graphics']["passwd"])
                self.assertGreaterEqual(20,
                                        vm_info['graphics']['passwdValidTo'])

                info = inst.vm_lookup('kimchi-vm1')
                self.assertEquals('running', info['state'])

                params = {'name': 'new-vm'}
                self.assertRaises(InvalidParameter, inst.vm_update,
                                  'kimchi-vm1', params)
            else:
                inst.vm_start('kimchi-vm1')

            # change VM users and groups, when wm is running.
            inst.vm_update(u'kimchi-vm1',
                           {'users': ['root'], 'groups': ['root']})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals(['root'], vm_info['users'])
            self.assertEquals(['root'], vm_info['groups'])

            # change VM users and groups by removing all elements,
            # when vm is running.
            inst.vm_update(u'kimchi-vm1', {'users': [], 'groups': []})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals([], vm_info['users'])
            self.assertEquals([], vm_info['groups'])

            # power off vm
            inst.vm_poweroff('kimchi-vm1')
            self.assertRaises(OperationFailed, inst.vm_update,
                              'kimchi-vm1', {'name': 'kimchi-vm2'})

            # update maxvcpus only
            inst.vm_update(u'kimchi-vm1', {'cpu_info': {'maxvcpus': 8}})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals(8, vm_info['cpu_info']['maxvcpus'])

            # update vcpus only
            inst.vm_update(u'kimchi-vm1', {'cpu_info': {'vcpus': 4}})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals(4, vm_info['cpu_info']['vcpus'])

            # vcpus > maxvcpus: failure
            self.assertRaises(InvalidParameter, inst.vm_update, u'kimchi-vm1',
                              {'cpu_info': {'vcpus': 10}})

            # define CPU topology
            inst.vm_update(u'kimchi-vm1', {'cpu_info': {'topology': {
                           'sockets': 2, 'cores': 2, 'threads': 2}}})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals({'sockets': 2, 'cores': 2, 'threads': 2},
                              vm_info['cpu_info']['topology'])

            # vcpus not a multiple of threads
            self.assertRaises(InvalidParameter, inst.vm_update, u'kimchi-vm1',
                              {'cpu_info': {'vcpus': 5}})

            # maxvcpus different of (sockets * cores * threads)
            self.assertRaises(InvalidParameter, inst.vm_update, u'kimchi-vm1',
                              {'cpu_info': {'maxvcpus': 4}})

            # topology does not match maxvcpus (8 != 3 * 2 * 2)
            self.assertRaises(InvalidParameter, inst.vm_update, u'kimchi-vm1',
                              {'cpu_info': {'topology': {
                               'sockets': 3, 'cores': 2, 'threads': 2}}})

            # undefine CPU topology
            inst.vm_update(u'kimchi-vm1', {'cpu_info': {'topology': {}}})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals({}, vm_info['cpu_info']['topology'])

            # reduce maxvcpus to same as vcpus
            inst.vm_update(u'kimchi-vm1', {'cpu_info': {'maxvcpus': 4}})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals(4, vm_info['cpu_info']['maxvcpus'])

            # rename and increase memory when vm is not running
            params = {'name': u'пeω-∨м',
                      'memory': {'current': 2048}}
            inst.vm_update('kimchi-vm1', params)
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_delete,
                                  u'пeω-∨м')
            self.assertEquals(vm_info['uuid'],
                              inst.vm_lookup(u'пeω-∨м')['uuid'])
            info = inst.vm_lookup(u'пeω-∨м')
            # Max memory is returned, add to test
            params['memory']['maxmemory'] = 2048
            for key in params.keys():
                self.assertEquals(params[key], info[key])

            # change only VM users - groups are not changed (default is empty)
            users = inst.users_get_list()[:3]
            inst.vm_update(u'пeω-∨м', {'users': users})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals([], inst.vm_lookup(u'пeω-∨м')['groups'])

            # change only VM groups - users are not changed (default is empty)
            groups = inst.groups_get_list()[:2]
            inst.vm_update(u'пeω-∨м', {'groups': groups})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users and groups by adding a new element to each one
            users.append(pwd.getpwuid(os.getuid()).pw_name)
            groups.append(grp.getgrgid(os.getgid()).gr_name)
            inst.vm_update(u'пeω-∨м', {'users': users, 'groups': groups})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users (wrong value) and groups
            # when an error occurs, everything fails and nothing is changed
            self.assertRaises(InvalidParameter, inst.vm_update, u'пeω-∨м',
                              {'users': ['userdoesnotexist'], 'groups': []})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users and groups (wrong value)
            # when an error occurs, everything fails and nothing is changed
            self.assertRaises(InvalidParameter, inst.vm_update, u'пeω-∨м',
                              {'users': [], 'groups': ['groupdoesnotexist']})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users and groups by removing all elements
            inst.vm_update(u'пeω-∨м', {'users': [], 'groups': []})
            self.assertEquals([], inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals([], inst.vm_lookup(u'пeω-∨м')['groups'])

            # change bootorder
            b_order = ["hd", "network", "cdrom"]
            inst.vm_update(u'пeω-∨м', {"bootorder": b_order})
            self.assertEquals(b_order, inst.vm_lookup(u'пeω-∨м')['bootorder'])

            # try to add empty list
            self.assertRaises(OperationFailed, inst.vm_update, u'пeω-∨м',
                              {"bootorder": [""]})

            # try to pass invalid parameter
            self.assertRaises(OperationFailed, inst.vm_update, u'пeω-∨м',
                              {"bootorder": ["bla"]})

            # enable/disable bootmenu
            inst.vm_update(u'пeω-∨м', {"bootmenu": True})
            self.assertEquals("yes", inst.vm_lookup(u'пeω-∨м')['bootmenu'])
            inst.vm_update(u'пeω-∨м', {"bootmenu": False})
            self.assertEquals("no", inst.vm_lookup(u'пeω-∨м')['bootmenu'])

    def test_get_vm_cpu_cores(self):
        xml = """<domain type='kvm'>\
<cpu><topology sockets='3' cores='2' threads='8'/></cpu>\
</domain>"""
        inst = model.Model(None, objstore_loc=self.tmp_store)
        self.assertEqual('2', inst.vm_get_vm_cpu_cores(xml))

    def test_get_vm_cpu_sockets(self):
        xml = """<domain type='kvm'>\
<cpu><topology sockets='3' cores='2' threads='8'/></cpu>\
</domain>"""
        inst = model.Model(None, objstore_loc=self.tmp_store)
        self.assertEqual('3', inst.vm_get_vm_cpu_sockets(xml))

    def test_get_vm_cpu_threads(self):
        xml = """<domain type='kvm'>\
<cpu><topology sockets='3' cores='2' threads='8'/></cpu>\
</domain>"""
        inst = model.Model(None, objstore_loc=self.tmp_store)
        self.assertEqual('8', inst.vm_get_vm_cpu_threads(xml))

    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.has_topology')
    def test_get_vm_cpu_topology(self, mock_has_topology):
        class FakeDom():
            def XMLDesc(self, flag):
                return """<domain type='kvm'>\
<cpu><topology sockets='3' cores='2' threads='8'/></cpu>\
</domain>"""

            def name(self):
                return 'fakedom'

        mock_has_topology.return_value = True
        expected_topology = {'sockets': 3, 'cores': 2, 'threads': 8}

        inst = model.Model(None, objstore_loc=self.tmp_store)
        self.assertEqual(expected_topology,
                         inst.vm_get_vm_cpu_topology(FakeDom()))

    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.has_topology')
    def test_get_vm_cpu_topology_blank(self, mock_has_topology):
        class FakeDom():
            def XMLDesc(self, flag):
                return """<domain type='kvm'></domain>"""

            def name(self):
                return 'fakedom'

        mock_has_topology.return_value = False
        expected_topology = {}

        inst = model.Model(None, objstore_loc=self.tmp_store)
        self.assertEqual(expected_topology,
                         inst.vm_get_vm_cpu_topology(FakeDom()))

    def test_vm_cpu_hotplug_invalidparam_fail(self):
        inst = model.Model(None, objstore_loc=self.tmp_store)

        with self.assertRaisesRegexp(InvalidParameter, 'KCHCPUHOTP0001E'):
            params = {"cpu_info": {"vcpus": 1, 'maxvcpus': 4}}
            inst.vm_cpu_hotplug_precheck('', params)

    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.has_topology')
    def test_vm_cpu_hotplug_abovemax_fail(self, mock_has_topology):
        class FakeDom():
            def XMLDesc(self, flag):
                return """<domain type='kvm'>\
<vcpu placement='static' current='1'>8</vcpu><\
/domain>"""

            def name(self):
                return 'fakedom'

        mock_has_topology.return_value = False
        inst = model.Model(None, objstore_loc=self.tmp_store)

        with self.assertRaisesRegexp(InvalidParameter, 'KCHCPUINF0001E'):
            params = {"cpu_info": {"vcpus": 16}}
            inst.vm_cpu_hotplug_precheck(FakeDom(), params)

    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.has_topology')
    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.get_vm_cpu_topology')
    def test_vm_cpu_hotplug_topology_mismatch_fail(self, mock_topology,
                                                   mock_has_topology):
        class FakeDom():
            def XMLDesc(self, flag):
                return """<domain type='kvm'>\
<vcpu placement='static' current='8'>48</vcpu><\
/domain>"""

            def name(self):
                return 'fakedom'

        mock_has_topology.return_value = True
        mock_topology.return_value = {'sockets': 3, 'cores': 2, 'threads': 8}

        inst = model.Model(None, objstore_loc=self.tmp_store)

        with self.assertRaisesRegexp(InvalidParameter, 'KCHCPUINF0005E'):
            params = {"cpu_info": {"vcpus": 10}}
            inst.vm_cpu_hotplug_precheck(FakeDom(), params)

    def test_vm_cpu_hotplug_error(self):
        class FakeDom():
            def setVcpusFlags(self, vcpu, flags):
                raise libvirt.libvirtError('')

        inst = model.Model(None, objstore_loc=self.tmp_store)
        with self.assertRaisesRegexp(OperationFailed, 'KCHCPUHOTP0002E'):
            inst.vm_update_cpu_live(FakeDom(), '')

            # enable/disable autostart
            inst.vm_update(u'пeω-∨м', {"autostart": True})
            self.assertEquals(1, inst.vm_lookup(u'пeω-∨м')['autostart'])
            inst.vm_update(u'пeω-∨м', {"autostart": False})
            self.assertEquals(0, inst.vm_lookup(u'пeω-∨м')['autostart'])

    def test_get_interfaces(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        expected_ifaces = netinfo.all_favored_interfaces()
        ifaces = inst.interfaces_get_list()
        self.assertEquals(len(expected_ifaces), len(ifaces))
        for name in expected_ifaces:
            iface = inst.interface_lookup(name)
            self.assertEquals(iface['name'], name)
            self.assertIn('type', iface)
            self.assertIn('status', iface)
            self.assertIn('ipaddr', iface)
            self.assertIn('netmask', iface)

    def test_async_tasks(self):
        class task_except(Exception):
            pass

        def quick_op(cb, message):
            cb(message, True)

        def long_op(cb, params):
            time.sleep(params.get('delay', 3))
            cb(params.get('message', ''), params.get('result', False))

        def abnormal_op(cb, params):
            try:
                raise task_except
            except:
                cb("Exception raised", False)

        def continuous_ops(cb, params):
            cb("step 1 OK")
            time.sleep(2)
            cb("step 2 OK")
            time.sleep(2)
            cb("step 3 OK", params.get('result', True))

        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        taskid = AsyncTask('', quick_op, 'Hello').id
        inst.task_wait(taskid)
        self.assertEquals('finished', inst.task_lookup(taskid)['status'])
        self.assertEquals('Hello', inst.task_lookup(taskid)['message'])

        params = {'delay': 3, 'result': False,
                  'message': 'It was not meant to be'}
        taskid = AsyncTask('', long_op, params).id
        self.assertEquals('running', inst.task_lookup(taskid)['status'])
        self.assertEquals('The request is being processing.',
                          inst.task_lookup(taskid)['message'])
        inst.task_wait(taskid)
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])
        self.assertEquals('It was not meant to be',
                          inst.task_lookup(taskid)['message'])
        taskid = AsyncTask('', abnormal_op, {}).id
        inst.task_wait(taskid)
        self.assertEquals('Exception raised',
                          inst.task_lookup(taskid)['message'])
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])

        taskid = AsyncTask('', continuous_ops, {'result': True}).id
        self.assertEquals('running', inst.task_lookup(taskid)['status'])
        inst.task_wait(taskid, timeout=10)
        self.assertEquals('finished', inst.task_lookup(taskid)['status'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_delete_running_vm(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': u'test', 'disks': [],
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': u'kīмсhī-∨м',
                      'template': u'/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_delete,
                                  u'kīмсhī-∨м')

            inst.vm_start(u'kīмсhī-∨м')
            self.assertEquals(inst.vm_lookup(u'kīмсhī-∨м')['state'], 'running')
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_poweroff,
                                  u'kīмсhī-∨м')

            inst.vm_delete(u'kīмсhī-∨м')

            vms = inst.vms_get_list()
            self.assertFalse(u'kīмсhī-∨м' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_list_sorted(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [],
                      'source_media': {'type': 'disk', 'path': UBUNTU_ISO}}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm',
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertEquals(vms, sorted(vms, key=unicode.lower))

    def test_vm_clone(self):
        inst = model.Model('test:///default', objstore_loc=self.tmp_store)

        all_vm_names = inst.vms_get_list()
        name = all_vm_names[0]

        original_vm = inst.vm_lookup(name)
        if original_vm['state'] == u'shutoff':
            inst.vm_start(name)

        # the VM 'test' should be running by now, so we can't clone it yet
        self.assertRaises(InvalidParameter, inst.vm_clone, name)

        with RollbackContext() as rollback:
            inst.vm_poweroff(name)
            rollback.prependDefer(inst.vm_start, name)

            # create two simultaneous clones of the same VM
            # and make sure both of them complete successfully
            task1 = inst.vm_clone(name)
            task2 = inst.vm_clone(name)
            clone1_name = task1['target_uri'].split('/')[-2]
            rollback.prependDefer(inst.vm_delete, clone1_name)
            clone2_name = task2['target_uri'].split('/')[-2]
            rollback.prependDefer(inst.vm_delete, clone2_name)
            inst.task_wait(task1['id'])
            task1 = inst.task_lookup(task1['id'])
            self.assertEquals('finished', task1['status'])
            inst.task_wait(task2['id'])
            task2 = inst.task_lookup(task2['id'])
            self.assertEquals('finished', task2['status'])

            # update the original VM info because its state has changed
            original_vm = inst.vm_lookup(name)
            clone_vm = inst.vm_lookup(clone1_name)

            self.assertNotEqual(original_vm['name'], clone_vm['name'])
            self.assertTrue(re.match(u'%s-clone-\d+' % original_vm['name'],
                                     clone_vm['name']))
            del original_vm['name']
            del clone_vm['name']

            self.assertNotEqual(original_vm['uuid'], clone_vm['uuid'])
            del original_vm['uuid']
            del clone_vm['uuid']

            # compare all VM settings except the ones already compared
            # (and removed) above (i.e. 'name' and 'uuid')
            self.assertEquals(original_vm, clone_vm)

    def test_use_test_host(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {
                'name': 'test',
                'source_media': {'type': 'disk', 'path': UBUNTU_ISO},
                'domain': 'test',
                'arch': 'i686',
                'disks': []
            }

            _setDiskPoolDefaultTest()
            rollback.prependDefer(_setDiskPoolDefault)

            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm',
                      'template': '/plugins/kimchi/templates/test'}
            task = inst.vms_create(params)
            inst.task_wait(task['id'])
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertTrue('kimchi-vm' in vms)

    def test_get_distros(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        distros = inst.distros_get_list()
        for d in distros:
            distro = inst.distro_lookup(d)
            self.assertIn('name', distro)
            self.assertIn('os_distro', distro)
            self.assertIn('os_version', distro)
            self.assertIn('os_arch', distro)
            self.assertIn('path', distro)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_deep_scan(self):
        inst = model.Model(None,
                           objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            deep_path = os.path.join(TMP_DIR, 'deep-scan')
            subdir_path = os.path.join(deep_path, 'isos')
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)
            ubuntu_iso = os.path.join(deep_path, 'ubuntu12.04.iso')
            sles_iso = os.path.join(subdir_path, 'sles10.iso')
            iso_gen.construct_fake_iso(ubuntu_iso, True, '12.04', 'ubuntu')
            iso_gen.construct_fake_iso(sles_iso, True, '10', 'sles')

            args = {'name': 'kimchi-scanning-pool',
                    'path': deep_path,
                    'type': 'kimchi-iso'}
            inst.storagepools_create(args)
            rollback.prependDefer(shutil.rmtree, deep_path)
            rollback.prependDefer(shutil.rmtree, args['path'])
            rollback.prependDefer(inst.storagepool_deactivate, args['name'])

            time.sleep(1)
            volumes = inst.storagevolumes_get_list(args['name'])
            self.assertEquals(len(volumes), 2)

    def _host_is_power():
        return platform.machine().startswith('ppc')

    @unittest.skipUnless(_host_is_power(), 'Only required for Power hosts')
    def test_pci_hotplug_requires_usb_controller(self):
        config.set("authentication", "method", "pam")
        inst = model.Model(None, objstore_loc=self.tmp_store)
        tpl_params = {'name': 'test', 'memory': 1024, 'cdrom': UBUNTU_ISO}
        inst.templates_create(tpl_params)

        with RollbackContext() as rollback:
            vm_params = {'name': 'kimchi-vm1', 'template': '/templates/test'}
            task1 = inst.vms_create(vm_params)
            inst.task_wait(task1['id'])
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_delete,
                                  'kimchi-vm1')
            # Start vm
            inst.vm_start('kimchi-vm1')
            rollback.prependDefer(utils.rollback_wrapper, inst.vm_poweroff,
                                  'kimchi-vm1')
            # check if create VM has USB controller
            self.assertTrue(
                inst.vmhostdevs_have_usb_controller('kimchi-vm1'))

    def get_hostdevs_xml(self):
        return """\
<domain type='kvm' id='N'>
  <name>vm_name</name>
  <devices>
    <emulator>/usr/bin/qemu-kvm</emulator>
    <hostdev mode='subsystem' type='pci' managed='yes'>
      <driver name='vfio'/>
      <source>
        <address domain='0x0001' bus='0x0d' slot='0x00' function='0x1'/>
      </source>
      <alias name='hostdev0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' \
function='0x1'/>
    </hostdev>
    <hostdev mode='subsystem' type='pci' managed='yes'>
      <driver name='vfio'/>
      <source>
        <address domain='0x0001' bus='0x0d' slot='0x00' function='0x0'/>
      </source>
      <alias name='hostdev1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' \
function='0x0' multifunction='on'/>
    </hostdev>
    <hostdev mode='subsystem' type='pci' managed='yes'>
      <driver name='vfio'/>
      <source>
        <address domain='0x0001' bus='0x0d' slot='0x00' function='0x2'/>
      </source>
      <alias name='hostdev2'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' \
function='0x0'/>
    </hostdev>
    <hostdev mode='subsystem' type='pci' managed='yes'>
      <driver name='vfio'/>
      <source>
        <address domain='0x0001' bus='0x0d' slot='0x00' function='0x4'/>
      </source>
      <alias name='hostdev3'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' \
function='0x0'/>
    </hostdev>
    <hostdev mode='subsystem' type='pci' managed='yes'>
      <driver name='vfio'/>
      <source>
        <address domain='0x0001' bus='0x0d' slot='0x00' function='0x5'/>
      </source>
      <alias name='hostdev4'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x08' \
function='0x0'/>
    </hostdev>
  </devices>
 </domain>
"""

    def get_hostdev_multifunction_xml(self):
        return """\
<hostdev mode='subsystem' type='pci' managed='yes'>
  <driver name='vfio'/>
  <source>
    <address domain='0x0001' bus='0x0d' slot='0x00' function='0x0'/>
  </source>
  <alias name='hostdev1'/>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0' \
multifunction='on'/>
</hostdev>
"""

    def get_hostdev_nomultifunction_xml(self):
        return """\
<hostdev mode='subsystem' type='pci' managed='yes'>
  <driver name='vfio'/>
  <source>
    <address domain='0x0001' bus='0x0d' slot='0x00' function='0x5'/>
  </source>
  <alias name='hostdev4'/>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x08' function='0x0'/>
</hostdev>
"""

    def test_vmhostdev_is_hostdev_multifunction(self):
        inst = model.Model(None, objstore_loc=self.tmp_store)

        hostdev_multi_elem = objectify.fromstring(
            self.get_hostdev_multifunction_xml()
        )
        self.assertTrue(
            inst.vmhostdev_is_hostdev_multifunction(hostdev_multi_elem)
        )

        hostdev_nomulti_elem = objectify.fromstring(
            self.get_hostdev_nomultifunction_xml()
        )
        self.assertFalse(
            inst.vmhostdev_is_hostdev_multifunction(hostdev_nomulti_elem)
        )

    def test_vmhostdev_get_devices_same_addr(self):
        inst = model.Model(None, objstore_loc=self.tmp_store)

        root = objectify.fromstring(self.get_hostdevs_xml())
        hostdevs = root.devices.hostdev

        hostdev_multi_elem = objectify.fromstring(
            self.get_hostdev_multifunction_xml()
        )

        hostdev_same_addr_str = """\
<hostdev mode="subsystem" type="pci" managed="yes"><driver name="vfio"/>\
<source><address domain="0x0001" bus="0x0d" slot="0x00" function="0x1"/>\
</source><alias name="hostdev0"/>\
<address type="pci" domain="0x0000" bus="0x00" slot="0x05" function="0x1"/>\
</hostdev>"""
        same_addr_devices = [
            ET.tostring(hostdev_multi_elem), hostdev_same_addr_str
        ]

        self.assertItemsEqual(
            same_addr_devices,
            inst.vmhostdev_get_devices_same_addr(hostdevs, hostdev_multi_elem)
        )

        nomatch_elem = objectify.fromstring(
            self.get_hostdev_nomultifunction_xml()
        )

        self.assertEqual(
            inst.vmhostdev_get_devices_same_addr(hostdevs, nomatch_elem),
            [ET.tostring(nomatch_elem)]
        )

    @mock.patch('wok.plugins.kimchi.model.vmhostdevs.get_vm_config_flag')
    def test_vmhostdev_unplug_multifunction_pci(self, mock_conf_flag):
        class FakeDom():
            def detachDeviceFlags(self, xml, config_flag):
                pass

        mock_conf_flag.return_value = ''

        inst = model.Model(None, objstore_loc=self.tmp_store)

        root = objectify.fromstring(self.get_hostdevs_xml())
        hostdevs = root.devices.hostdev

        hostdev_multi_elem = objectify.fromstring(
            self.get_hostdev_multifunction_xml()
        )

        self.assertTrue(
            inst.vmhostdev_unplug_multifunction_pci(FakeDom(), hostdevs,
                                                    hostdev_multi_elem)
        )

        nomatch_elem = objectify.fromstring(
            self.get_hostdev_nomultifunction_xml()
        )

        self.assertFalse(
            inst.vmhostdev_unplug_multifunction_pci(FakeDom(), hostdevs,
                                                    nomatch_elem)
        )


class BaseModelTests(unittest.TestCase):
    class FoosModel(object):
        def __init__(self):
            self.data = {}

        def create(self, params):
            self.data.update(params)

        def get_list(self):
            return list(self.data)

    class TestModel(wok.basemodel.BaseModel):
        def __init__(self):
            foo = BaseModelTests.FoosModel()
            super(BaseModelTests.TestModel, self).__init__([foo])

    def test_root_model(self):
        t = BaseModelTests.TestModel()
        t.foos_create({'item1': 10})
        self.assertEquals(t.foos_get_list(), ['item1'])
