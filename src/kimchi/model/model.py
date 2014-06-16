#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
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

import inspect
import logging
import os
import sys

import cherrypy
import libvirt
import lxml.etree as ET
from lxml.builder import E

from kimchi.basemodel import BaseModel
from kimchi.model.libvirtconnection import LibvirtConnection
from kimchi.objectstore import ObjectStore
from kimchi.utils import import_module, listPathModules


DEFAULT_POOLS = {'default': {'path': '/var/lib/libvirt/images'},
                 'ISO': {'path': '/var/lib/kimchi/isos'}}


class Model(BaseModel):
    def __init__(self, libvirt_uri='qemu:///system', objstore_loc=None):
        self.objstore = ObjectStore(objstore_loc)
        self.conn = LibvirtConnection(libvirt_uri)
        kargs = {'objstore': self.objstore, 'conn': self.conn}

        if 'qemu:///' in libvirt_uri:
            for pool_name, pool_arg in DEFAULT_POOLS.iteritems():
                self._default_pool_check(pool_name, pool_arg)

        this = os.path.basename(__file__)
        this_mod = os.path.splitext(this)[0]

        models = []
        for mod_name in listPathModules(os.path.dirname(__file__)):
            if mod_name.startswith("_") or mod_name == this_mod:
                continue

            module = import_module('model.' + mod_name)
            members = inspect.getmembers(module, inspect.isclass)
            for cls_name, instance in members:
                if inspect.getmodule(instance) == module:
                    if cls_name.endswith('Model'):
                        models.append(instance(**kargs))

        return super(Model, self).__init__(models)

    def _default_pool_check(self, pool_name, pool_arg):
        conn = self.conn.get()
        pool = E.pool(E.name(pool_name), type='dir')
        pool.append(E.target(E.path(pool_arg['path'])))
        xml = ET.tostring(pool)
        try:
            pool = conn.storagePoolLookupByName(pool_name)
        except libvirt.libvirtError:
            try:
                pool = conn.storagePoolDefineXML(xml, 0)
                # Add build step to make sure target directory created
                pool.build(libvirt.VIR_STORAGE_POOL_BUILD_NEW)
                pool.setAutostart(1)
            except libvirt.libvirtError, e:
                cherrypy.log.error("Fatal: Cannot create default pool because "
                                   "of %s, exit kimchid" % e.message,
                                   severity=logging.ERROR)
                sys.exit(1)

        if pool.isActive() == 0:
            try:
                pool.create(0)
            except libvirt.libvirtError, e:
                err = "Fatal: Default pool cannot be activated, exit kimchid"
                cherrypy.log.error(err, severity=logging.ERROR)
                sys.exit(1)
