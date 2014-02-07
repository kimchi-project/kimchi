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

import cherrypy
import copy
import disks
import glob
import ipaddr
import os
import psutil
import random
import time
import uuid


try:
    from PIL import Image
    from PIL import ImageDraw
except ImportError:
    import Image
    import ImageDraw



from kimchi import config
from kimchi.asynctask import AsyncTask
from kimchi.config import config as kconfig
from kimchi.distroloader import DistroLoader
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import MissingParameter, NotFoundError, OperationFailed
from kimchi.model.storagepools import ISO_POOL_NAME, STORAGE_SOURCES
from kimchi.model.utils import get_vm_name
from kimchi.model.vms import VM_STATIC_UPDATE_PARAMS
from kimchi.objectstore import ObjectStore
from kimchi.screenshot import VMScreenshot
from kimchi.utils import pool_name_from_uri, run_command, template_name_from_uri
from kimchi.vmtemplate import VMTemplate


class MockModel(object):
    def __init__(self, objstore_loc=None):
        self.reset()
        self.objstore = ObjectStore(objstore_loc)
        self.distros = self._get_distros()

    def capabilities_lookup(self, *ident):
        return {'libvirt_stream_protocols': ['http', 'https', 'ftp', 'ftps', 'tftp'],
                'qemu_stream': True,
                'screenshot': True,
                'system_report_tool': True}

    def reset(self):
        self._mock_vms = {}
        self._mock_screenshots = {}
        self._mock_templates = {}
        self._mock_storagepools = {'default': MockStoragePool('default')}
        self._mock_networks = {'default': MockNetwork('default')}
        self._mock_interfaces = self.dummy_interfaces()
        self.next_taskid = 1
        self.storagepool_activate('default')

    def _static_vm_update(self, dom, params):
        state = dom.info['state']

        if 'name' in params:
            if state == 'running' or params['name'] in self.vms_get_list():
                msg_args = {'name': dom.name, 'new_name': params['name']}
                raise InvalidParameter("KCHVM0003E", msg_args)
            else:
                del self._mock_vms[dom.name]
                dom.name = params['name']
                self._mock_vms[dom.name] = dom

        for key, val in params.items():
            if key in VM_STATIC_UPDATE_PARAMS and key in dom.info:
                dom.info[key] = val

    def _live_vm_update(self, dom, params):
        pass

    def vm_update(self, name, params):
        dom = self._get_vm(name)
        self._static_vm_update(dom, params)
        self._live_vm_update(dom, params)

        return dom.name

    def vm_lookup(self, name):
        vm = self._get_vm(name)
        if vm.info['state'] == 'running':
            vm.info['screenshot'] = self.vmscreenshot_lookup(name)
        else:
            vm.info['screenshot'] = None
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
        pass

    def vms_create(self, params):
        t_name = template_name_from_uri(params['template'])
        name = get_vm_name(params.get('name'), t_name,
                                      self._mock_vms.keys())
        if name in self._mock_vms:
            raise InvalidOperation("KCHVM0001E", {'name': name})

        vm_uuid = str(uuid.uuid4())
        vm_overrides = dict()
        pool_uri = params.get('storagepool')
        if pool_uri:
            vm_overrides['storagepool'] = pool_uri

        t = self._get_template(t_name, vm_overrides)
        t.validate()

        t_info = copy.deepcopy(t.info)
        graphics = params.get('graphics')
        if graphics:
                t_info.update({'graphics': graphics})

        vm = MockVM(vm_uuid, name, t_info)
        icon = t_info.get('icon')
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
            raise NotFoundError("KCHVM0004E", {'name': name})

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
            raise NotFoundError("KCHTMPL0002E", {'name': name})

    def templates_create(self, params):
        name = params['name']
        if name in self._mock_templates:
            raise InvalidOperation("KCHTMPL0001E", {'name': name})

        for net_name in params.get(u'networks', []):
            try:
                self._get_network(net_name)
            except NotFoundError:
                msg_args = {'network': net_name, 'template': name}
                raise InvalidParameter("KCHTMPL0003E", msg_args)

        t = MockVMTemplate(params, self)
        self._mock_templates[name] = t
        return name

    def template_update(self, name, params):
        old_t = self.template_lookup(name)
        new_t = copy.copy(old_t)

        new_t.update(params)
        ident = name

        new_storagepool = new_t.get(u'storagepool', '')
        try:
            self._get_storagepool(pool_name_from_uri(new_storagepool))
        except Exception:
            msg_args = {'pool': new_storagepool, 'template': name}
            raise InvalidParameter("KCHTMPL0004E", msg_args)

        for net_name in params.get(u'networks', []):
            try:
                self._get_network(net_name)
            except NotFoundError:
                msg_args = {'network': net_name, 'template': name}
                raise InvalidParameter("KCHTMPL0003E", msg_args)

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
            raise NotFoundError("KCHTMPL0002E", {'name': name})

    def debugreport_lookup(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name + '.txt')
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError("KCHDR0001E", {'name', name})

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
            raise NotFoundError("KCHDR0001E", {'name', name})

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
            raise NotFoundError("KCHVM0002E", {'name': name})

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
            raise MissingParameter("KCHPOOL0004E",
                                   {'item': item, 'name': name})

        if name in self._mock_storagepools or name in (ISO_POOL_NAME,):
            raise InvalidOperation("KCHPOOL0001E", {'name': name})

        self._mock_storagepools[name] = pool
        return name

    def storagepool_lookup(self, name):
        storagepool = self._get_storagepool(name)
        storagepool.refresh()
        return storagepool.info

    def storagepool_update(self, name, params):
        pool = self._get_storagepool(name)
        if 'autostart' in params:
            pool.info['autostart'] = params['autostart']
        if 'disks' in params:
            # check if pool is type 'logical'
            if pool.info['type'] != 'logical':
                raise InvalidOperation('KCHPOOL0029E')
            self._update_lvm_disks(name, params['disks'])
        ident = pool.name
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
        return sorted(self._mock_storagepools.keys())

    def _get_storagepool(self, name):
        try:
            return self._mock_storagepools[name]
        except KeyError:
            raise NotFoundError("KCHPOOL0002E", {'name': name})

    def storagevolumes_create(self, pool_name, params):
        pool = self._get_storagepool(pool_name)
        if pool.info['state'] == 'inactive':
            raise InvalidOperation("KCHVOL0003E",
                                   {'pool': pool_name,
                                    'volume': params['name']})

        try:
            name = params['name']
            volume = MockStorageVolume(pool, name, params)
            volume.info['type'] = params['type']
            volume.info['format'] = params['format']
            volume.info['path'] = os.path.join(
                pool.info['path'], name)
        except KeyError, item:
            raise MissingParameter("KCHVOL0004E",
                                   {'item': item, 'volume': name})

        if name in pool._volumes:
            raise InvalidOperation("KCHVOL0001E", {'name': name})

        pool._volumes[name] = volume
        return name

    def storagevolume_lookup(self, pool, name):
        if self._get_storagepool(pool).info['state'] != 'active':
            raise InvalidOperation("KCHVOL0005E", {'pool': pool,
                                                         'volume': name})

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
            raise InvalidOperation("KCHVOL0006E", {'pool': pool})
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

    def storageservers_get_list(self, _target_type=None):
        # FIXME: When added new storage server support, this needs to be updated
        target_type = STORAGE_SOURCES.keys() \
            if not _target_type else [_target_type]
        pools = self.storagepools_get_list()
        server_list = []
        for pool in pools:
            try:
                pool_info = self.storagepool_lookup(pool)
                if (pool_info['type'] in target_type and
                        pool_info['source']['addr'] not in server_list):
                    server_list.append(pool_info['source']['addr'])
            except NotFoundError:
                pass

        return server_list

    def storageserver_lookup(self, server):
        pools = self.storagepools_get_list()
        for pool in pools:
            try:
                pool_info = self.storagepool_lookup(pool)
                if pool_info['source'] and pool_info['source']['addr'] == server:
                    return dict(host=server)
            except NotFoundError:
            # Avoid inconsistent pool result because of lease between list and lookup
                pass

        raise NotFoundError("KCHSR0001E", {'server': server})

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

    def networks_create(self, params):
        name = params['name']
        if name in self.networks_get_list():
            raise InvalidOperation("KCHNET0001E", {'name': name})

        network = MockNetwork(name)
        connection = params['connection']
        network.info['connection'] = connection
        if connection == "bridge":
            try:
                interface = params['interface']
                network.info['interface'] = interface
            except KeyError:
                raise MissingParameter("KCHNET0004E",
                                       {'name': name})

        subnet = params.get('subnet', '')
        if subnet:
            network.info['subnet'] = subnet
            try:
                net = ipaddr.IPNetwork(subnet)
            except ValueError:
                msg_args = {'subnet':subnet, 'network': name}
                raise InvalidParameter("KCHNET0003E", msg_args)

            network.info['dhcp'] = {
                'start': str(net.network + net.numhosts / 2),
                'stop': str(net.network + net.numhosts - 2)}

        self._mock_networks[name] = network
        return name

    def _get_network(self, name):
        try:
            return self._mock_networks[name]
        except KeyError:
            raise NotFoundError("KCHNET0002E", {'name': name})

    def _get_vms_attach_to_a_network(self, network):
        vms = []
        for name, dom in self._mock_vms.iteritems():
             if network in dom.networks:
                 vms.append(name)
        return vms

    def network_lookup(self, name):
        network = self._get_network(name)
        network.info['vms'] = self._get_vms_attach_to_a_network(name)
        return network.info

    def network_activate(self, name):
        self._get_network(name).info['state'] = 'active'

    def network_deactivate(self, name):
        self._get_network(name).info['state'] = 'inactive'

    def network_delete(self, name):
        # firstly, we should check the network actually exists
        network = self._get_network(name)
        del self._mock_networks[network.name]

    def networks_get_list(self):
        return sorted(self._mock_networks.keys())

    def vmifaces_create(self, vm, params):
        if (params["type"] == "network" and
            params["network"] not in self.networks_get_list()):
            msg_args = {'network': params["network"], 'name': vm}
            raise InvalidParameter("KCHVMIF0002E", msg_args)

        dom = self._get_vm(vm)
        iface = MockVMIface(params["network"])
        ("model" in params.keys() and
         iface.info.update({"model": params["model"]}))

        mac = iface.info['mac']
        dom.ifaces[mac] = iface
        return mac

    def vmifaces_get_list(self, vm):
        dom = self._get_vm(vm)
        macs = dom.ifaces.keys()
        return macs

    def vmiface_lookup(self, vm, mac):
        dom = self._get_vm(vm)
        try:
            info = dom.ifaces[mac].info
        except KeyError:
            raise NotFoundError("KCHVMIF0001E", {'iface': mac, 'name': vm})
        return info

    def vmiface_delete(self, vm, mac):
        dom = self._get_vm(vm)
        try:
           del dom.ifaces[mac]
        except KeyError:
            raise NotFoundError("KCHVMIF0001E", {'iface': mac, 'name': vm})

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
            raise NotFoundError("KCHVOL0002E", {'name': name, 'pool': pool})

    def _get_distros(self):
        distroloader = DistroLoader()
        return distroloader.get()

    def distros_get_list(self):
        return self.distros.keys()

    def distro_lookup(self, name):
        try:
            return self.distros[name]
        except KeyError:
            raise NotFoundError("KCHDISTRO0001E", {'name': name})

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

    def host_lookup(self, *name):
        res = {}
        res['memory'] = 6114058240
        res['cpu'] = 'Intel(R) Core(TM) i5 CPU       M 560  @ 2.67GHz'
        res['os_distro'] = 'Red Hat Enterprise Linux Server'
        res['os_version'] = '6.4'
        res['os_codename'] = 'Santiago'

        return res

    def hoststats_lookup(self, *name):
        virt_mem = psutil.virtual_memory()
        memory_stats = {'total': virt_mem.total,
                        'free': virt_mem.free,
                        'cached': virt_mem.cached,
                        'buffers': virt_mem.buffers,
                        'avail': virt_mem.available}
        return {'cpu_utilization': round(random.uniform(0, 100), 1),
                'memory': memory_stats,
                'disk_read_rate': round(random.uniform(0, 4000), 1),
                'disk_write_rate': round(random.uniform(0, 4000), 1),
                'net_recv_rate': round(random.uniform(0, 4000), 1),
                'net_sent_rate': round(random.uniform(0, 4000), 1)}

    def vms_get_list_by_state(self, state):
        ret_list = []
        for name in self.vms_get_list():
            if (self._mock_vms[name].info['state']) == state:
                ret_list.append(name)
        return ret_list

    def host_shutdown(self, args=None):
        # Check for running vms before shutdown
        running_vms = self.vms_get_list_by_state('running')
        if len(running_vms) > 0:
            raise OperationFailed("KCHHOST0001E")
        cherrypy.engine.exit()

    def host_reboot(self, args=None):
        # Find running VMs
        running_vms = self.vms_get_list_by_state('running')
        if len(running_vms) > 0:
            raise OperationFailed("KCHHOST0002E")
        cherrypy.engine.stop()
        time.sleep(10)
        cherrypy.engine.start()

    def partitions_get_list(self):
        result = disks.get_partitions_names()
        return result

    def partition_lookup(self, name):
        if name not in disks.get_partitions_names():
            raise NotFoundError("KCHPART0001E", {'name': name})

        return disks.get_partition_details(name)

    def config_lookup(self, name):
        return {'http_port': cherrypy.server.socket_port,
                'display_proxy_port':
                kconfig.get('display', 'display_proxy_port')}


class MockVMTemplate(VMTemplate):
    def __init__(self, args, mockmodel_inst=None):
        VMTemplate.__init__(self, args)
        self.model = mockmodel_inst

    def _storage_validate(self):
        pool_uri = self.info['storagepool']
        pool_name = pool_name_from_uri(pool_uri)
        try:
            pool = self.model._get_storagepool(pool_name)
        except NotFoundError:
            msg_args = {'pool': pool_name, 'template': self.name}
            raise InvalidParameter("KCHTMPL0004E", msg_args)

        if pool.info['state'] != 'active':
            msg_args = {'pool': pool_name, 'template': self.name}
            raise InvalidParameter("KCHTMPL0005E", msg_args)

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


class MockVMIface(object):
    counter = 0

    def __init__(self, network=None):
        self.__class__.counter += 1
        self.info = {'type': 'network',
                     'model': 'virtio',
                     'network': network if network else "net-%s" % self.counter,
                     'mac': self.get_mac()
                     }

    @classmethod
    def get_mac(cls):
        mac = ":".join(["52", "54"] + ["%02x" % (cls.counter/(256**i) % 256)
                       for i in range(3, -1, -1)])
        return mac


class MockVM(object):
    def __init__(self, uuid, name, template_info):
        self.uuid = uuid
        self.name = name
        self.disk_paths = []
        self.networks = template_info['networks']
        ifaces = [MockVMIface(net) for net in self.networks]
        self.ifaces = dict([(iface.info['mac'], iface) for iface in ifaces])
        self.info = {'state': 'shutoff',
                     'stats': "{'cpu_utilization': 20, 'net_throughput' : 35, \
                                'net_throughput_peak': 100, 'io_throughput': 45, \
                                'io_throughput_peak': 100}",
                     'uuid': self.uuid,
                     'memory': template_info['memory'],
                     'cpus': template_info['cpus'],
                     'icon': None,
                     'graphics': {'type': 'vnc', 'listen': '0.0.0.0', 'port': None}
                     }
        self.info['graphics'].update(template_info['graphics'])


class MockStoragePool(object):
    def __init__(self, name):
        self.name = name
        self.info = {'state': 'inactive',
                     'capacity': 1024 << 20,
                     'allocated': 512 << 20,
                     'available': 512 << 20,
                     'path': '/var/lib/libvirt/images',
                     'source': {},
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


class MockNetwork(object):
    def __init__(self, name):
        self.name = name
        self.info = {'state': 'inactive',
                     'autostart': True,
                     'connection': 'nat',
                     'interface': 'virbr0',
                     'subnet': '192.168.122.0/24',
                     'dhcp': {'start': '192.168.122.128',
                              'stop':  '192.168.122.254'},
                     }


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

    #mock network
    for i in xrange(5):
        name = 'test-network-%i' % i
        testnetwork = MockNetwork(name)
        testnetwork.info['interface'] = 'virbr%i' % (i + 1)
        testnetwork.info['subnet'] = '192.168.%s.0/24' % (i + 1)
        testnetwork.info['dhcp']['start'] = '192.168.%s.128' % (i + 1)
        testnetwork.info['dhcp']['end'] = '192.168.%s.254' % (i + 1)
        model._mock_networks[name] = testnetwork

    return model
