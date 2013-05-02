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
