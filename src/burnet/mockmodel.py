#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.

import burnet.model
import burnet.vmtemplate


class MockModel(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._mock_vms = {}
        self._mock_templates = {}
        self._mock_storagepools = {}

    def vm_lookup(self, name):
        vm = self._get_vm(name)
        return vm.info

    def vm_delete(self, name):
        vm = self._get_vm(name)
        del self._mock_vms[vm.name]

    def vm_start(self, name):
        self._get_vm(name).info['state'] = 'running'

    def vm_stop(self, name):
        self._get_vm(name).info['state'] = 'shutoff'

    def vms_create(self, params):
        try:
            name = params['name']
            mem = params['memory']
        except KeyError, item:
            raise burnet.model.MissingParameter(item)
        if name in self._mock_vms:
            raise burnet.model.InvalidOperation("VM already exists")
        vm = MockVM(name)
        vm.info['memory'] = mem
        self._mock_vms[name] = vm

    def vms_get_list(self):
        return self._mock_vms.keys()

    def template_lookup(self, name):
        t = self._get_template(name)
        return t.info

    def template_delete(self, name):
        try:
            del self._mock_templates[name]
        except KeyError:
            raise burnet.model.NotFoundError()

    def templates_create(self, params):
        name = params['name']
        if name in self._mock_templates:
            raise burnet.model.InvalidOperation("Template already exists")
        t = burnet.vmtemplate.VMTemplate(params)
        self._mock_templates[name] = t

    def templates_get_list(self):
        return self._mock_templates.keys()

    def _get_template(self, name):
        try:
            return self._mock_templates[name]
        except KeyError:
            raise burnet.model.NotFoundError()

    def _get_vm(self, name):
        try:
            return self._mock_vms[name]
        except KeyError:
            raise burnet.model.NotFoundError()

    def storagepools_create(self, params):
        try:
            name = params['name']
            pool = MockStoragePool(name)
            pool.info['capacity'] = params['capacity']
            pool.info['type'] = params['type']
            pool.info['path'] = params['path']
        except KeyError, item:
            raise burnet.model.MissingParameter(item)
        if name in self._mock_storagepools:
            raise burnet.model.InvalidOperation("StoragePool already exists")
        self._mock_storagepools[name] = pool

    def storagepool_lookup(self, name):
        storagepool = self._get_storagepool(name)
        return storagepool.info

    def storagepool_activate(self, name):
        self._get_storagepool(name).info['state'] = 'active'

    def storagepool_deactivate(self, name):
        self._get_storagepool(name).info['state'] = 'inactive'

    def storagepool_delete(self, name):
        # firstly, we should check the pool actually exists
        pool = self._get_storagepool(name)
        del self._mock_storagepools[pool.name]

    def storagepools_get_list(self):
        return self._mock_storagepools.keys()

    def _get_storagepool(self, name):
        try:
            return self._mock_storagepools[name]
        except KeyError:
            raise burnet.model.NotFoundError()

    def storagevolumes_create(self, pool, params):
        try:
            name = params['name']
            volume = MockStorageVolume(pool, name)
            volume.info['capacity'] = params['capacity']
            volume.info['type'] = params['type']
            volume.info['format'] = params['format']
        except KeyError, item:
            raise burnet.model.MissingParameter(item)
        if name in self._get_storagepool(pool)._volumes:
            raise burnet.model.InvalidOperation("StorageVolume already exists")
        self._get_storagepool(pool)._volumes[name] = volume

    def storagevolume_lookup(self, pool, name):
        storagevolume = self._get_storagevolume(pool, name)
        return storagevolume.info

    def storagevolume_wipe(self, pool, name):
        volume = self._get_storagevolume(pool, name)
        volume.info['allocation'] = 0

    def storagevolume_delete(self, pool, name):
        # firstly, we should check the pool actually exists
        volume = self._get_storagevolume(pool, name)
        del self._get_storagepool(pool)._volumes[volume.name]

    def storagevolume_resize(self, pool, name, size):
        volume = self._get_storagevolume(pool, name)
        volume.info['capacity'] = size
        pass

    def storagevolumes_get_list(self, pool):
        return self._get_storagepool(pool)._volumes.keys()

    def _get_storagevolume(self, pool, name):
        try:
            return self._get_storagepool(pool)._volumes[name]
        except KeyError:
            raise burnet.model.NotFoundError()


class MockVM(object):
    def __init__(self, name):
        self.name = name
        self.info = {'state': 'shutoff', 'memory': 1024,
                     'screenshot': '/images/image-missing.svg'}


class MockStoragePool(object):
    def __init__(self, name):
        self.name = name
        self.info = {'state': 'inactive',
                     'capacity': 1024,
                     'allocated': 512,
                     'path': '/var/lib/libvirt/images',
                     'type': 'dir'}
        self._volumes = {}


class MockStorageVolume(object):
    def __init__(self, pool, name):
        self.name = name
        self.pool = pool
        self.info = {'type': 'disk',
                     'capacity': 1024,
                     'allocation': 512,
                     'format': 'raw'}


def get_mock_environment():
    model = MockModel()
    for i in xrange(10):
        name = 'test-vm-%i' % i
        vm = MockVM(name)
        model._mock_vms[name] = vm

    for i in xrange(5):
        name = 'test-template-%i' % i
        params = {'name': name}
        t = burnet.vmtemplate.VMTemplate(params)
        model._mock_templates[name] = t

    #mock storagepool
    for i in xrange(5):
        name = 'default-pool-%i' % i
        defaultstoragepool = MockStoragePool(name)
        defaultstoragepool.info['path'] += '/%i' % i
        model._mock_storagepools[name] = defaultstoragepool
        for j in xrange(5):
            vol_name = 'volume-%i' % j
            defaultstoragevolume = MockStorageVolume(name, vol_name)
            mockpool = model._mock_storagepools[name]
            mockpool._volumes[vol_name] = defaultstoragevolume

    return model
