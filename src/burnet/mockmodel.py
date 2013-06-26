#
# Project Burnet
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

import random
import Image
import ImageDraw

import platform
import subprocess

import burnet.model
import burnet.vmtemplate
from burnet.screenshot import VMScreenshot
import burnet.vnc


class MockModel(object):
    def __init__(self):
        self.reset()
        self.vnc_port = 5999

        # open vnc port
        # make it here to make sure it will be available on server startup
        cmd = "qemu-system-%s"  % platform.machine()
        args = [cmd, "-vnc", ":99"]

        proc = subprocess.Popen(["ps", "-C", '"%s"' % " ".join(args), "-o", "pid", "h"], stdout=subprocess.PIPE)

        if len(proc.stdout.readlines()) == 0:
            p = subprocess.Popen(args, close_fds=True)

    def reset(self):
        self._mock_vms = {}
        self._mock_screenshots = {}
        self._mock_templates = {}
        self._mock_storagepools = {'default': MockStoragePool('default')}
        self._mock_vnc_ports = {}

    def vm_lookup(self, name):
        vm = self._get_vm(name)
        if vm.info['state'] == 'running':
            vm.info['screenshot'] = self.vmscreenshot_lookup(name)
        else:
            vm.info['screenshot'] = None
        vm.info['vnc_port'] = self._mock_vnc_ports.get(name, None)
        return vm.info

    def vm_delete(self, name):
        self._vmscreenshot_delete(name)
        vm = self._get_vm(name)
        for disk in vm.disk_paths:
            self.storagevolume_delete(disk['pool'], disk['volume'])

        del self._mock_vms[vm.name]

    def vm_start(self, name):
        self._get_vm(name).info['state'] = 'running'
        info = self._get_vm(name).info

    def vm_stop(self, name):
        self._get_vm(name).info['state'] = 'shutoff'

    def vm_connect(self, name):
        vnc_port = burnet.vnc.new_ws_proxy(self.vnc_port)
        self._mock_vnc_ports[name] = vnc_port

    def vms_create(self, params):
        try:
            t_name = burnet.model.template_name_from_uri(params['template'])
        except KeyError, item:
            raise burnet.model.MissingParameter(item)

        name = burnet.model.get_vm_name(params.get('name'), t_name,
                                        self._mock_vms.keys())
        if name in self._mock_vms:
            raise burnet.model.InvalidOperation("VM already exists")
        t = self._get_template(t_name)

        pool_uri = params.get('storagepool', t.info['storagepool'])
        pool_name = burnet.model.pool_name_from_uri(pool_uri)
        p = self._get_storagepool(pool_name)
        volumes = t.to_volume_list(name, p.info['path'])
        disk_paths = []
        for vol_info in volumes:
            self.storagevolumes_create(pool_name, vol_info)
            disk_paths.append({'pool': pool_name, 'volume': vol_info['name']})

        vm = MockVM(name, t.info)
        icon = t.info.get('icon')
        if icon:
            vm.info['icon'] = icon

        vm.disk_paths = disk_paths
        self._mock_vms[name] = vm
        return name

    def vms_get_list(self):
        return self._mock_vms.keys()

    def vmscreenshot_lookup(self, name):
        if self._get_vm(name).info['state'] != 'running':
            raise burnet.model.NotFoundError('No screenshot for stopped vm')
        screenshot = self._mock_screenshots.setdefault(
            name, MockVMScreenshot({'name': name}))
        return screenshot.lookup()

    def _vmscreenshot_delete(self, name):
        screenshot = self._mock_screenshots.get(name)
        if screenshot:
            screenshot.delete()
            del self._mock_screenshots[name]

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
        return name

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
        return name

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
        return name

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

    def storagevolumes_get_list(self, pool):
        return self._get_storagepool(pool)._volumes.keys()

    def _get_storagevolume(self, pool, name):
        try:
            return self._get_storagepool(pool)._volumes[name]
        except KeyError:
            raise burnet.model.NotFoundError()


class MockVM(object):
    def __init__(self, name, template_info):
        self.name = name
        self.disk_paths = []
        self.info = {'state': 'shutoff',
                     'cpu_stats': "35",
                     'memory': template_info['memory'],
                     'icon': None}


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


class MockVMScreenshot(VMScreenshot):
    OUTDATED_SECS = 5
    BACKGROUND_COLOR = ['blue', 'green', 'purple', 'red', 'yellow']
    BOX_COORD = (50, 115, 206, 141)
    BAR_COORD = (50, 115, 50, 141)

    def __init__(self, vm_name):
        VMScreenshot.__init__(self, vm_name)
        self.coord = MockVMScreenshot.BAR_COORD
        self.background = random.choice(MockVMScreenshot.BACKGROUND_COLOR)

    def _generate_scratch(self, thumbnail):
        self.coord = (self.coord[0],
                      self.coord[1],
                      min(MockVMScreenshot.BOX_COORD[2],
                          self.coord[2]+random.randrange(50)),
                      self.coord[3])

        image = Image.new("RGB", (256, 256), self.background)
        d = ImageDraw.Draw(image)
        d.rectangle(MockVMScreenshot.BOX_COORD, outline='black')
        d.rectangle(self.coord, outline='black', fill='black')
        image.save(thumbnail)


def get_mock_environment():
    model = MockModel()
    for i in xrange(5):
        name = 'test-template-%i' % i
        params = {'name': name}
        t = burnet.vmtemplate.VMTemplate(params)
        model._mock_templates[name] = t

    for name in ('test-template-1', 'test-template-3'):
        model._mock_templates[name].info.update({'folder': ['rhel', '6']})

    for i in xrange(10):
        name = 'test-vm-%i' % i
        vm = MockVM(name, model.template_lookup('test-template-0'))
        model._mock_vms[name] = vm

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
