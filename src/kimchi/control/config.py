#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#  Aline Manera <alinefm@linux.vnet.ibm.com>
#  ShaoHe Feng <shaohef@linux.vnet.ibm.com>
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

    @property
    def data(self):
        caps = ['libvirt_stream_protocols', 'qemu_stream',
                'screenshot', 'system_report_tool']
        ret = dict([(x, None) for x in caps])
        ret.update(self.model.get_capabilities())
        return ret


class Distros(Collection):
    def __init__(self, model):
        super(Distros, self).__init__(model)
        self.resource = Distro


class Distro(Resource):
    def __init__(self, model, ident):
        super(Distro, self).__init__(model, ident)

    @property
    def data(self):
        return self.info
