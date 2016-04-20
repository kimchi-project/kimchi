#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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

from wok.control.base import Collection, Resource
from wok.control.utils import get_class_name, model_fn
from wok.control.utils import validate_params
from wok.control.utils import UrlSubNode

from wok.plugins.kimchi.control.storagevolumes import IsoVolumes
from wok.plugins.kimchi.control.storagevolumes import StorageVolumes
from wok.plugins.kimchi.model.storagepools import ISO_POOL_NAME


STORAGEPOOLS_REQUESTS = {
    'POST': {'default': "Create %(type)s storage pool '%(name)s'"},
}

STORAGEPOOL_REQUESTS = {
    'DELETE': {'default': "Remove storage pool '%(ident)s'"},
    'PUT': {'default': "Update storage pool '%(ident)s'"},
    'POST': {
        'activate': "Activate storage pool '%(ident)s'",
        'deactivate': "Deactivate storage pool '%(ident)s'",
    },
}


@UrlSubNode('storagepools', True)
class StoragePools(Collection):
    def __init__(self, model):
        super(StoragePools, self).__init__(model)
        self.role_key = 'storage'
        self.admin_methods = ['POST']
        self.resource = StoragePool
        isos = IsoPool(model)
        setattr(self, ISO_POOL_NAME, isos)
        self.log_map = STORAGEPOOLS_REQUESTS

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
        res.lookup()
        resp = res.get()
        cherrypy.response.status = 202 if 'task_id' in res.data else 201

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
        self.log_map = STORAGEPOOL_REQUESTS

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
               'persistent': self.info['persistent'],
               'in_use': self.info['in_use']}

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
