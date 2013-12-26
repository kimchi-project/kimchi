#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import cherrypy
import urllib2


from functools import wraps


import kimchi.template
from kimchi.control.utils import get_class_name, internal_redirect, model_fn
from kimchi.control.utils import parse_request, validate_method, validate_params
from kimchi.exception import InvalidOperation, InvalidParameter, MissingParameter
from kimchi.exception import NotFoundError,  OperationFailed
from kimchi.model import ISO_POOL_NAME


class Task(Resource):
    def __init__(self, model, id):
        super(Task, self).__init__(model, id)

    @property
    def data(self):
        return {'id': self.ident,
                'status': self.info['status'],
                'message': self.info['message']}


class Tasks(Collection):
    def __init__(self, model):
        super(Tasks, self).__init__(model)
        self.resource = Task


class Host(Resource):
    def __init__(self, model, id=None):
        super(Host, self).__init__(model, id)
        self.stats = HostStats(self.model)
        self.stats.exposed = True
        self.uri_fmt = '/host/%s'
        self.reboot = self.generate_action_handler('reboot')
        self.shutdown = self.generate_action_handler('shutdown')
        self.partitions = Partitions(self.model)
        self.partitions.exposed = True

    @property
    def data(self):
        return self.info

class HostStats(Resource):
    @property
    def data(self):
        return self.info

class Partitions(Collection):
    def __init__(self, model):
        super(Partitions, self).__init__(model)
        self.resource = Partition


class Partition(Resource):
    def __init__(self, model,id):
        super(Partition, self).__init__(model,id)

    @property
    def data(self):
        return self.info

class Plugins(Collection):
    def __init__(self, model):
        super(Plugins, self).__init__(model)
        self.model = model

    @property
    def data(self):
        return self.info

    def get(self):
        res_list = []
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            res_list = get_list(*self.model_args)
        except AttributeError:
            pass
        return kimchi.template.render(get_class_name(self), res_list)
