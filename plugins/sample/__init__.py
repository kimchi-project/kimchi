#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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

import json
import os


from cherrypy import expose


from kimchi.config import PluginPaths
from kimchi.control.base import Collection, Resource
from kimchi.root import Root
from plugins.sample.i18n import messages
from plugins.sample.model import Model


model = Model()


class Drawings(Root):
    def __init__(self):
        Resource.__init__(self, model)
        self.description = Description(model)
        self.rectangles = Rectangles(model)
        self.circles = Circles(model)
        self.paths = PluginPaths('sample')
        self.domain = 'sample'
        self.messages = messages
        self.api_schema = json.load(open(os.path.join(os.path.dirname(
                                    os.path.abspath(__file__)), 'API.json')))

    @expose
    def index(self):
        return 'This is a sample plugin for Kimchi'


class Description(Resource):
    def __init__(self, model):
        super(Description, self).__init__(model)

    @property
    def data(self):
        return {'name': 'sample', 'version': '0.1'}


class Circles(Collection):
    def __init__(self, model):
        super(Circles, self).__init__(model)
        self.resource = Circle
        self.admin_methods = ['POST', 'PUT']


class Rectangles(Collection):
    def __init__(self, model):
        super(Rectangles, self).__init__(model)
        self.resource = Rectangle
        self.admin_methods = ['POST', 'PUT']


class Circle(Resource):
    def __init__(self, model, ident):
        super(Circle, self).__init__(model, ident)
        self.update_params = ['radius']

    @property
    def data(self):
        ret = {'name': self.ident}
        ret.update(self.info)
        return ret


class Rectangle(Resource):
    def __init__(self, model, ident):
        super(Rectangle, self).__init__(model, ident)
        self.update_params = ['length', 'width']

    @property
    def data(self):
        self.info.update({'name': self.ident})
        return self.info
