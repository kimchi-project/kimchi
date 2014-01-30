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
import os


from kimchi import auth
from kimchi import template
from kimchi.config import paths
from kimchi.control import sub_nodes
from kimchi.control.base import Resource
from kimchi.control.utils import parse_request
from kimchi.exception import OperationFailed


class Root(Resource):
    def __init__(self, model, dev_env):
        super(Root, self).__init__(model)
        self._handled_error = ['error_page.400', 'error_page.404',
                               'error_page.405', 'error_page.406',
                               'error_page.415', 'error_page.500']

        if not dev_env:
            self._cp_config = dict([(key, self.error_production_handler)
                                    for key in self._handled_error])
        else:
            self._cp_config = dict([(key, self.error_development_handler)
                                    for key in self._handled_error])

        for ident, node in sub_nodes.items():
            setattr(self, ident, node(model))
        self.api_schema = json.load(open(os.path.join(paths.src_dir,
                                                      'API.json')))

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
