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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import cherrypy
import json


from kimchi import auth
from kimchi import controller
from kimchi import template
from kimchi.config import get_api_schema_file
from kimchi.control.base import Resource
from kimchi.control.utils import parse_request
from kimchi.control.vms import VMs
from kimchi.exception import OperationFailed


class Root(Resource):
    def __init__(self, model, dev_env):
        self._handled_error = ['error_page.400', 'error_page.404',
                               'error_page.405', 'error_page.406',
                               'error_page.415', 'error_page.500']

        if not dev_env:
            self._cp_config = dict([(key, self.error_production_handler)
                                    for key in self._handled_error])
        else:
            self._cp_config = dict([(key, self.error_development_handler)
                                    for key in self._handled_error])

        Resource.__init__(self, model)
        self.vms = VMs(model)
        self.templates = controller.Templates(model)
        self.storagepools = controller.StoragePools(model)
        self.interfaces = controller.Interfaces(model)
        self.networks = controller.Networks(model)
        self.tasks = controller.Tasks(model)
        self.config = controller.Config(model)
        self.host = controller.Host(model)
        self.debugreports = controller.DebugReports(model)
        self.plugins = controller.Plugins(model)
        self.api_schema = json.load(open(get_api_schema_file()))

    def error_production_handler(self, status, message, traceback, version):
        data = {'code': status, 'reason': message}
        res = template.render('error.html', data)
        if type(res) is unicode:
            res = res.encode("utf-8")
        return res

    def error_development_handler(self, status, message, traceback, version):
        data = {'code': status, 'reason': message,
                'call_stack': cherrypy._cperror.format_exc()}
        res = template.render('error.html', data)
        if type(res) is unicode:
            res = res.encode("utf-8")
        return res

    def get(self):
        return self.default('kimchi-ui.html')

    @cherrypy.expose
    def default(self, page, **kwargs):
        if page.endswith('.html'):
            return template.render(page, None)
        raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def tabs(self, page, **kwargs):
        if page.endswith('.html'):
            return template.render('tabs/' + page, None)
        raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def login(self, *args):
        params = parse_request()
        try:
            userid = params['userid']
            password = params['password']
        except KeyError, key:
            raise cherrypy.HTTPError(400, "Missing parameter: '%s'" % key)

        try:
            auth.login(userid, password)
        except OperationFailed:
            raise cherrypy.HTTPError(401)

        return '{}'

    @cherrypy.expose
    def logout(self):
        auth.logout()
        return '{}'
