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

import vmtemplate

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


def template_name_from_uri(uri):
    m = re.match('/templates/(.*?)/?$', uri)
    if not m:
        raise InvalidParameter(uri)
    return m.group(1)


class Model(object):
    dom_state_map = {0: 'nostate',
                     1: 'running',
                     2: 'blocked',
                     3: 'paused',
                     4: 'shutdown',
                     5: 'shutoff',
                     6: 'crashed' }

    def __init__(self, libvirt_uri=None):
        self.libvirt_uri = libvirt_uri or 'qemu:///system'
        self.conn = LibvirtConnection(self.libvirt_uri)

        # TODO: Replace this with persistent storage
        self.shelf = {}
        self.shelf.setdefault('templates', {})

    def vm_lookup(self, name):
        dom = self._get_vm(name)
        info = dom.info()
        return {'state': Model.dom_state_map[info[0]],
                'memory': info[2] >> 10,
                'screenshot': 'images/image-missing.svg'}

    def vm_delete(self, name):
        dom = self._get_vm(name)
        dom.undefine()

    def vm_start(self, name):
        dom = self._get_vm(name)
        dom.create()

    def vm_stop(self, name):
        dom = self._get_vm(name)
        dom.destroy()

    def vms_create(self, params):
        try:
            name = params['name']
            t_name = template_name_from_uri(params['template'])
        except KeyError, item:
            raise MissingParameter(item)
        if name in self.vms_get_list():
            raise InvalidOperation("VM already exists")

        # TODO: Lookup Storage path using the libvirt API once Pools are modeled
        storage_path = "/var/lib/libvirt/images"

        t = self._get_template(t_name)
        xml = t.to_vm_xml(name, storage_path)
        conn = self.conn.get()
        dom = conn.defineXML(xml)

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
        try:
            del self.shelf['templates'][name]
        except KeyError:
            raise NotFoundError()

    def templates_create(self, params):
        name = params['name']
        if name in self.shelf['templates']:
            raise InvalidOperation("Template already exists")
        t = vmtemplate.VMTemplate(params)
        self.shelf['templates'][name] = t.info

    def templates_get_list(self):
        return self.shelf['templates'].keys()

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
        try:
            params = self.shelf['templates'][name]
        except KeyError:
            raise NotFoundError()
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
