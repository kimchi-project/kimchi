#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#  Aline Manera <alinefm@linux.vnet.ibm.com>
#  Bing Bu Cao <mars@linux.vnet.ibm.com>
#  Royce Lv <lvroyce@linux.vnet.ibm.com>
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

import kimchi.template
from kimchi.control.base import Collection, Resource
from kimchi.control.utils import get_class_name, model_fn


class StorageVolumes(Collection):
    def __init__(self, model, pool):
        super(StorageVolumes, self).__init__(model)
        self.resource = StorageVolume
        self.pool = pool
        self.resource_args = [self.pool, ]
        self.model_args = [self.pool, ]


class StorageVolume(Resource):
    def __init__(self, model, pool, ident):
        super(StorageVolume, self).__init__(model, ident)
        self.pool = pool
        self.ident = ident
        self.info = {}
        self.model_args = [self.pool, self.ident]
        self.uri_fmt = '/storagepools/%s/storagevolumes/%s'
        self.resize = self.generate_action_handler('resize', ['size'])
        self.wipe = self.generate_action_handler('wipe')

    @property
    def data(self):
        res = {'name': self.ident,
               'type': self.info['type'],
               'capacity': self.info['capacity'],
               'allocation': self.info['allocation'],
               'path': self.info['path'],
               'format': self.info['format']}

        for key in ('os_version', 'os_distro', 'bootable'):
            val = self.info.get(key)
            if val:
                res[key] = val

        return res


class IsoVolumes(Collection):
    def __init__(self, model, pool):
        super(IsoVolumes, self).__init__(model)
        self.pool = pool

    def get(self, filter_params):
        res_list = []
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            res_list = get_list(*self.model_args)
        except AttributeError:
            pass

        return kimchi.template.render(get_class_name(self), res_list)
