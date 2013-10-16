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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import unittest
import threading
import os
import time
import tempfile

import kimchi.model
import kimchi.objectstore
from kimchi.exception import *
import utils

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/kimchi-store-test'

    def tearDown(self):
        os.unlink(self.tmp_store)

    def test_vm_info(self):
        inst = kimchi.model.Model('test:///default', self.tmp_store)
        vms = inst.vms_get_list()
        self.assertEquals(1, len(vms))
        self.assertEquals('test', vms[0])

        keys = set(('state', 'stats', 'uuid', 'memory', 'screenshot', 'icon', 'graphics'))
        stats_keys = set(('cpu_utilization',
                          'net_throughput', 'net_throughput_peak',
                          'io_throughput', 'io_throughput_peak'))
        info = inst.vm_lookup('test')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('running', info['state'])
        self.assertEquals(2048, info['memory'])
        self.assertEquals(None, info['icon'])
        self.assertEquals(stats_keys, set(eval(info['stats']).keys()))

        self.assertRaises(NotFoundError, inst.vm_lookup, 'nosuchvm')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_lifecycle(self):
        inst = kimchi.model.Model(objstore_loc=self.tmp_store)

        with utils.RollbackContext() as rollback:
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
    def test_vm_storage_provisioning(self):
        inst = kimchi.model.Model(objstore_loc=self.tmp_store)

        with utils.RollbackContext() as rollback:
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
        inst = kimchi.model.Model('qemu:///system', self.tmp_store)

        with utils.RollbackContext() as rollback:
            path = '/tmp/kimchi-images'
            name = 'test-pool'
            if not os.path.exists(path):
                os.mkdir(path)

            pools = inst.storagepools_get_list()
            num = len(pools) + 1

            args = {'name': name,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, name)

            pools = inst.storagepools_get_list()
            self.assertEquals(num, len(pools))

            poolinfo = inst.storagepool_lookup(name)
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
            ori_params = {'autostart': True} if autostart else {'autostart': False}
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
        inst = kimchi.model.Model('qemu:///system', self.tmp_store)

        with utils.RollbackContext() as rollback:
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

            self.assertRaises(InvalidOperation, inst.storagevolumes_get_list, pool)
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

    def test_template_create(self):
        inst = kimchi.model.Model('test:///default', objstore_loc=self.tmp_store)
        # Test non-exist path raises InvalidParameter
        params = {'name': 'test',
                  'cdrom': '/non-exsitent.iso'}
        self.assertRaises(InvalidParameter, inst.templates_create, params)

        # Test non-iso path raises InvalidParameter
        params['cdrom'] = os.path.abspath(__file__)
        self.assertRaises(InvalidParameter, inst.templates_create, params)

    def test_template_update(self):
        inst = kimchi.model.Model('test:///default', objstore_loc=self.tmp_store)

        orig_params = {'name': 'test', 'memory': '1024', 'cpus': '1'}
        inst.templates_create(orig_params)

        params = {'name': '   '}
        self.assertRaises(InvalidParameter, inst.template_update, 'test', params)

        params = {'memory': ' invalid-value '}
        self.assertRaises(InvalidParameter, inst.template_update, 'test', params)

        params = {'memory': '   '}
        self.assertRaises(InvalidParameter, inst.template_update, 'test', params)

        params = {'cpus': ' invalid-value '}
        self.assertRaises(InvalidParameter, inst.template_update, 'test', params)

        params = {'cpus': '   '}
        self.assertRaises(InvalidParameter, inst.template_update, 'test', params)

        params = {'name': 'new-test'}
        self.assertEquals('new-test', inst.template_update('test', params))

        params = {'name': 'new-test', 'memory': '512', 'cpus': '2'}
        inst.template_update('new-test', params)
        info = inst.template_lookup('new-test')
        for key in params.keys():
            self.assertEquals(params[key], info[key])

        params = {'name': 'new-test', 'memory': 1024, 'cpus': 1}
        inst.template_update('new-test', params)
        info = inst.template_lookup('new-test')
        for key in params.keys():
            self.assertEquals(params[key], info[key])

    def test_multithreaded_connection(self):
        def worker():
            for i in xrange(100):
                ret = inst.vms_get_list()
                self.assertEquals('test', ret[0])

        inst = kimchi.model.Model('test:///default', self.tmp_store)
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

    def test_async_tasks(self):
        class task_except(Exception):
            pass
        def wait_task(model, taskid, timeout=5):
            for i in range(0, timeout):
                if model.task_lookup(taskid)['status'] == 'running':
                    time.sleep(1)

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

        inst = kimchi.model.Model('test:///default', objstore_loc=self.tmp_store)
        taskid = inst.add_task('', quick_op, 'Hello')
        wait_task(inst, taskid)
        self.assertEquals(1, taskid)
        self.assertEquals('finished', inst.task_lookup(taskid)['status'])
        self.assertEquals('Hello', inst.task_lookup(taskid)['message'])

        taskid = inst.add_task('', long_op,
                                     {'delay': 3, 'result': False,
                                      'message': 'It was not meant to be'})
        self.assertEquals(2, taskid)
        self.assertEquals('running', inst.task_lookup(taskid)['status'])
        self.assertEquals('OK', inst.task_lookup(taskid)['message'])
        wait_task(inst, taskid)
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])
        self.assertEquals('It was not meant to be', inst.task_lookup(taskid)['message'])
        taskid = inst.add_task('', abnormal_op, {})
        wait_task(inst, taskid)
        self.assertEquals('Exception raised', inst.task_lookup(taskid)['message'])
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_delete_running_vm(self):
        inst = kimchi.model.Model(objstore_loc=self.tmp_store)

        with utils.RollbackContext() as rollback:
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
        inst = kimchi.model.Model(objstore_loc=self.tmp_store)

        with utils.RollbackContext() as rollback:
            params = {'name': 'test', 'disks': []}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertEquals(vms, sorted(vms, key=unicode.lower))

    def test_use_test_host(self):
        inst = kimchi.model.Model('test:///default', objstore_loc=self.tmp_store)

        with utils.RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [],
                       'storagepool': '/storagepools/default-pool',
                       'domain': 'test',
                       'arch': 'i686'}

            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm', 'template': '/templates/test',}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertTrue('kimchi-vm' in vms)
