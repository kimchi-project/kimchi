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

import random
import copy

import subprocess
import os

try:
    from PIL import Image
    from PIL import ImageDraw
except ImportError:
    import Image
    import ImageDraw

import kimchi.model
import kimchi.vmtemplate
from kimchi.screenshot import VMScreenshot
import kimchi.vnc
import config
from kimchi.objectstore import ObjectStore
from kimchi.asynctask import AsyncTask
from kimchi.exception import *


class MockModel(object):
    def __init__(self, objstore_loc=None):
        self.reset()
        self.objstore = ObjectStore(objstore_loc)
        self.vnc_port = 5999

        # open vnc port
        # make it here to make sure it will be available on server startup
        cmd = config.find_qemu_binary()
        args = [cmd, "-vnc", ":99"]

        cmd  = "ps aux | grep '%s' | grep -v grep" % " ".join(args)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        if len(proc.stdout.readlines()) == 0:
            p = subprocess.Popen(args, close_fds=True)

    def get_capabilities(self):
        return {'stream_protocols': ['http', 'https', 'ftp', 'ftps', 'tftp'],
                'screenshot': True}

    def reset(self):
        self._mock_vms = {}
        self._mock_screenshots = {}
        self._mock_templates = {}
        self._mock_storagepools = {'default': MockStoragePool('default')}
        self._mock_graphics_ports = {}
        self.next_taskid = 1
        self.storagepool_activate('default')

    def vm_lookup(self, name):
        vm = self._get_vm(name)
        if vm.info['state'] == 'running':
            vm.info['screenshot'] = self.vmscreenshot_lookup(name)
        else:
            vm.info['screenshot'] = None
        vm.info['graphics']['port'] = self._mock_graphics_ports.get(name, None)
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
        vnc_port = kimchi.vnc.new_ws_proxy(self.vnc_port)
        self._mock_graphics_ports[name] = vnc_port

    def vms_create(self, params):
        try:
            t_name = kimchi.model.template_name_from_uri(params['template'])
        except KeyError, item:
            raise MissingParameter(item)

        name = kimchi.model.get_vm_name(params.get('name'), t_name,
                                        self._mock_vms.keys())
        if name in self._mock_vms:
            raise InvalidOperation("VM already exists")
        t = self._get_template(t_name)

        pool_uri = params.get('storagepool', t.info['storagepool'])
        pool_name = kimchi.model.pool_name_from_uri(pool_uri)
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
        names = self._mock_vms.keys()
        return sorted(names, key=unicode.lower)

    def vmscreenshot_lookup(self, name):
        if self._get_vm(name).info['state'] != 'running':
            raise NotFoundError('No screenshot for stopped vm')
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
            raise NotFoundError()

    def templates_create(self, params):
        name = params['name']
        if name in self._mock_templates:
            raise InvalidOperation("Template already exists")
        t = kimchi.vmtemplate.VMTemplate(params, scan=False)
        self._mock_templates[name] = t
        return name

    def template_update(self, name, params):
        old_t = self.template_lookup(name)
        new_t = copy.copy(old_t)
        new_t.update(params)
        ident = name

        self.template_delete(name)
        try:
            ident = self.templates_create(new_t)
        except:
            ident = self.templates_create(old_t)
            raise
        return ident

    def templates_get_list(self):
        return self._mock_templates.keys()

    def _get_template(self, name):
        try:
            return self._mock_templates[name]
        except KeyError:
            raise NotFoundError()

    def _get_vm(self, name):
        try:
            return self._mock_vms[name]
        except KeyError:
            raise NotFoundError()

    def storagepools_create(self, params):
        try:
            name = params['name']
            pool = MockStoragePool(name)
            pool.info['type'] = params['type']
            pool.info['path'] = params['path']
            if params['type'] == 'dir':
                pool.info['autostart'] = True
            else:
                pool.info['autostart'] = False
        except KeyError, item:
            raise MissingParameter(item)
        if name in self._mock_storagepools or name in (kimchi.model.ISO_POOL_NAME,):
            raise InvalidOperation("StoragePool already exists")
        self._mock_storagepools[name] = pool
        return name

    def storagepool_lookup(self, name):
        storagepool = self._get_storagepool(name)
        storagepool.refresh()
        return storagepool.info

    def storagepool_update(self, name, params):
        autostart = params['autostart']
        if autostart not in [True, False]:
            raise InvalidOperation("Autostart flag must be true or false")
        storagepool = self._get_storagepool(name)
        storagepool.info['autostart'] = autostart
        ident = storagepool.name
        return ident

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
            raise NotFoundError()

    def storagevolumes_create(self, pool_name, params):
        pool = self._get_storagepool(pool_name)
        if pool.info['state'] == 'inactive':
            raise InvalidOperation("StoragePool not active")
        try:
            name = params['name']
            volume = MockStorageVolume(pool, name, params['format'])
            volume.info['capacity'] = params['capacity']
            volume.info['type'] = params['type']
            volume.info['format'] = params['format']
            volume.info['path'] = os.path.join(
                pool.info['path'], name)
        except KeyError, item:
            raise MissingParameter(item)
        if name in pool._volumes:
            raise InvalidOperation("StorageVolume already exists")
        pool._volumes[name] = volume
        return name

    def storagevolume_lookup(self, pool, name):
        if self._get_storagepool(pool).info['state'] != 'active':
            raise InvalidOperation("StoragePool %s is not active" % pool)
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
        res = self._get_storagepool(pool)
        if res.info['state'] == 'inactive':
            raise InvalidOperation(
                "Unable to list volumes of inactive storagepool %s" % pool)
        return res._volumes.keys()

    def isopool_lookup(self, name):
        return {'state': 'active',
                'type': 'kimchi-iso'}

    def isovolumes_get_list(self):
        iso_volumes = []
        pools = self.storagepools_get_list()

        for pool in pools:
            try:
                volumes = self.storagevolumes_get_list(pool)
            except InvalidOperation:
                # Skip inactive pools
                continue
            for volume in volumes:
                res = self.storagevolume_lookup(pool, volume)
                if res['format'] == 'iso':
                    # prevent iso from different pool having same volume name
                    res['name'] = '%s-%s' % (pool, volume)
                    iso_volumes.append(res)
        return iso_volumes

    def tasks_get_list(self):
        with self.objstore as session:
            return session.get_list('task')

    def task_lookup(self, id):
        with self.objstore as session:
            return session.get('task', str(id))

    def add_task(self, target_uri, fn, opaque=None):
        id = self.next_taskid
        self.next_taskid = self.next_taskid + 1
        task = AsyncTask(id, target_uri, fn, self.objstore, opaque)

        return id

    def _get_storagevolume(self, pool, name):
        try:
            return self._get_storagepool(pool)._volumes[name]
        except KeyError:
            raise NotFoundError()


class MockVM(object):
    def __init__(self, name, template_info):
        self.name = name
        self.disk_paths = []
        self.info = {'state': 'shutoff',
                     'stats': "{'cpu_utilization': 20, 'net_throughput' : 35, \
                                'net_throughput_peak': 100, 'io_throughput': 45, \
                                'io_throughput_peak': 100}",
                     'memory': template_info['memory'],
                     'icon': None,
                     'graphics': {'type': 'vnc', 'port': None}}


class MockStoragePool(object):
    def __init__(self, name):
        self.name = name
        self.info = {'state': 'inactive',
                     'capacity': 1024,
                     'allocated': 512,
                     'available': 512,
                     'path': '/var/lib/libvirt/images',
                     'type': 'dir',
                     'nr_volumes': 0,
                     'autostart': 0}
        self._volumes = {}

    def refresh(self):
        state = self.info['state']
        self.info['nr_volumes'] = len(self._volumes) \
            if state == 'active' else 0


class MockTask(object):
    def __init__(self, id):
        self.id = id

class MockStorageVolume(object):
    def __init__(self, pool, name, fmt='raw'):
        self.name = name
        self.pool = pool
        self.info = {'type': 'disk',
                     'capacity': 1024,
                     'allocation': 512,
                     'format': fmt}
        if fmt == 'iso':
            self.info['allocation'] = self.info['capacity']
            self.info['os_version'] = '17'
            self.info['os_distro'] = 'fedora'
            self.info['bootable'] = True


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
        t = kimchi.vmtemplate.VMTemplate(params)
        model._mock_templates[name] = t

    for name in ('test-template-1', 'test-template-3'):
        model._mock_templates[name].info.update({'folder': ['rhel', '6']})

    for i in xrange(10):
        name = u'test-vm-%i' % i
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
            defaultstoragevolume.info['path'] = '%s/%s' % (
                defaultstoragepool.info['path'], vol_name)
            mockpool = model._mock_storagepools[name]
            mockpool._volumes[vol_name] = defaultstoragevolume
        vol_name = 'Fedora17.iso'
        defaultstoragevolume = MockStorageVolume(name, vol_name, 'iso')
        defaultstoragevolume.info['path'] = '%s/%s' % (
            defaultstoragepool.info['path'], vol_name)
        mockpool = model._mock_storagepools[name]
        mockpool._volumes[vol_name] = defaultstoragevolume

    return model
