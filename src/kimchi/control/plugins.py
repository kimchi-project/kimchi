#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
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
from kimchi.control.base import Collection
from kimchi.control.utils import get_class_name, model_fn
from kimchi.control.utils import UrlSubNode


@UrlSubNode("plugins")
class Plugins(Collection):
    def __init__(self, model):
        super(Plugins, self).__init__(model)

    @property
    def data(self):
        return self.info

    def get(self, filter_params):
        res_list = []
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            res_list = get_list(*self.model_args)
        except AttributeError:
            pass
        return kimchi.template.render(get_class_name(self), res_list)
