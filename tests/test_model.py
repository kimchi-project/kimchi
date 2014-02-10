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

import os
import platform
import psutil
import tempfile
import threading
import time
import unittest
import uuid


import iso_gen
import kimchi.objectstore
import utils
from kimchi import netinfo
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.iscsi import TargetClient
from kimchi.model import model
from kimchi.rollbackcontext import RollbackContext
from kimchi.utils import add_task


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/kimchi-store-test'

    def tearDown(self):
        os.unlink(self.tmp_store)

    def test_vm_info(self):
        inst = model.Model('test:///default', self.tmp_store)
        vms = inst.vms_get_list()
        self.assertEquals(1, len(vms))
        self.assertEquals('test', vms[0])

        keys = set(('state', 'stats', 'uuid', 'memory', 'cpus', 'screenshot',
                    'icon', 'graphics'))
        stats_keys = set(('cpu_utilization',
                          'net_throughput', 'net_throughput_peak',
                          'io_throughput', 'io_throughput_peak'))
        info = inst.vm_lookup('test')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('running', info['state'])
        self.assertEquals(2048, info['memory'])
        self.assertEquals(2, info['cpus'])
        self.assertEquals(None, info['icon'])
        self.assertEquals(stats_keys, set(eval(info['stats']).keys()))
        self.assertRaises(NotFoundError, inst.vm_lookup, 'nosuchvm')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_lifecycle(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': []}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm' in vms)

            inst.vm_start('kimchi-vm')
            rollback.prependDefer(inst.vm_stop, 'kimchi-vm')

            info = inst.vm_lookup('kimchi-vm')
            self.assertEquals('running', info['state'])

        vms = inst.vms_get_list()
        self.assertFalse('kimchi-vm' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_graphics(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        params = {'name': 'test', 'disks': []}
        inst.templates_create(params)
        with RollbackContext() as rollback:
            params = {'name': 'kimchi-vnc', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vnc')

            info = inst.vm_lookup('kimchi-vnc')
            self.assertEquals('vnc', info['graphics']['type'])
            self.assertEquals('0.0.0.0', info['graphics']['listen'])

            graphics = {'type': 'spice', 'listen': '127.0.0.1'}
            params = {'name': 'kimchi-spice', 'template': '/templates/test',
                      'graphics': graphics}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-spice')

            info = inst.vm_lookup('kimchi-spice')
            self.assertEquals('spice', info['graphics']['type'])
            self.assertEquals('127.0.0.1', info['graphics']['listen'])

        inst.template_delete('test')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_ifaces(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': []}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            params = {'name': 'kimchi-ifaces', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-ifaces')

            # Create a network
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)
            rollback.prependDefer(inst.network_delete, net_name)

            ifaces = inst.vmifaces_get_list('kimchi-ifaces')
            self.assertEquals(1, len(ifaces))

            iface = inst.vmiface_lookup('kimchi-ifaces', ifaces[0])
            self.assertEquals(17, len(iface['mac']))
            self.assertEquals("default", iface['network'])
            self.assertIn("model", iface)

            # attach network interface to vm
            iface_args = {"type": "network",
                          "network": "test-network",
                          "model": "virtio"}
            mac = inst.vmifaces_create('kimchi-ifaces', iface_args)
            self.assertEquals(17, len(mac))
            # detach network interface from vm
            rollback.prependDefer(inst.vmiface_delete, 'kimchi-ifaces', mac)

            iface = inst.vmiface_lookup('kimchi-ifaces', mac)
            self.assertEquals("network", iface["type"])
            self.assertEquals("test-network", iface['network'])
            self.assertEquals("virtio", iface["model"])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_storage_provisioning(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [{'size': 1}]}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'test-vm-1', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')

            vm_info = inst.vm_lookup(params['name'])
            disk_path = '/var/lib/libvirt/images/%s-0.img' % vm_info['uuid']
            self.assertTrue(os.access(disk_path, os.F_OK))
        self.assertFalse(os.access(disk_path, os.F_OK))

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_storagepool(self):
        inst = model.Model('qemu:///system', self.tmp_store)

        poolDefs = [
            {'type': 'dir',
             'name': u'kīмсhīUnitTestDirPool',
             'path': '/tmp/kimchi-images'},
            {'type': 'iscsi',
             'name': u'kīмсhīUnitTestISCSIPool',
             'source': {'host': '127.0.0.1',
                        'target': 'iqn.2013-12.localhost.kimchiUnitTest'}}]

        for poolDef in poolDefs:
            with RollbackContext() as rollback:
                path = poolDef.get('path')
                name = poolDef['name']

                if poolDef['type'] == 'iscsi':
                    if not TargetClient(**poolDef['source']).validate():
                        continue

                pools = inst.storagepools_get_list()
                num = len(pools) + 1

                inst.storagepools_create(poolDef)
                rollback.prependDefer(inst.storagepool_delete, name)

                pools = inst.storagepools_get_list()
                self.assertEquals(num, len(pools))

                poolinfo = inst.storagepool_lookup(name)
                if path is not None:
                    self.assertEquals(path, poolinfo['path'])
                self.assertEquals('inactive', poolinfo['state'])
                if poolinfo['type'] == 'dir':
                    self.assertEquals(True, poolinfo['autostart'])
                else:
                    self.assertEquals(False, poolinfo['autostart'])

                inst.storagepool_activate(name)
                rollback.prependDefer(inst.storagepool_deactivate, name)

                poolinfo = inst.storagepool_lookup(name)
                self.assertEquals('active', poolinfo['state'])

                autostart = poolinfo['autostart']
                ori_params = {'autostart':
                              True} if autostart else {'autostart': False}
                for i in [True, False]:
                    params = {'autostart': i}
                    inst.storagepool_update(name, params)
                    rollback.prependDefer(inst.storagepool_update, name,
                                          ori_params)
                    poolinfo = inst.storagepool_lookup(name)
                    self.assertEquals(i, poolinfo['autostart'])
                inst.storagepool_update(name, ori_params)

        pools = inst.storagepools_get_list()
        self.assertIn('default', pools)
        poolinfo = inst.storagepool_lookup('default')
        self.assertEquals('active', poolinfo['state'])
        self.assertEquals((num - 1), len(pools))

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_storagevolume(self):
        inst = model.Model('qemu:///system', self.tmp_store)

        with RollbackContext() as rollback:
            path = '/tmp/kimchi-images'
            pool = 'test-pool'
            vol = 'test-volume.img'
            if not os.path.exists(path):
                os.mkdir(path)

            args = {'name': pool,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, pool)

            self.assertRaises(InvalidOperation, inst.storagevolumes_get_list,
                              pool)
            poolinfo = inst.storagepool_lookup(pool)
            self.assertEquals(0, poolinfo['nr_volumes'])
            # Activate the pool before adding any volume
            inst.storagepool_activate(pool)
            rollback.prependDefer(inst.storagepool_deactivate, pool)

            vols = inst.storagevolumes_get_list(pool)
            num = len(vols) + 2
            params = {'name': vol,
                      'capacity': 1024,
                      'allocation': 512,
                      'format': 'raw'}
            inst.storagevolumes_create(pool, params)
            rollback.prependDefer(inst.storagevolume_delete, pool, vol)

            fd, path = tempfile.mkstemp(dir=path)
            name = os.path.basename(path)
            rollback.prependDefer(inst.storagevolume_delete, pool, name)
            vols = inst.storagevolumes_get_list(pool)
            self.assertIn(name, vols)
            self.assertEquals(num, len(vols))

            inst.storagevolume_wipe(pool, vol)
            volinfo = inst.storagevolume_lookup(pool, vol)
            self.assertEquals(0, volinfo['allocation'])

            volinfo = inst.storagevolume_lookup(pool, vol)
            # Define the size = capacity + 16M
            capacity = volinfo['capacity'] >> 20
            size = capacity + 16
            inst.storagevolume_resize(pool, vol, size)

            volinfo = inst.storagevolume_lookup(pool, vol)
            self.assertEquals((1024 + 16) << 20, volinfo['capacity'])
            poolinfo = inst.storagepool_lookup(pool)
            self.assertEquals(len(vols), poolinfo['nr_volumes'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_storage_customise(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            path = '/tmp/kimchi-images'
            pool = 'test-pool'
            if not os.path.exists(path):
                os.mkdir(path)

            params = {'name': 'test', 'disks': [{'size': 1}]}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'storagepool': '/storagepools/test-pool'}
            self.assertRaises(InvalidParameter, inst.template_update,
                              'test', params)

            args = {'name': pool,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, pool)

            inst.template_update('test', params)

            params = {'name': 'test-vm-1', 'template': '/templates/test'}
            self.assertRaises(InvalidParameter, inst.vms_create, params)

            inst.storagepool_activate(pool)
            rollback.prependDefer(inst.storagepool_deactivate, pool)

            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')
            vm_info = inst.vm_lookup(params['name'])
            disk_path = '/tmp/kimchi-images/%s-0.img' % vm_info['uuid']
            self.assertTrue(os.access(disk_path, os.F_OK))

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_create(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        # Test non-exist path raises InvalidParameter
        params = {'name': 'test',
                  'cdrom': '/non-exsitent.iso'}
        self.assertRaises(InvalidParameter, inst.templates_create, params)

        # Test non-iso path raises InvalidParameter
        params['cdrom'] = os.path.abspath(__file__)
        self.assertRaises(InvalidParameter, inst.templates_create, params)

        with RollbackContext() as rollback:
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)
            rollback.prependDefer(inst.network_delete, net_name)

            params = {'name': 'test', 'memory': 1024, 'cpus': 1}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            info = inst.template_lookup('test')
            for key in params.keys():
                self.assertEquals(params[key], info[key])
            self.assertEquals("default", info["networks"][0])

            # create template with non-existent network
            params['name'] = 'new-test'
            params['networks'] = ["no-exist"]
            self.assertRaises(InvalidParameter, inst.templates_create, params)

            params['networks'] = ['default', 'test-network']
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, params['name'])
            info = inst.template_lookup(params['name'])
            for key in params.keys():
                self.assertEquals(params[key], info[key])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_update(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)
            rollback.prependDefer(inst.network_delete, net_name)

            orig_params = {'name': 'test', 'memory': 1024, 'cpus': 1}
            inst.templates_create(orig_params)

            params = {'name': 'new-test'}
            self.assertEquals('new-test', inst.template_update('test', params))
            self.assertRaises(NotFoundError, inst.template_delete, 'test')

            params = {'name': 'new-test', 'memory': 512, 'cpus': 2}
            inst.template_update('new-test', params)
            rollback.prependDefer(inst.template_delete, 'new-test')

            info = inst.template_lookup('new-test')
            for key in params.keys():
                self.assertEquals(params[key], info[key])
            self.assertEquals("default", info["networks"][0])

            params = {'name': 'new-test', 'memory': 1024, 'cpus': 1,
                      'networks': ['default', 'test-network']}
            inst.template_update('new-test', params)
            info = inst.template_lookup('new-test')
            for key in params.keys():
                self.assertEquals(params[key], info[key])

            # test update with non-existent network
            params = {'networks': ["no-exist"]}
            self.assertRaises(InvalidParameter, inst.template_update,
                              'new-test', params)

    def test_vm_edit(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)

        orig_params = {'name': 'test', 'memory': '1024', 'cpus': '1'}
        inst.templates_create(orig_params)

        with RollbackContext() as rollback:
            params_1 = {'name': 'kimchi-vm1', 'template': '/templates/test'}
            params_2 = {'name': 'kimchi-vm2', 'template': '/templates/test'}
            inst.vms_create(params_1)
            inst.vms_create(params_2)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm1')
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm2')

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm1' in vms)

            inst.vm_start('kimchi-vm1')
            rollback.prependDefer(inst.vm_stop, 'kimchi-vm1')

            info = inst.vm_lookup('kimchi-vm1')
            self.assertEquals('running', info['state'])

            params = {'name': 'new-vm'}
            self.assertRaises(InvalidParameter, inst.vm_update,
                              'kimchi-vm1', params)

            inst.vm_stop('kimchi-vm1')
            params = {'name': 'new-vm'}
            self.assertRaises(OperationFailed, inst.vm_update,
                              'kimchi-vm1', {'name': 'kimchi-vm2'})
            inst.vm_update('kimchi-vm1', params)
            self.assertEquals(info['uuid'], inst.vm_lookup('new-vm')['uuid'])
            rollback.prependDefer(inst.vm_delete, 'new-vm')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_network(self):
        inst = model.Model('qemu:///system', self.tmp_store)

        with RollbackContext() as rollback:
            name = 'test-network'

            networks = inst.networks_get_list()
            num = len(networks) + 1
            args = {'name': name,
                    'connection': 'nat',
                    'subnet': '127.0.100.0/24'}
            inst.networks_create(args)
            rollback.prependDefer(inst.network_delete, name)

            networks = inst.networks_get_list()
            self.assertEquals(num, len(networks))

            networkinfo = inst.network_lookup(name)
            self.assertEquals(args['subnet'], networkinfo['subnet'])
            self.assertEqual(args['connection'], networkinfo['connection'])
            self.assertEquals('inactive', networkinfo['state'])
            self.assertEquals([], networkinfo['vms'])
            self.assertTrue(networkinfo['autostart'])

            inst.network_activate(name)
            rollback.prependDefer(inst.network_deactivate, name)

            networkinfo = inst.network_lookup(name)
            self.assertEquals('active', networkinfo['state'])

        networks = inst.networks_get_list()
        self.assertEquals((num - 1), len(networks))

    def test_multithreaded_connection(self):
        def worker():
            for i in xrange(100):
                ret = inst.vms_get_list()
                self.assertEquals('test', ret[0])

        inst = model.Model('test:///default', self.tmp_store)
        threads = []
        for i in xrange(100):
            t = threading.Thread(target=worker)
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def test_object_store(self):
        store = kimchi.objectstore.ObjectStore(self.tmp_store)

        with store as session:
            # Test create
            session.store('fǒǒ', 'těst1', {'α': 1})
            session.store('fǒǒ', 'těst2', {'β': 2})

            # Test list
            items = session.get_list('fǒǒ')
            self.assertTrue(u'těst1' in items)
            self.assertTrue(u'těst2' in items)

            # Test get
            item = session.get('fǒǒ', 'těst1')
            self.assertEquals(1, item[u'α'])

            # Test delete
            session.delete('fǒǒ', 'těst2')
            self.assertEquals(1, len(session.get_list('fǒǒ')))

            # Test get non-existent item

            self.assertRaises(NotFoundError, session.get,
                              'α', 'β')

            # Test delete non-existent item
            self.assertRaises(NotFoundError, session.delete,
                              'fǒǒ', 'těst2')

            # Test refresh existing item
            session.store('fǒǒ', 'těst1', {'α': 2})
            item = session.get('fǒǒ', 'těst1')
            self.assertEquals(2, item[u'α'])

    def test_object_store_threaded(self):
        def worker(ident):
            with store as session:
                session.store('foo', ident, {})

        store = kimchi.objectstore.ObjectStore(self.tmp_store)

        threads = []
        for i in xrange(50):
            t = threading.Thread(target=worker, args=(i,))
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        with store as session:
            self.assertEquals(50, len(session.get_list('foo')))
            self.assertEquals(10, len(store._connections.keys()))

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

        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        taskid = add_task('', quick_op, inst.objstore, 'Hello')
        self._wait_task(inst, taskid)
        self.assertEquals(1, taskid)
        self.assertEquals('finished', inst.task_lookup(taskid)['status'])
        self.assertEquals('Hello', inst.task_lookup(taskid)['message'])

        taskid = add_task('', long_op, inst.objstore,
                          {'delay': 3, 'result': False,
                           'message': 'It was not meant to be'})
        self.assertEquals(2, taskid)
        self.assertEquals('running', inst.task_lookup(taskid)['status'])
        self.assertEquals('OK', inst.task_lookup(taskid)['message'])
        self._wait_task(inst, taskid)
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])
        self.assertEquals('It was not meant to be',
                          inst.task_lookup(taskid)['message'])
        taskid = add_task('', abnormal_op, inst.objstore, {})
        self._wait_task(inst, taskid)
        self.assertEquals('Exception raised',
                          inst.task_lookup(taskid)['message'])
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_delete_running_vm(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': u'test', 'disks': []}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': u'kīмkhī-∨м', 'template': u'/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, u'kīмkhī-∨м')

            inst.vm_start(u'kīмkhī-∨м')
            rollback.prependDefer(inst.vm_stop, u'kīмkhī-∨м')

            inst.vm_delete(u'kīмkhī-∨м')

            vms = inst.vms_get_list()
            self.assertFalse(u'kīмkhī-∨м' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_list_sorted(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': []}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertEquals(vms, sorted(vms, key=unicode.lower))

    def test_use_test_host(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [],
                      'storagepool': '/storagepools/default-pool',
                      'domain': 'test',
                      'arch': 'i686'}

            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm',
                      'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertTrue('kimchi-vm' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_debug_reports(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        if not inst.capabilities_lookup()['system_report_tool']:
            raise unittest.SkipTest("Without debug report tool")

        try:
            timeout = int(os.environ['TEST_REPORT_TIMEOUT'])
        except (ValueError, KeyError):
            timeout = 120

        namePrefix = 'unitTestReport'
        # sosreport always deletes unsual letters like '-' and '_' in the
        # generated report file name.
        uuidstr = str(uuid.uuid4()).translate(None, "-_")
        reportName = namePrefix + uuidstr
        try:
            inst.debugreport_delete(namePrefix + '*')
        except NotFoundError:
            pass
        with RollbackContext() as rollback:
            report_list = inst.debugreports_get_list()
            self.assertFalse(reportName in report_list)
            try:
                task = inst.debugreports_create({'name': reportName})
                rollback.prependDefer(inst.debugreport_delete, reportName)
                taskid = task['id']
                self._wait_task(inst, taskid, timeout)
                self.assertEquals('finished',
                                  inst.task_lookup(taskid)['status'],
                                  "It is not necessary an error.  "
                                  "You may need to increase the "
                                  "timeout number by "
                                  "TEST_REPORT_TIMEOUT=200 "
                                  "./run_tests.sh test_model")
                report_list = inst.debugreports_get_list()
                self.assertTrue(reportName in report_list)
            except OperationFailed, e:
                if not 'debugreport tool not found' in e.message:
                    raise e

    def _wait_task(self, model, taskid, timeout=5):
            for i in range(0, timeout):
                if model.task_lookup(taskid)['status'] == 'running':
                    time.sleep(1)

    def test_get_distros(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        distros = inst.distros_get_list()
        for d in distros:
            distro = inst.distro_lookup(d)
            self.assertIn('name', distro)
            self.assertIn('os_distro', distro)
            self.assertIn('os_version', distro)
            self.assertIn('path', distro)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_get_hostinfo(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)
        info = inst.host_lookup()
        distro, version, codename = platform.linux_distribution()
        self.assertIn('cpu', info)
        self.assertEquals(distro, info['os_distro'])
        self.assertEquals(version, info['os_version'])
        self.assertEquals(unicode(codename, "utf-8"), info['os_codename'])
        self.assertEquals(psutil.TOTAL_PHYMEM, info['memory'])

    def test_get_hoststats(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        time.sleep(1.5)
        stats = inst.hoststats_lookup()
        cpu_utilization = stats['cpu_utilization']
        # cpu_utilization is set int 0, after first stats sample
        # the cpu_utilization is float in range [0.0, 100.0]
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

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_deep_scan(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            path = '/tmp/kimchi-images/tmpdir'
            if not os.path.exists(path):
                os.makedirs(path)
            iso_gen.construct_fake_iso('/tmp/kimchi-images/tmpdir/'
                                       'ubuntu12.04.iso', True,
                                       '12.04', 'ubuntu')
            iso_gen.construct_fake_iso('/tmp/kimchi-images/sles10.iso',
                                       True, '10', 'sles')

            args = {'name': 'kimchi-scanning-pool',
                    'path': '/tmp/kimchi-images',
                    'type': 'kimchi-iso'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_deactivate, args['name'])

            time.sleep(1)
            volumes = inst.storagevolumes_get_list(args['name'])
            self.assertEquals(len(volumes), 2)


class BaseModelTests(unittest.TestCase):
    class FoosModel(object):
        def __init__(self):
            self.data = {}

        def create(self, params):
            self.data.update(params)

        def get_list(self):
            return list(self.data)

    class TestModel(kimchi.basemodel.BaseModel):
        def __init__(self):
            foo = BaseModelTests.FoosModel()
            super(BaseModelTests.TestModel, self).__init__([foo])

    def test_root_model(self):
        t = BaseModelTests.TestModel()
        t.foos_create({'item1': 10})
        self.assertEquals(t.foos_get_list(), ['item1'])
