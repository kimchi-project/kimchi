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

from kimchi.control.base import Collection, Resource
from kimchi.control.utils import UrlSubNode


@UrlSubNode("config")
class Config(Resource):
    def __init__(self, model, id=None):
        super(Config, self).__init__(model, id)
        self.capabilities = Capabilities(self.model)
        self.distros = Distros(model)

    @property
    def data(self):
        return self.info


class Capabilities(Resource):
    def __init__(self, model, id=None):
        super(Capabilities, self).__init__(model, id)

    @property
    def data(self):
        return self.info


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
