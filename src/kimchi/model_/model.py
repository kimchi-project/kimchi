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

import inspect
import logging
import os
import sys

import cherrypy
import libvirt

from kimchi.basemodel import BaseModel
from kimchi.model_.libvirtconnection import LibvirtConnection
from kimchi.objectstore import ObjectStore
from kimchi.utils import import_module, listPathModules


class Model(BaseModel):
    def __init__(self, libvirt_uri='qemu:///system', objstore_loc=None):
        self.objstore = ObjectStore(objstore_loc)
        self.conn = LibvirtConnection(libvirt_uri)
        kargs = {'objstore': self.objstore, 'conn': self.conn}

        if 'qemu:///' in libvirt_uri:
            self._default_pool_check()
            self._default_network_check()

        this = os.path.basename(__file__)
        this_mod = os.path.splitext(this)[0]

        models = []
        for mod_name in listPathModules(os.path.dirname(__file__)):
            if mod_name.startswith("_") or mod_name == this_mod:
                continue

            module = import_module('model_.' + mod_name)
            members = inspect.getmembers(module, inspect.isclass)
            for cls_name, instance in members:
                if inspect.getmodule(instance) == module:
                    if cls_name.endswith('Model'):
                        models.append(instance(**kargs))

        return super(Model, self).__init__(models)

    def _default_network_check(self):
        conn = self.conn.get()
        xml = """
            <network>
              <name>default</name>
              <forward mode='nat'/>
              <bridge name='virbr0' stp='on' delay='0' />
              <ip address='192.168.122.1' netmask='255.255.255.0'>
                <dhcp>
                  <range start='192.168.122.2' end='192.168.122.254' />
                </dhcp>
              </ip>
            </network>
        """
        try:
            net = conn.networkLookupByName("default")
        except libvirt.libvirtError:
            try:
                net = conn.networkDefineXML(xml)
            except libvirt.libvirtError, e:
                cherrypy.log.error("Fatal: Cannot create default network "
                                   "because of %s, exit kimchid" % e.message,
                                   severity=logging.ERROR)
                sys.exit(1)

        if net.isActive() == 0:
            try:
                net.create()
            except libvirt.libvirtError, e:
                cherrypy.log.error("Fatal: Cannot activate default network "
                                   "because of %s, exit kimchid" % e.message,
                                   severity=logging.ERROR)
                sys.exit(1)

    def _default_pool_check(self):
        conn = self.conn.get()
        xml = """
            <pool type='dir'>
              <name>default</name>
              <target>
                <path>/var/lib/libvirt/images</path>
              </target>
            </pool>
        """
        try:
            pool = conn.storagePoolLookupByName("default")
        except libvirt.libvirtError:
            try:
                pool = conn.storagePoolCreateXML(xml, 0)
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
