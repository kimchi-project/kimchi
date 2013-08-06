#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
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
import template
import controller
import json


def error_page_handler(status, message, traceback, version):
    data = {'reason': message, 'call_stack': cherrypy._cperror.format_exc()}
    return json.dumps(data, indent=2,
                          separators=(',', ':'),
                          encoding='iso-8859-1')

class Root(controller.Resource):
    _handled_error = ['error_page.400',
        'error_page.404', 'error_page.405',
        'error_page.406', 'error_page.415', 'error_page.500']
    _cp_config = dict(map(lambda(x): (x, error_page_handler), _handled_error))

    def __init__(self, model):
        controller.Resource.__init__(self, model)
        self.vms = controller.VMs(model)
        self.templates = controller.Templates(model)
        self.storagepools = controller.StoragePools(model)
        self.tasks = controller.Tasks(model)

    def get(self):
        return self.default('kimchi-ui.html')

    @cherrypy.expose
    def default(self, page, **kwargs):
        if page.endswith('.html'):
            return template.render(page, None)
        raise cherrypy.HTTPError(404)
