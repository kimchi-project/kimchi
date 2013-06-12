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

import re
import threading
import time
import logging
import libvirt
import functools
import sqlite3
import os
import json
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import vmtemplate
import config
import xmlutils
import vnc
from screenshot import VMScreenshot

class NotFoundError(Exception):
    pass

class OperationFailed(Exception):
    pass

class MissingParameter(Exception):
    pass

class InvalidParameter(Exception):
    pass

class InvalidOperation(Exception):
    pass


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


class ObjectStoreSession(object):
    def __init__(self, conn):
        self.conn = conn

    def get_list(self, obj_type):
        c = self.conn.cursor()
        res = c.execute('SELECT id FROM objects WHERE type=?', (obj_type,))
        return [x[0] for x in res]

    def get(self, obj_type, ident):
        c = self.conn.cursor()
        res = c.execute('SELECT json FROM objects WHERE type=? AND id=?',
                        (obj_type, ident))
        try:
            jsonstr = res.fetchall()[0][0]
        except IndexError:
            self.conn.rollback()
            raise NotFoundError(ident)
        return json.loads(jsonstr)

    def delete(self, obj_type, ident):
        c = self.conn.cursor()
        c.execute('DELETE FROM objects WHERE type=? AND id=?',
                  (obj_type, ident))
        if c.rowcount != 1:
            self.conn.rollback()
            raise NotFoundError(ident)
        self.conn.commit()

    def store(self, obj_type, ident, data):
        jsonstr = json.dumps(data)
        c = self.conn.cursor()
        c.execute('DELETE FROM objects WHERE type=? AND id=?',
                  (obj_type, ident))
        c.execute('INSERT INTO objects (id, type, json) VALUES (?,?,?)',
                  (ident, obj_type, jsonstr))
        self.conn.commit()


class ObjectStore(object):
    def __init__(self, location=None):
        self._lock = threading.Semaphore()
        self._connections = OrderedDict()
        self.location = location or config.get_object_store()
        with self._lock:
            self._init_db()

    def _init_db(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''SELECT * FROM sqlite_master WHERE type='table' AND
                     tbl_name='objects'; ''')
        res = c.fetchall()
        if len(res) == 1:
            return

        c.execute('''CREATE TABLE objects
                     (id TEXT, type TEXT, json TEXT, PRIMARY KEY (id, type))''')
        conn.commit()

    def _get_conn(self):
        ident = threading.currentThread().ident
        try:
            return self._connections[ident]
        except KeyError:
            self._connections[ident] = sqlite3.connect(self.location, timeout=10)
            if len(self._connections.keys()) > 10:
                id, conn = self._connections.popitem(last=False)
                conn.interrupt()
                del conn
            return self._connections[ident]

    def __enter__(self):
        self._lock.acquire()
        return ObjectStoreSession(self._get_conn())

    def __exit__(self, type, value, tb):
        self._lock.release()


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
        self.vnc_ports = {}
        self.cpu_stats = {}

    def _get_cpu_stats(self, name, info):
        timestamp = time.time()
        prevCpuTime = 0
        prevTimestamp = 0

        prevStats = self.cpu_stats.get(name, None)
        if prevStats is not None:
            prevTimestamp = prevStats["timestamp"]
            prevCpuTime = prevStats["cputime"]

        self.cpu_stats[name] = {'timestamp': timestamp, 'cputime': info[4]}

        cpus = info[3]
        cpuTime = info[4] - prevCpuTime
        base = (((cpuTime) * 100.0) / ((timestamp - prevTimestamp) * 1000.0 * 1000.0 * 1000.0))

        return max(0.0, min(100.0, base / cpus))

    def vm_lookup(self, name):
        dom = self._get_vm(name)
        info = dom.info()
        state = Model.dom_state_map[info[0]]
        screenshot = 'images/image-missing.svg'
        cpu_stats = 0
        try:
            if state == 'running':
                screenshot = self.vmscreenshot_lookup(name)
                cpu_stats = self._get_cpu_stats(name, info)
        except NotFoundError:
            pass

        with self.objstore as session:
            try:
                extra_info = session.get('vm', name)
            except NotFoundError:
                extra_info = {}
        icon = extra_info.get('icon')

        return {'state': state,
                'cpu_stats': str(cpu_stats),
                'memory': info[2] >> 10,
                'screenshot': screenshot,
                'icon': icon,
                'vnc_port': self.vnc_ports.get(name, None)}

    def _vm_get_disk_paths(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='disk']/source/@file"
        return xmlutils.xpath_get_text(xml, xpath)

    def vm_delete(self, name):
        self._vmscreenshot_delete(name)
        conn = self.conn.get()
        dom = self._get_vm(name)
        paths = self._vm_get_disk_paths(dom)
        dom.undefine()

        for path in paths:
            vol = conn.storageVolLookupByPath(path)
            vol.delete(0)

        with self.objstore as session:
            session.delete('vm', name)

    def vm_start(self, name):
        dom = self._get_vm(name)
        dom.create()

    def vm_stop(self, name):
        dom = self._get_vm(name)
        dom.destroy()

    def vm_connect(self, name):
        dom = self._get_vm(name)
        xml = dom.XMLDesc(0)
        expr = "/domain/devices/graphics[@type='vnc']/@port"
        res = xmlutils.xpath_get_text(xml, expr)

        if len(res) < 1:
            raise OperationFailed("Unable to find VNC port in %s" % name)

        vnc_port = int(res[0])
        vnc_port = vnc.new_ws_proxy(vnc_port)
        self.vnc_ports[name] = vnc_port

    def vms_create(self, params):
        try:
            t_name = template_name_from_uri(params['template'])
        except KeyError, item:
            raise MissingParameter(item)

        vm_list = self.vms_get_list()
        name = get_vm_name(params.get('name'), t_name, vm_list)
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
            pool.createXML(v['xml'], 0)

        # Store the icon for displaying later
        icon = t.info.get('icon')
        if icon:
            with self.objstore as session:
                session.store('vm', name, {'icon': icon})

        xml = t.to_vm_xml(name, storage_path)
        dom = conn.defineXML(xml)
        return name

    def vms_get_list(self):
        conn = self.conn.get()
        ids = conn.listDomainsID()
        names = map(lambda x: conn.lookupByID(x).name(), ids)
        names += conn.listDefinedDomains()
        return names

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
            t = vmtemplate.VMTemplate(params)
            session.store('template', name, t.info)
        return name

    def templates_get_list(self):
        with self.objstore as session:
            return session.get_list('template')

    def _get_vm(self, name):
        conn = self.conn.get()
        try:
            return conn.lookupByName(name)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
                raise NotFoundError("Virtual Machine '%s' not found" % name)
            else:
                raise

    def _get_template(self, name):
        with self.objstore as session:
            params = session.get('template', name)
        return vmtemplate.VMTemplate(params)

    def storagepools_create(self, params):
        conn = self.conn.get()
        try:
            xml = _get_pool_xml(**params)
            name = params['name']
        except KeyError, key:
            raise MissingParameter(key)
        pool = conn.storagePoolDefineXML(xml, 0)
        return name

    def storagepool_lookup(self, name):
        pool = self._get_storagepool(name)
        info = pool.info()
        xml = pool.XMLDesc(0)
        path = xmlutils.xpath_get_text(xml, "/pool/target/path")[0]
        pool_type = xmlutils.xpath_get_text(xml, "/pool/@type")[0]
        return {'state': Model.pool_state_map[info[0]],
                'path': path,
                'type': pool_type,
                'capacity': info[1] >> 20,
                'allocated': info[2] >> 20,
                'available': info[3] >> 20}

    def storagepool_activate(self, name):
        pool = self._get_storagepool(name)
        pool.create(0)

    def storagepool_deactivate(self, name):
        pool = self._get_storagepool(name)
        pool.destroy()

    def storagepool_delete(self, name):
        pool = self._get_storagepool(name)
        if pool.isActive():
            raise InvalidOperation(
                        "Unable to delete the active storagepool %s" % name)
        pool.undefine()

    def storagepools_get_list(self):
        conn = self.conn.get()
        names = conn.listStoragePools()
        names += conn.listDefinedStoragePools()
        return names

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
            params['path'] = os.path.join(info['path'], name)
            xml = _get_volume_xml(**params)
        except KeyError, key:
            raise MissingParameter(key)
        pool = self._get_storagepool(pool)
        pool.createXML(xml, 0)
        return name

    def storagevolume_lookup(self, pool, name):
        vol = self._get_storagevolume(pool, name)
        path = vol.path()
        info = vol.info()
        xml = vol.XMLDesc(0)
        fmt = xmlutils.xpath_get_text(xml, "/volume/target/format/@type")[0]
        return {'type': Model.volume_type_map[info[0]],
                'capacity': info[1] >> 20,
                'allocation': info[2] >> 20,
                'path': path,
                'format': fmt}

    def storagevolume_wipe(self, pool, name):
        volume = self._get_storagevolume(pool, name)
        volume.wipePattern(libvirt.VIR_STORAGE_VOL_WIPE_ALG_ZERO, 0)

    def storagevolume_delete(self, pool, name):
        volume = self._get_storagevolume(pool, name)
        volume.delete(0)

    def storagevolume_resize(self, pool, name, size):
        size = size << 20
        volume = self._get_storagevolume(pool, name)
        volume.resize(size, 0)

    def storagevolumes_get_list(self, pool):
        pool = self._get_storagepool(pool)
        return pool.listVolumes()

    def _get_storagevolume(self, pool, name):
        pool = self._get_storagepool(pool)
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
            dom = conn.lookupByName(self.vm_name)
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
        <path>%(path)s</path>
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
        log = logging.getLogger('LibvirtConnection')

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
