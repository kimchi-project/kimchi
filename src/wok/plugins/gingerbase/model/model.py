#
# Project Ginger Base
#
# Copyright IBM, Corp. 2015
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

from wok.basemodel import BaseModel
from wok.objectstore import ObjectStore
from wok.plugins.gingerbase import config
from wok.utils import import_module, listPathModules


class Model(BaseModel):
    def __init__(self, objstore_loc=None):

        def get_instances(module_name):
            instances = []
            module = import_module(module_name)
            members = inspect.getmembers(module, inspect.isclass)
            for cls_name, instance in members:
                if inspect.getmodule(instance) == module and \
                   cls_name.endswith('Model'):
                    instances.append(instance)

            return instances

        if objstore_loc is None:
            objstore_loc = config.get_object_store()

        self.objstore = ObjectStore(objstore_loc)
        kargs = {'objstore': self.objstore}

        models = []
        # Import task model from Wok
        instances = get_instances('wok.model.tasks')
        for instance in instances:
            models.append(instance(**kargs))

        # Import all Kimchi plugin models
        this = os.path.basename(__file__)
        this_mod = os.path.splitext(this)[0]

        for mod_name in listPathModules(os.path.dirname(__file__)):
            if mod_name.startswith("_") or mod_name == this_mod:
                continue

            instances = get_instances('wok.plugins.gingerbase.model.'
                                      + mod_name)
            for instance in instances:
                models.append(instance(**kargs))

        return super(Model, self).__init__(models)
