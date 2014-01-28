#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import copy

import libvirt

from kimchi import xmlutils
from kimchi.exception import InvalidOperation, InvalidParameter, NotFoundError
from kimchi.utils import pool_name_from_uri
from kimchi.vmtemplate import VMTemplate


class TemplatesModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']

    def create(self, params):
        name = params['name']
        conn = self.conn.get()

        pool_uri = params.get(u'storagepool', '')
        if pool_uri:
            pool_name = pool_name_from_uri(pool_uri)
            try:
                conn.storagePoolLookupByName(pool_name)
            except Exception as e:
                err = "Storagepool specified is not valid: %s."
                raise InvalidParameter(err % e.message)

        for net_name in params.get(u'networks', []):
            try:
                conn.networkLookupByName(net_name)
            except Exception, e:
                raise InvalidParameter("Network '%s' specified by template "
                                       "does not exist." % net_name)

        with self.objstore as session:
            if name in session.get_list('template'):
                raise InvalidOperation("Template already exists")
            t = LibvirtVMTemplate(params, scan=True)
            session.store('template', name, t.info)
        return name

    def get_list(self):
        with self.objstore as session:
            return session.get_list('template')


class TemplateModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']
        self.templates = TemplatesModel(**kargs)

    @staticmethod
    def get_template(name, objstore, conn, overrides=None):
        with objstore as session:
            params = session.get('template', name)
        if overrides:
            params.update(overrides)
        return LibvirtVMTemplate(params, False, conn)

    def lookup(self, name):
        t = self.get_template(name, self.objstore, self.conn)
        return t.info

    def delete(self, name):
        with self.objstore as session:
            session.delete('template', name)

    def update(self, name, params):
        old_t = self.lookup(name)
        new_t = copy.copy(old_t)
        new_t.update(params)
        ident = name

        pool_uri = new_t.get(u'storagepool', '')
        pool_name = pool_name_from_uri(pool_uri)
        try:
            conn = self.conn.get()
            conn.storagePoolLookupByName(pool_name)
        except Exception as e:
            err = "Storagepool specified is not valid: %s."
            raise InvalidParameter(err % e.message)

        for net_name in params.get(u'networks', []):
            try:
                conn = self.conn.get()
                conn.networkLookupByName(net_name)
            except Exception, e:
                raise InvalidParameter("Network '%s' specified by template "
                                       "does not exist" % net_name)

        self.delete(name)
        try:
            ident = self.templates.create(new_t)
        except:
            ident = self.templates.create(old_t)
            raise
        return ident


class LibvirtVMTemplate(VMTemplate):
    def __init__(self, args, scan=False, conn=None):
        VMTemplate.__init__(self, args, scan)
        self.conn = conn

    def _storage_validate(self):
        pool_uri = self.info['storagepool']
        pool_name = pool_name_from_uri(pool_uri)
        try:
            conn = self.conn.get()
            pool = conn.storagePoolLookupByName(pool_name)
        except libvirt.libvirtError:
            err = 'Storage specified by template does not exist'
            raise InvalidParameter(err)

        if not pool.isActive():
            err = 'Storage specified by template is not active'
            raise InvalidParameter(err)

        return pool

    def _network_validate(self):
        names = self.info['networks']
        for name in names:
            try:
                conn = self.conn.get()
                network = conn.networkLookupByName(name)
            except libvirt.libvirtError:
                err = 'Network specified by template does not exist'
                raise InvalidParameter(err)

            if not network.isActive():
                err = 'Network specified by template is not active'
                raise InvalidParameter(err)

    def _get_storage_path(self):
        pool = self._storage_validate()
        xml = pool.XMLDesc(0)
        return xmlutils.xpath_get_text(xml, "/pool/target/path")[0]

    def fork_vm_storage(self, vm_uuid):
        # Provision storage:
        # TODO: Rebase on the storage API once upstream
        pool = self._storage_validate()
        vol_list = self.to_volume_list(vm_uuid)
        for v in vol_list:
            # outgoing text to libvirt, encode('utf-8')
            pool.createXML(v['xml'].encode('utf-8'), 0)
        return vol_list
