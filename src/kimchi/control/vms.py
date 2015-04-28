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

from kimchi.control.base import AsyncCollection, Resource
from kimchi.control.utils import internal_redirect, UrlSubNode
from kimchi.control.vm import sub_nodes


@UrlSubNode('vms', True)
class VMs(AsyncCollection):
    def __init__(self, model):
        super(VMs, self).__init__(model)
        self.resource = VM
        self.role_key = 'guests'
        self.admin_methods = ['POST']


class VM(Resource):
    def __init__(self, model, ident):
        super(VM, self).__init__(model, ident)
        self.role_key = 'guests'
        self.screenshot = VMScreenShot(model, ident)
        self.uri_fmt = '/vms/%s'
        for ident, node in sub_nodes.items():
            setattr(self, ident, node(model, self.ident))
        self.start = self.generate_action_handler('start')
        self.poweroff = self.generate_action_handler('poweroff',
                                                     destructive=True)
        self.shutdown = self.generate_action_handler('shutdown',
                                                     destructive=True)
        self.reset = self.generate_action_handler('reset',
                                                  destructive=True)
        self.connect = self.generate_action_handler('connect')
        self.clone = self.generate_action_handler_task('clone')
        self.suspend = self.generate_action_handler('suspend')
        self.resume = self.generate_action_handler('resume')

    @property
    def data(self):
        return self.info


class VMScreenShot(Resource):
    def __init__(self, model, ident):
        super(VMScreenShot, self).__init__(model, ident)
        self.role_key = 'guests'

    def get(self):
        self.lookup()
        raise internal_redirect(self.info)
