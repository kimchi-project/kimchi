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
import uuid

try:
    from PIL import Image
    from PIL import ImageDraw
except ImportError:
    import Image
    import ImageDraw

import time
import glob
import kimchi.model
from kimchi.vmtemplate import VMTemplate
from kimchi.screenshot import VMScreenshot
import kimchi.vnc
import config
from kimchi.objectstore import ObjectStore
from kimchi.asynctask import AsyncTask
from kimchi.exception import *
from kimchi.utils import is_digit
from kimchi.distroloader import DistroLoader


class MockModel(object):
    def __init__(self, objstore_loc=None):
        self.reset()
        self.objstore = ObjectStore(objstore_loc)
        self.vnc_port = 5999
        self.distros = self._get_distros()

        # open vnc port
        # make it here to make sure it will be available on server startup
        cmd = config.find_qemu_binary()
        args = [cmd, "-vnc", ":99"]

        cmd  = "ps aux | grep '%s' | grep -v grep" % " ".join(args)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        if len(proc.stdout.readlines()) == 0:
            p = subprocess.Popen(args, close_fds=True)

    def get_capabilities(self):
        return {'libvirt_stream_protocols': ['http', 'https', 'ftp', 'ftps', 'tftp'],
                'screenshot': True}

    def reset(self):
        self._mock_vms = {}
        self._mock_screenshots = {}
        self._mock_templates = {}
        self._mock_storagepools = {'default': MockStoragePool('default')}
        self._mock_graphics_ports = {}
        self._mock_interfaces = self.dummy_interfaces()
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
        vm = self._get_vm(name)
        self._vmscreenshot_delete(vm.uuid)
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
        t_name = kimchi.model.template_name_from_uri(params['template'])
        name = kimchi.model.get_vm_name(params.get('name'), t_name,
                                        self._mock_vms.keys())
        if name in self._mock_vms:
            raise InvalidOperation("VM already exists")

        vm_uuid = str(uuid.uuid4())
        vm_overrides = dict()
        pool_uri = params.get('storagepool')
        if pool_uri:
            vm_overrides['storagepool'] = pool_uri

        t = self._get_template(t_name, vm_overrides)
        t.validate()

        vm = MockVM(vm_uuid, name, t.info)
        icon = t.info.get('icon')
        if icon:
            vm.info['icon'] = icon

        vm.disk_paths = t.fork_vm_storage(vm_uuid)
        self._mock_vms[name] = vm
        return name

    def vms_get_list(self):
        names = self._mock_vms.keys()
        return sorted(names, key=unicode.lower)

    def vmscreenshot_lookup(self, name):
        vm = self._get_vm(name)
        if vm.info['state'] != 'running':
            raise NotFoundError('No screenshot for stopped vm')
        screenshot = self._mock_screenshots.setdefault(
            vm.uuid, MockVMScreenshot({'uuid': vm.uuid}))
        return screenshot.lookup()

    def _vmscreenshot_delete(self, vm_uuid):
        screenshot = self._mock_screenshots.get(vm_uuid)
        if screenshot:
            screenshot.delete()
            del self._mock_screenshots[vm_uuid]

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
        t = MockVMTemplate(params, self)
        self._mock_templates[name] = t
        return name

    def template_update(self, name, params):
        old_t = self.template_lookup(name)
        new_t = copy.copy(old_t)

        new_t.update(params)
        ident = name

        new_name = new_t.get(u'name', '')
        if len(new_name.strip()) == 0:
            raise InvalidParameter("You must specify a template name.")

        new_memory = new_t.get(u'memory', '')
        if not is_digit(new_memory):
            raise InvalidParameter("You must specify a number for memory.")

        new_ncpus = new_t.get(u'cpus', '')
        if not is_digit(new_ncpus):
            raise InvalidParameter("You must specify a number for cpus.")

        new_storagepool = new_t.get(u'storagepool', '')
        try:
            self._get_storagepool(kimchi.model.pool_name_from_uri(new_storagepool))
        except Exception as e:
            raise InvalidParameter("Storagepool specified is not valid: %s." % e.message)

        self.template_delete(name)
        try:
            ident = self.templates_create(new_t)
        except:
            ident = self.templates_create(old_t)
            raise
        return ident

    def templates_get_list(self):
        return self._mock_templates.keys()

    def _get_template(self, name, overrides=None):
        try:
            t = self._mock_templates[name]
            if overrides:
                args = copy.copy(t.info)
                args.update(overrides)
                return MockVMTemplate(args, self)
            else:
                return t
        except KeyError:
            raise NotFoundError()

    def debugreport_lookup(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name + '.txt')
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError('no such report')

        ctime = os.stat(file_target).st_ctime
        ctime = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(ctime))
        file_target = os.path.split(file_target)[-1]
        file_target = os.path.join("/data/debugreports", file_target)
        return {'file': file_target,
                'ctime': ctime}

    def debugreportcontent_lookup(self, name):
        return self.debugreport_lookup(name)

    def debugreport_delete(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name + '.txt')
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError('no such report')

        os.remove(file_target)

    def debugreports_create(self, params):
        ident = params['name']
        taskid = self._gen_debugreport_file(ident)
        return self.task_lookup(taskid)

    def debugreports_get_list(self):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, '*.txt')
        file_lists = glob.glob(file_pattern)
        file_lists = [os.path.split(file)[1] for file in file_lists]
        name_lists = [file.split('.', 1)[0] for file in file_lists]

        return name_lists

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
            volume = MockStorageVolume(pool, name, params)
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

    def dummy_interfaces(self):
        interfaces = {}
        ifaces = {"eth1": "nic", "bond0": "bonding",
                  "eth1.10": "vlan", "bridge0": "bridge"}
        for i, name in enumerate(ifaces.iterkeys()):
            iface = Interface(name)
            iface.info['type'] = ifaces[name]
            iface.info['ipaddr'] = '192.168.%s.101' % (i + 1)
            interfaces[name] = iface
        interfaces['eth1'].info['ipaddr'] = '192.168.0.101'
        return interfaces

    def interfaces_get_list(self):
        return self._mock_interfaces.keys()

    def interface_lookup(self, name):
        return self._mock_interfaces[name].info

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

    def _get_distros(self):
        distroloader = DistroLoader()
        return distroloader.get()

    def distros_get_list(self):
        return self.distros.keys()

    def distro_lookup(self, name):
        try:
            return self.distros[name]
        except KeyError:
            raise NotFoundError("distro '%s' not found" % name)

    def _gen_debugreport_file(self, ident):
        return self.add_task('', self._create_log, ident)

    def _create_log(self, cb, name):
        path = config.get_debugreports_path()
        tmpf = os.path.join(path, name + '.tmp')
        realf = os.path.join(path, name + '.txt')
        length = random.randint(1000, 10000)
        with open(tmpf, 'w') as fd:
            while length:
                fd.write('I am logged')
                length = length - 1
        os.rename(tmpf, realf)
        cb("OK", True)

    def hoststats_lookup(self, *name):
        return {'cpu_utilization': round(random.uniform(0, 100), 1)}


class MockVMTemplate(VMTemplate):
    def __init__(self, args, mockmodel_inst=None):
        VMTemplate.__init__(self, args)
        self.model = mockmodel_inst

    def _storage_validate(self):
        pool_uri = self.info['storagepool']
        pool_name = kimchi.model.pool_name_from_uri(pool_uri)
        try:
            pool = self.model._get_storagepool(pool_name)
        except NotFoundError:
            raise InvalidParameter('Storage specified by template does not exist')
        if pool.info['state'] != 'active':
            raise InvalidParameter('Storage specified by template is not active')

        return pool

    def _get_storage_path(self):
        pool = self._storage_validate()
        return pool.info['path']

    def fork_vm_storage(self, vm_name):
        pool = self._storage_validate()
        volumes = self.to_volume_list(vm_name)
        disk_paths = []
        for vol_info in volumes:
            vol_info['capacity'] = vol_info['capacity'] << 10
            self.model.storagevolumes_create(pool.name, vol_info)
            disk_paths.append({'pool': pool.name, 'volume': vol_info['name']})
        return disk_paths


class MockVM(object):
    def __init__(self, uuid, name, template_info):
        self.uuid = uuid
        self.name = name
        self.disk_paths = []
        self.info = {'state': 'shutoff',
                     'stats': "{'cpu_utilization': 20, 'net_throughput' : 35, \
                                'net_throughput_peak': 100, 'io_throughput': 45, \
                                'io_throughput_peak': 100}",
                     'uuid': self.uuid,
                     'memory': template_info['memory'],
                     'cpus': template_info['cpus'],
                     'icon': None,
                     'graphics': {'type': 'vnc', 'port': None}}


class MockStoragePool(object):
    def __init__(self, name):
        self.name = name
        self.info = {'state': 'inactive',
                     'capacity': 1024 << 20,
                     'allocated': 512 << 20,
                     'available': 512 << 20,
                     'path': '/var/lib/libvirt/images',
                     'type': 'dir',
                     'nr_volumes': 0,
                     'autostart': 0}
        self._volumes = {}

    def refresh(self):
        state = self.info['state']
        self.info['nr_volumes'] = len(self._volumes) \
            if state == 'active' else 0


class Interface(object):
    def __init__(self, name):
        self.name = name
        self.info = {'type': 'nic',
                     'ipaddr': '192.168.0.101',
                     'netmask': '255.255.255.0',
                     'status': 'active'}


class MockTask(object):
    def __init__(self, id):
        self.id = id

class MockStorageVolume(object):
    def __init__(self, pool, name, params={}):
        self.name = name
        self.pool = pool
        fmt = params.get('format', 'raw')
        capacity = params.get('capacity', 1024)
        self.info = {'type': 'disk',
                     'capacity': capacity << 20,
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
        t = MockVMTemplate(params, model)
        model._mock_templates[name] = t

    for name in ('test-template-1', 'test-template-3'):
        model._mock_templates[name].info.update({'folder': ['rhel', '6']})

    for i in xrange(10):
        name = u'test-vm-%i' % i
        vm_uuid = str(uuid.uuid4())
        vm = MockVM(vm_uuid, name, model.template_lookup('test-template-0'))
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
        defaultstoragevolume = MockStorageVolume(name, vol_name,
                                                 {'format': 'iso'})
        defaultstoragevolume.info['path'] = '%s/%s' % (
            defaultstoragepool.info['path'], vol_name)
        mockpool = model._mock_storagepools[name]
        mockpool._volumes[vol_name] = defaultstoragevolume

    return model
