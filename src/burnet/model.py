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
import logging
import libvirt
import functools
import sqlite3
import os
import json
from collections import OrderedDict

import vmtemplate
import config
import xmlutils
import vnc

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
                     6: 'crashed' }

    def __init__(self, libvirt_uri=None, objstore_loc=None):
        self.libvirt_uri = libvirt_uri or 'qemu:///system'
        self.conn = LibvirtConnection(self.libvirt_uri)
        self.objstore = ObjectStore(objstore_loc)
        self.vnc_ports = {}

    def vm_lookup(self, name):
        dom = self._get_vm(name)
        info = dom.info()
        return {'state': Model.dom_state_map[info[0]],
                'memory': info[2] >> 10,
                'screenshot': 'images/image-missing.svg',
                'vnc_port': self.vnc_ports.get(name, None)}

    def _vm_get_disk_paths(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='disk']/source/@file"
        return xmlutils.xpath_get_text(xml, xpath)

    def vm_delete(self, name):
        conn = self.conn.get()
        dom = self._get_vm(name)
        paths = self._vm_get_disk_paths(dom)
        dom.undefine()

        for path in paths:
            vol = conn.storageVolLookupByPath(path)
            vol.delete(0)

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

        xml = t.to_vm_xml(name, storage_path)
        dom = conn.defineXML(xml)
        return name

    def vms_get_list(self):
        conn = self.conn.get()
        ids = conn.listDomainsID()
        names = map(lambda x: conn.lookupByID(x).name(), ids)
        names += conn.listDefinedDomains()
        return names

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
