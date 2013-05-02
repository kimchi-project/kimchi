#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.
#

import unittest
import threading
import os

import burnet.model
import utils

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/burnet-store-test'

    def tearDown(self):
        os.unlink(self.tmp_store)

    def test_vm_info(self):
        inst = burnet.model.Model('test:///default', self.tmp_store)
        vms = inst.vms_get_list()
        self.assertEquals(1, len(vms))
        self.assertEquals('test', vms[0])

        keys = set(('state', 'memory', 'screenshot', 'vnc_port'))
        info = inst.vm_lookup('test')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('running', info['state'])
        self.assertEquals(2048, info['memory'])

        self.assertRaises(burnet.model.NotFoundError,
                          inst.vm_lookup, 'nosuchvm')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_lifecycle(self):
        inst = burnet.model.Model(objstore_loc=self.tmp_store)

        with utils.RollbackContext() as rollback:
            params = {'name': 'test', 'disks': []}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'burnet-vm', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'burnet-vm')

            vms = inst.vms_get_list()
            self.assertTrue('burnet-vm' in vms)

            inst.vm_start('burnet-vm')
            rollback.prependDefer(inst.vm_stop, 'burnet-vm')

            info = inst.vm_lookup('burnet-vm')
            self.assertEquals('running', info['state'])

        vms = inst.vms_get_list()
        self.assertFalse('burnet-vm' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_storage_provisioning(self):
        inst = burnet.model.Model(objstore_loc=self.tmp_store)

        with utils.RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [{'size': 1}]}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'test-vm-1', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')

            disk_path = '/var/lib/libvirt/images/test-vm-1-0.img'
            self.assertTrue(os.access(disk_path, os.F_OK))
        self.assertFalse(os.access(disk_path, os.F_OK))

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_storagepool(self):
        inst = burnet.model.Model('qemu:///system', self.tmp_store)

        with utils.RollbackContext() as rollback:
            path = '/tmp/burnet-images'
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

            inst.storagepool_activate(name)
            rollback.prependDefer(inst.storagepool_deactivate, name)

            poolinfo = inst.storagepool_lookup(name)
            self.assertEquals('active', poolinfo['state'])

        pools = inst.storagepools_get_list()
        self.assertEquals((num - 1), len(pools))

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_storagevolume(self):
        inst = burnet.model.Model('qemu:///system', self.tmp_store)

        with utils.RollbackContext() as rollback:
            path = '/tmp/burnet-images'
            pool = 'test-pool'
            vol = 'test-volume.img'
            if not os.path.exists(path):
                os.mkdir(path)

            args = {'name': pool,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, pool)

            # Activate the pool before adding any volume
            inst.storagepool_activate(pool)
            rollback.prependDefer(inst.storagepool_deactivate, pool)

            vols = inst.storagevolumes_get_list(pool)
            num = len(vols) + 1
            params = {'name': vol,
                      'capacity': 1024,
                      'allocation': 512,
                      'format': 'raw'}
            inst.storagevolumes_create(pool, params)
            rollback.prependDefer(inst.storagevolume_delete, pool, vol)

            vols = inst.storagevolumes_get_list(pool)
            self.assertEquals(num, len(vols))

            inst.storagevolume_wipe(pool, vol)
            volinfo = inst.storagevolume_lookup(pool, vol)
            self.assertEquals(0, volinfo['allocation'])

            volinfo = inst.storagevolume_lookup(pool, vol)
            # Define the size = capacity + 16M
            size = volinfo['capacity'] + 16
            inst.storagevolume_resize(pool, vol, size)

            volinfo = inst.storagevolume_lookup(pool, vol)
            self.assertEquals(size, volinfo['capacity'])

    def test_multithreaded_connection(self):
        def worker():
            for i in xrange(100):
                ret = inst.vms_get_list()
                self.assertEquals('test', ret[0])

        inst = burnet.model.Model('test:///default', self.tmp_store)
        threads = []
        for i in xrange(100):
            t = threading.Thread(target=worker)
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def test_object_store(self):
        store = burnet.model.ObjectStore(self.tmp_store)

        with store as session:
            # Test create
            session.store('foo', 'test1', {'a': 1})
            session.store('foo', 'test2', {'b': 2})

            # Test list
            items = session.get_list('foo')
            self.assertTrue('test1' in items)
            self.assertTrue('test2' in items)

            # Test get
            item = session.get('foo', 'test1')
            self.assertEquals(1, item['a'])

            # Test delete
            session.delete('foo', 'test2')
            self.assertEquals(1, len(session.get_list('foo')))

            # Test get non-existent item
            self.assertRaises(burnet.model.NotFoundError, session.get,
                              'a', 'b')

            # Test delete non-existent item
            self.assertRaises(burnet.model.NotFoundError, session.delete,
                              'foo', 'test2')

            # Test refresh existing item
            session.store('foo', 'test1', {'a': 2})
            item = session.get('foo', 'test1')
            self.assertEquals(2, item['a'])

    def test_object_store_threaded(self):
        def worker(ident):
            with store as session:
                session.store('foo', ident, {})

        store = burnet.model.ObjectStore(self.tmp_store)

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
