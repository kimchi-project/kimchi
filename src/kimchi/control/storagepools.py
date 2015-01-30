#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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

import cherrypy

from kimchi.control.base import Collection, Resource
from kimchi.control.storagevolumes import IsoVolumes, StorageVolumes
from kimchi.control.utils import get_class_name, model_fn
from kimchi.control.utils import validate_params
from kimchi.model.storagepools import ISO_POOL_NAME
from kimchi.control.utils import UrlSubNode


@UrlSubNode('storagepools', True)
class StoragePools(Collection):
    def __init__(self, model):
        super(StoragePools, self).__init__(model)
        self.role_key = 'storage'
        self.admin_methods = ['POST']
        self.resource = StoragePool
        isos = IsoPool(model)
        setattr(self, ISO_POOL_NAME, isos)

    def create(self, params, *args):
        try:
            create = getattr(self.model, model_fn(self, 'create'))
        except AttributeError:
            error = 'Create is not allowed for %s' % get_class_name(self)
            raise cherrypy.HTTPError(405, error)

        validate_params(params, self, 'create')
        args = self.model_args + [params]
        name = create(*args)
        args = self.resource_args + [name]
        res = self.resource(self.model, *args)
        resp = res.get()

        if 'task_id' in res.data:
            cherrypy.response.status = 202
        else:
            cherrypy.response.status = 201

        return resp

    def _get_resources(self, filter_params):
        try:
            res_list = super(StoragePools, self)._get_resources(filter_params)
            # Append reserved pools
            isos = getattr(self, ISO_POOL_NAME)
            isos.lookup()
            res_list.append(isos)
        except AttributeError:
            pass

        return res_list


class StoragePool(Resource):
    def __init__(self, model, ident):
        super(StoragePool, self).__init__(model, ident)
        self.role_key = 'storage'
        self.admin_methods = ['PUT', 'POST', 'DELETE']
        self.uri_fmt = "/storagepools/%s"
        self.activate = self.generate_action_handler('activate')
        self.deactivate = self.generate_action_handler('deactivate',
                                                       destructive=True)
        self.storagevolumes = StorageVolumes(self.model, ident)

    @property
    def data(self):
        res = {'name': self.ident,
               'state': self.info['state'],
               'capacity': self.info['capacity'],
               'allocated': self.info['allocated'],
               'available': self.info['available'],
               'path': self.info['path'],
               'source': self.info['source'],
               'type': self.info['type'],
               'nr_volumes': self.info['nr_volumes'],
               'autostart': self.info['autostart'],
               'persistent': self.info['persistent']}

        val = self.info.get('task_id')
        if val:
            res['task_id'] = val

        return res


class IsoPool(Resource):
    def __init__(self, model):
        super(IsoPool, self).__init__(model, ISO_POOL_NAME)
        self.storagevolumes = IsoVolumes(self.model, ISO_POOL_NAME)

    @property
    def data(self):
        return {'name': self.ident,
                'state': self.info['state'],
                'type': self.info['type']}
