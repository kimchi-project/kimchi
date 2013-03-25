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

class MockModel(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._mock_vms = {}

    def vm_lookup(self, name):
        vm = self._get_vm(name)
        return vm.info

    def vm_delete(self, name):
        vm = self._get_vm(name)
        del self._mock_vms[vm.name]

    def vms_create(self, params):
        try:
            name = params['name']
            mem = params['memory']
        except KeyError, item:
            raise burnet.model.MissingParameter(item)
        if name in self._mock_vms:
            raise burnet.model.OperationFailed("VM already exists")
        vm = MockVM(name)
        vm.info['memory'] = mem
        self._mock_vms[name] = vm

    def vms_get_list(self):
        return self._mock_vms.keys()

    def _get_vm(self, name):
        try:
            return self._mock_vms[name]
        except KeyError:
            raise burnet.model.NotFoundError()


class MockVM(object):
    def __init__(self, name):
        self.name = name
        self.info = {'state': 'shutoff', 'memory': 1024}

def get_mock_environment():
    model = MockModel()
    for i in xrange(10):
        name = 'test-vm-%i' % i
        vm = MockVM(name)
        model._mock_vms[name] = vm
    return model
