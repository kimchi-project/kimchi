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


class Interfaces(Collection):
    def __init__(self, model):
        super(Interfaces, self).__init__(model)
        self.resource = Interface


class Interface(Resource):
    def __init__(self, model, ident):
        super(Interface, self).__init__(model, ident)
        self.uri_fmt = "/interfaces/%s"

    @property
    def data(self):
        return {'name': self.ident,
                'type': self.info['type'],
                'ipaddr': self.info['ipaddr'],
                'netmask': self.info['netmask'],
                'status': self.info['status']}


class Networks(Collection):
    def __init__(self, model):
        super(Networks, self).__init__(model)
        self.resource = Network


class Network(Resource):
    def __init__(self, model, ident):
        super(Network, self).__init__(model, ident)
        self.uri_fmt = "/networks/%s"
        self.activate = self.generate_action_handler('activate')
        self.deactivate = self.generate_action_handler('deactivate')

    @property
    def data(self):
        return {'name': self.ident,
                'autostart': self.info['autostart'],
                'connection': self.info['connection'],
                'interface': self.info['interface'],
                'subnet': self.info['subnet'],
                'dhcp': self.info['dhcp'],
                'state': self.info['state']}


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


class Config(Resource):
    def __init__(self, model, id=None):
        super(Config, self).__init__(model, id)
        self.capabilities = Capabilities(self.model)
        self.capabilities.exposed = True
        self.distros = Distros(model)
        self.distros.exposed = True

    @property
    def data(self):
        return {'http_port': cherrypy.server.socket_port}

class Capabilities(Resource):
    def __init__(self, model, id=None):
        super(Capabilities, self).__init__(model, id)
        self.model = model

    @property
    def data(self):
        caps = ['libvirt_stream_protocols', 'qemu_stream',
                'screenshot', 'system_report_tool']
        ret = dict([(x, None) for x in caps])
        ret.update(self.model.get_capabilities())
        return ret


class Distro(Resource):
    def __init__(self, model, ident):
        super(Distro, self).__init__(model, ident)

    @property
    def data(self):
        return self.info


class Distros(Collection):
    def __init__(self, model):
        super(Distros, self).__init__(model)
        self.resource = Distro


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
