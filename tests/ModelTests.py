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

import burnet.model
import utils

class ModelTests(unittest.TestCase):
    def test_vm_info(self):
        inst = burnet.model.Model(libvirt_uri='test:///default')
        vms = inst.vms_get_list()
        self.assertEquals(1, len(vms))
        self.assertEquals('test', vms[0])

        keys = set(('state', 'memory', 'screenshot'))
        info = inst.vm_lookup('test')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('running', info['state'])
        self.assertEquals(2048, info['memory'])

        self.assertRaises(burnet.model.NotFoundError,
                          inst.vm_lookup, 'nosuchvm')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_lifecycle(self):
        inst = burnet.model.Model()

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

        inst = burnet.model.Model(libvirt_uri='test:///default')
        threads = []
        for i in xrange(100):
            t = threading.Thread(target=worker)
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
