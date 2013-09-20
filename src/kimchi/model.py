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

import re
import threading
import time
import libvirt
import functools
import os
import json
import copy
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from xml.etree import ElementTree
from cherrypy.process.plugins import BackgroundTask

import vmtemplate
import config
import xmlutils
import vnc
import isoinfo
from screenshot import VMScreenshot
from kimchi.featuretests import FeatureTests
from kimchi.objectstore import ObjectStore
from kimchi.asynctask import AsyncTask
from kimchi.exception import *


ISO_POOL_NAME = u'kimchi_isos'
STATS_INTERVAL = 5

def _uri_to_name(collection, uri):
    expr = '/%s/(.*?)/?$' % collection
    m = re.match(expr, uri)
    if not m:
        raise InvalidParameter(uri)
    return m.group(1)

def template_name_from_uri(uri):
    return _uri_to_name('templates', uri)

def pool_name_from_uri(uri):
    return _uri_to_name('storagepools', uri)

def get_vm_name(vm_name, t_name, name_list):
    if vm_name:
        return vm_name
    for i in xrange(1, 1000):
        vm_name = "%s-vm-%i" % (t_name, i)
        if vm_name not in name_list:
            return vm_name
    raise OperationFailed("Unable to choose a VM name")

class Model(object):
    dom_state_map = {0: 'nostate',
                     1: 'running',
                     2: 'blocked',
                     3: 'paused',
                     4: 'shutdown',
                     5: 'shutoff',
                     6: 'crashed'}

    pool_state_map = {0: 'inactive',
                      1: 'initializing',
                      2: 'active',
                      3: 'degraded',
                      4: 'inaccessible'}

    volume_type_map = {0: 'file',
                       1: 'block',
                       2: 'directory',
                       3: 'network'}

    def __init__(self, libvirt_uri=None, objstore_loc=None):
        self.libvirt_uri = libvirt_uri or 'qemu:///system'
        self.conn = LibvirtConnection(self.libvirt_uri)
        self.objstore = ObjectStore(objstore_loc)
        self.graphics_ports = {}
        self.next_taskid = 1
        self.stats = {}
        self.statsThread = BackgroundTask(STATS_INTERVAL, self._update_stats)
        self.statsThread.start()
        if 'qemu:///' in self.libvirt_uri:
            self._default_pool_check()

    def _default_pool_check(self):
        default_pool = {'name': 'default',
                        'path': '/var/lib/libvirt/images',
                        'type': 'dir'}
        try:
            self.storagepools_create(default_pool)
        except InvalidOperation:
            # ignore error when pool existed
            pass
        except OperationFailed as e:
            # path used by other pool or other reasons of failure, exit
            cherrypy.log.error(
                "Fatal: Cannot create default because of %s, exit kimchid",
                e.message,
                serverity=logging.ERROR)
            sys.exit(1)

        if self.storagepool_lookup('default')['state'] == 'inactive':
            try:
                self.storagepool_activate('default')
            except OperationFailed:
                cherrypy.log.error(
                    "Fatal: Default pool cannot be activated, exit kimchid",
                    severity=logging.ERROR)
                sys.exit(1)

    def get_capabilities(self):
        protocols = []
        for p in ['http', 'https', 'ftp', 'ftps', 'tftp']:
            if FeatureTests.is_iso_stream_supported(p):
                protocols.append(p)

        return {'stream_protocols': protocols,
                'screenshot': VMScreenshot.get_stream_test_result()}

    def _update_stats(self):
        vm_list = self.vms_get_list()

        for name in vm_list:
            dom = self._get_vm(name)
            info = dom.info()
            state = Model.dom_state_map[info[0]]

            if state != 'running':
                self.stats[name] = {}
                continue

            if self.stats.get(name, None) is None:
                self.stats[name] = {}

            timestamp = time.time()
            prevStats = self.stats.get(name, {})
            seconds = timestamp - prevStats.get('timestamp', 0)
            self.stats[name].update({'timestamp': timestamp})

            self._get_percentage_cpu_usage(name, info, seconds)
            self._get_network_io_rate(name, dom, seconds)
            self._get_disk_io_rate(name, dom, seconds)

    def _get_percentage_cpu_usage(self, name, info, seconds):
        prevCpuTime = self.stats[name].get('cputime', 0)

        cpus = info[3]
        cpuTime = info[4] - prevCpuTime

        base = (((cpuTime) * 100.0) / (seconds * 1000.0 * 1000.0 * 1000.0))
        percentage = max(0.0, min(100.0, base / cpus))

        self.stats[name].update({'cputime': info[4], 'cpu': percentage})

    def _get_network_io_rate(self, name, dom, seconds):
        prevNetRxKB = self.stats[name].get('netRxKB', 0)
        prevNetTxKB = self.stats[name].get('netTxKB', 0)
        currentMaxNetRate = self.stats[name].get('max_net_io', 100)

        rx_bytes = 0
        tx_bytes = 0

        tree = ElementTree.fromstring(dom.XMLDesc(0))
        for target in tree.findall('devices/interface/target'):
            dev = target.get('dev')
            io = dom.interfaceStats(dev)
            rx_bytes += io[0]
            tx_bytes += io[4]

        netRxKB = float(rx_bytes / 1000)
        netTxKB = float(tx_bytes / 1000)

        rx_stats = float((netRxKB - prevNetRxKB) / seconds)
        tx_stats = float((netTxKB - prevNetTxKB) / seconds)

        rate = float(rx_stats + tx_stats)
        max_net_io = max(currentMaxNetRate, int(rate))

        self.stats[name].update({'net_io': rate, 'max_net_io': max_net_io,
                                 'netRxKB': netRxKB, 'netTxKB': netTxKB})

    def _get_disk_io_rate(self, name, dom, seconds):
        prevDiskRdKB = self.stats[name].get('diskRdKB', 0)
        prevDiskWrKB = self.stats[name].get('diskWrKB', 0)
        currentMaxDiskRate = self.stats[name].get('max_disk_io', 100)

        rd_bytes = 0
        wr_bytes = 0

        tree = ElementTree.fromstring(dom.XMLDesc(0))
        for target in tree.findall("devices/disk/target"):
            dev = target.get("dev")
            io = dom.blockStats(dev)
            rd_bytes += io[1]
            wr_bytes += io[3]

        diskRdKB = float(rd_bytes / 1024)
        diskWrKB = float(wr_bytes / 1024)

        rd_stats = float((diskRdKB - prevDiskRdKB) / seconds)
        wr_stats = float((diskWrKB - prevDiskWrKB) / seconds)

        rate = float(rd_stats + wr_stats)
        max_disk_io = max(currentMaxDiskRate, int(rate))

        self.stats[name].update({'disk_io': rate, 'max_disk_io': max_disk_io,
                                 'diskRdKB': diskRdKB, 'diskWrKB': diskWrKB})

    def vm_lookup(self, name):
        dom = self._get_vm(name)
        info = dom.info()
        state = Model.dom_state_map[info[0]]
        screenshot = None
        graphics_type, _ = self._vm_get_graphics(name)
        # 'port' must remain None until a connect call is issued
        graphics_port = (self.graphics_ports.get(name, None) if state == 'running'
                      else None)
        try:
            if state == 'running':
                screenshot = self.vmscreenshot_lookup(name)
        except NotFoundError:
            pass

        with self.objstore as session:
            try:
                extra_info = session.get('vm', name)
            except NotFoundError:
                extra_info = {}
        icon = extra_info.get('icon')

        vm_stats = self.stats.get(name, {})
        stats = {}
        stats['cpu_utilization'] = vm_stats.get('cpu', 0)
        stats['net_throughput'] = vm_stats.get('net_io', 0)
        stats['net_throughput_peak'] = vm_stats.get('max_net_io', 100)
        stats['io_throughput'] = vm_stats.get('disk_io', 0)
        stats['io_throughput_peak'] = vm_stats.get('max_disk_io', 100)

        return {'state': state,
                'stats': str(stats),
                'memory': info[2] >> 10,
                'screenshot': screenshot,
                'icon': icon,
                'graphics': {"type": graphics_type, "port": graphics_port}}

    def _vm_get_disk_paths(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='disk']/source/@file"
        return xmlutils.xpath_get_text(xml, xpath)

    def vm_delete(self, name):
        if self._vm_exists(name):
            self._vmscreenshot_delete(name)
            conn = self.conn.get()
            dom = self._get_vm(name)
            paths = self._vm_get_disk_paths(dom)
            info = self.vm_lookup(name)

            if info['state'] == 'running':
                self.vm_stop(name)

            dom.undefine()

            for path in paths:
                vol = conn.storageVolLookupByPath(path)
                vol.delete(0)

            with self.objstore as session:
                session.delete('vm', name, ignore_missing=True)

    def vm_start(self, name):
        dom = self._get_vm(name)
        dom.create()

    def vm_stop(self, name):
        if self._vm_exists(name):
            dom = self._get_vm(name)
            dom.destroy()

    def _vm_get_graphics(self, name):
        dom = self._get_vm(name)
        xml = dom.XMLDesc(0)
        expr = "/domain/devices/graphics/@type"
        res = xmlutils.xpath_get_text(xml, expr)
        graphics_type = res[0] if res else None
        port = None
        if graphics_type:
            expr = "/domain/devices/graphics[@type='%s']/@port" % graphics_type
            res = xmlutils.xpath_get_text(xml, expr)
            port = int(res[0]) if res else None
        # FIX ME
        # graphics_type should be 'vnc' or None.  'spice' should only be
        # returned if we support it in the future.
        graphics_type = None if graphics_type != "vnc" else graphics_type
        return graphics_type, port

    def vm_connect(self, name):
        graphics, port = self._vm_get_graphics(name)
        if graphics == "vnc" and port != None:
            port = vnc.new_ws_proxy(port)
            self.graphics_ports[name] = port
        else:
            raise OperationFailed("Unable to find VNC port in %s" % name)

    def vms_create(self, params):
        try:
            t_name = template_name_from_uri(params['template'])
        except KeyError, item:
            raise MissingParameter(item)

        vm_list = self.vms_get_list()
        name = get_vm_name(params.get('name'), t_name, vm_list)
        # incoming text, from js json, is unicode, do not need decode
        if name in vm_list:
            raise InvalidOperation("VM already exists")
        t = self._get_template(t_name)

        conn = self.conn.get()
        pool_uri = params.get('storagepool', t.info['storagepool'])
        pool_name = pool_name_from_uri(pool_uri)
        pool = conn.storagePoolLookupByName(pool_name)
        xml = pool.XMLDesc(0)
        storage_path = xmlutils.xpath_get_text(xml, "/pool/target/path")[0]

        # Provision storage:
        # TODO: Rebase on the storage API once upstream
        vol_list = t.to_volume_list(name, storage_path)
        for v in vol_list:
            # outgoing text to libvirt, encode('utf-8')
            pool.createXML(v['xml'].encode('utf-8'), 0)

        # Store the icon for displaying later
        icon = t.info.get('icon')
        if icon:
            with self.objstore as session:
                session.store('vm', name, {'icon': icon})

        xml = t.to_vm_xml(name, storage_path)
        # outgoing text to libvirt, encode('utf-8')
        dom = conn.defineXML(xml.encode('utf-8'))
        return name

    def vms_get_list(self):
        conn = self.conn.get()
        ids = conn.listDomainsID()
        names = map(lambda x: conn.lookupByID(x).name(), ids)
        names += conn.listDefinedDomains()
        names = map(lambda x: x.decode('utf-8'), names)
        return sorted(names, key=unicode.lower)

    def vmscreenshot_lookup(self, name):
        dom = self._get_vm(name)
        d_info = dom.info()
        if Model.dom_state_map[d_info[0]] != 'running':
            raise NotFoundError('No screenshot for stopped vm')

        screenshot = self._get_screenshot(name)
        img_path = screenshot.lookup()
        # screenshot info changed after scratch generation
        with self.objstore as session:
            session.store('screenshot', name, screenshot.info)
        return img_path

    def _vmscreenshot_delete(self, name):
        screenshot = self._get_screenshot(name)
        screenshot.delete()
        with self.objstore as session:
            session.delete('screenshot', name)

    def template_lookup(self, name):
        t = self._get_template(name)
        return t.info

    def template_delete(self, name):
        with self.objstore as session:
            session.delete('template', name)

    def templates_create(self, params):
        name = params['name']
        with self.objstore as session:
            if name in session.get_list('template'):
                raise InvalidOperation("Template already exists")
            t = vmtemplate.VMTemplate(params, scan=True)
            session.store('template', name, t.info)
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
        with self.objstore as session:
            return session.get_list('template')

    def add_task(self, target_uri, fn, opaque=None):
        id = self.next_taskid
        self.next_taskid = self.next_taskid + 1

        task = AsyncTask(id, target_uri, fn, self.objstore, opaque)

        return id

    def tasks_get_list(self):
        with self.objstore as session:
            return session.get_list('task')

    def task_lookup(self, id):
        with self.objstore as session:
            return session.get('task', str(id))

    def _vm_exists(self, name):
        try:
            self._get_vm(name)
            return True
        except NotFoundError:
            return False
        except:
            raise


    def _get_vm(self, name):
        conn = self.conn.get()
        try:
            # outgoing text to libvirt, encode('utf-8')
            return conn.lookupByName(name.encode("utf-8"))
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
                raise NotFoundError("Virtual Machine '%s' not found" % name)
            else:
                raise

    def _get_template(self, name):
        with self.objstore as session:
            params = session.get('template', name)
        return vmtemplate.VMTemplate(params)

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

    def storagepools_create(self, params):
        conn = self.conn.get()
        try:
            name = params['name']
            if name in (ISO_POOL_NAME, ):
                raise InvalidOperation("StoragePool already exists")
            xml = _get_pool_xml(**params)
        except KeyError, key:
            raise MissingParameter(key)
        if name in self.storagepools_get_list():
            raise InvalidOperation("The name %s has been used by a pool.")
        try:
            conn.storagePoolDefineXML(xml, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())
        return name

    def storagepool_lookup(self, name):
        pool = self._get_storagepool(name)
        info = pool.info()
        nr_volumes = self._get_storagepool_vols_num(pool)
        xml = pool.XMLDesc(0)
        path = xmlutils.xpath_get_text(xml, "/pool/target/path")[0]
        pool_type = xmlutils.xpath_get_text(xml, "/pool/@type")[0]
        return {'state': Model.pool_state_map[info[0]],
                'path': path,
                'type': pool_type,
                'capacity': info[1] >> 20,
                'allocated': info[2] >> 20,
                'available': info[3] >> 20,
                'nr_volumes': nr_volumes}

    def storagepool_activate(self, name):
        pool = self._get_storagepool(name)
        try:
            pool.create(0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def storagepool_deactivate(self, name):
        pool = self._get_storagepool(name)
        try:
            pool.destroy()
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def _pool_refresh(self, pool):
        try:
            pool.refresh(0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def _get_storagepool_vols_num(self, pool):
        try:
            if pool.isActive():
                self._pool_refresh(pool)
                return pool.numOfVolumes()
            else:
                return 0
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def storagepool_delete(self, name):
        pool = self._get_storagepool(name)
        if pool.isActive():
            raise InvalidOperation(
                        "Unable to delete the active storagepool %s" % name)
        try:
            pool.undefine()
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def storagepools_get_list(self):
        try:
            conn = self.conn.get()
            names = conn.listStoragePools()
            names += conn.listDefinedStoragePools()
            return names
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def _get_storagepool(self, name):
        conn = self.conn.get()
        try:
            return conn.storagePoolLookupByName(name)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_POOL:
                raise NotFoundError("Storage Pool '%s' not found" % name)
            else:
                raise

    def storagevolumes_create(self, pool, params):
        info = self.storagepool_lookup(pool)
        try:
            name = params['name']
            xml = _get_volume_xml(**params)
        except KeyError, key:
            raise MissingParameter(key)
        pool = self._get_storagepool(pool)
        try:
            pool.createXML(xml, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())
        return name

    def storagevolume_lookup(self, pool, name):
        vol = self._get_storagevolume(pool, name)
        path = vol.path()
        info = vol.info()
        xml = vol.XMLDesc(0)
        fmt = xmlutils.xpath_get_text(xml, "/volume/target/format/@type")[0]
        res = dict(type=Model.volume_type_map[info[0]],
                   capacity=info[1]>>20,
                   allocation=info[2]>>20,
                   path=path,
                   format=fmt)
        if fmt == 'iso':
            if os.path.islink(path):
                path = os.readlink(path)
            os_distro = os_version = 'unknown'
            try:
                os_distro, os_version = isoinfo.probe_one(path)
                bootable = True
            except isoinfo.IsoFormatError:
                bootable = False
            res.update(
                dict(os_distro=os_distro, os_version=os_version, path=path, bootable=bootable))

        return res

    def storagevolume_wipe(self, pool, name):
        volume = self._get_storagevolume(pool, name)
        try:
            volume.wipePattern(libvirt.VIR_STORAGE_VOL_WIPE_ALG_ZERO, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def storagevolume_delete(self, pool, name):
        volume = self._get_storagevolume(pool, name)
        try:
            volume.delete(0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def storagevolume_resize(self, pool, name, size):
        size = size << 20
        volume = self._get_storagevolume(pool, name)
        try:
            volume.resize(size, 0)
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def storagevolumes_get_list(self, pool):
        pool = self._get_storagepool(pool)
        if not pool.isActive():
            raise InvalidOperation(
            "Unable to list volumes in inactive storagepool %s" % pool.name())
        try:
            self._pool_refresh(pool)
            return pool.listVolumes()
        except libvirt.libvirtError as e:
            raise OperationFailed(e.get_error_message())

    def _get_storagevolume(self, pool, name):
        pool = self._get_storagepool(pool)
        if not pool.isActive():
            raise InvalidOperation(
            "Unable to list volumes in inactive storagepool %s" % pool.name())
        try:
            return pool.storageVolLookupByName(name)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_STORAGE_VOL:
                raise NotFoundError("Storage Volume '%s' not found" % name)
            else:
                raise

    def _get_screenshot(self, name):
        with self.objstore as session:
            try:
                params = session.get('screenshot', name)
            except NotFoundError:
                params = {'name': name}
                session.store('screenshot', name, params)
        return LibvirtVMScreenshot(params, self.conn)


class LibvirtVMScreenshot(VMScreenshot):
    def __init__(self, vm_name, conn):
        VMScreenshot.__init__(self, vm_name)
        self.conn = conn

    def _generate_scratch(self, thumbnail):
        def handler(stream, buf, opaque):
            fd = opaque
            os.write(fd, buf)

        fd = os.open(thumbnail, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0644)
        try:
            conn = self.conn.get()
            # outgoing text to libvirt, encode('utf-8')
            dom = conn.lookupByName(self.vm_name.encode('utf-8'))
            stream = conn.newStream(0)
            mimetype = dom.screenshot(stream, 0, 0)
            stream.recvAll(handler, fd)
        except libvirt.libvirtError:
            try:
                stream.abort()
            except:
                pass
            raise NotFoundError("Screenshot not supported for %s" %
                                self.vm_name)
        else:
            stream.finish()
        finally:
            os.close(fd)


def _get_pool_xml(**kwargs):
    # Required parameters
    # name:
    # type:
    # path:
    xml = """
    <pool type='%(type)s'>
      <name>%(name)s</name>
      <target>
        <path>%(path)s</path>
      </target>
    </pool>
    """ % kwargs
    return xml


def _get_volume_xml(**kwargs):
    # Required parameters
    # name:
    # capacity:
    #
    # Optional:
    # allocation:
    # format:
    kwargs.setdefault('allocation', 0)
    kwargs.setdefault('format', 'qcow2')

    xml = """
    <volume>
      <name>%(name)s</name>
      <allocation unit="MiB">%(allocation)s</allocation>
      <capacity unit="MiB">%(capacity)s</capacity>
      <source>
      </source>
      <target>
        <format type='%(format)s'/>
      </target>
    </volume>
    """ % kwargs
    return xml


class LibvirtConnection(object):
    def __init__(self, uri):
        self.uri = uri
        self._connections = {}
        self._connectionLock = threading.Lock()

    def get(self, conn_id=0):
        """
        Return current connection to libvirt or open a new one.
        """

        with self._connectionLock:
            conn = self._connections.get(conn_id)
            if not conn:
                # TODO: Retry
                conn = libvirt.open(self.uri)
                self._connections[conn_id] = conn
                # In case we're running into troubles with keeping the connections
                # alive we should place here:
                # conn.setKeepAlive(interval=5, count=3)
                # However the values need to be considered wisely to not affect
                # hosts which are hosting a lot of virtual machines
            return conn
