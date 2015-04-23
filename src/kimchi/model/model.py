#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
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
import os

from kimchi.basemodel import BaseModel
from kimchi.model.libvirtconnection import LibvirtConnection
from kimchi.objectstore import ObjectStore
from kimchi.utils import import_module, listPathModules


class Model(BaseModel):
    def __init__(self, libvirt_uri=None, objstore_loc=None):

        self.objstore = ObjectStore(objstore_loc)
        self.conn = LibvirtConnection(libvirt_uri)
        kargs = {'objstore': self.objstore, 'conn': self.conn}

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
