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

import cherrypy
import json
import os


from distutils.version import LooseVersion
from kimchi import auth
from kimchi import template
from kimchi.i18n import messages
from kimchi.config import paths
from kimchi.control import sub_nodes
from kimchi.control.base import Resource
from kimchi.control.utils import parse_request
from kimchi.exception import MissingParameter, OperationFailed


class Root(Resource):
    def __init__(self, model, dev_env=False):
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

    def error_production_handler(self, status, message, traceback, version):
        data = {'code': status, 'reason': message}
        res = template.render('error.html', data)
        if (type(res) is unicode and
                LooseVersion(cherrypy.__version__) < LooseVersion('3.2.5')):
            res = res.encode("utf-8")
        return res

    def error_development_handler(self, status, message, traceback, version):
        data = {'code': status, 'reason': message,
                'call_stack': cherrypy._cperror.format_exc()}
        res = template.render('error.html', data)
        if (type(res) is unicode and
                LooseVersion(cherrypy.__version__) < LooseVersion('3.2.5')):
            res = res.encode("utf-8")
        return res

    def get(self):
        return self.default(self.default_page)

    @cherrypy.expose
    def default(self, page, **kwargs):
        if page.endswith('.html'):
            return template.render(page, None)
        raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def tabs(self, page, **kwargs):
        # In order to load the Guests tab, we also use Cheetah in the tab
        # template to save the delay of the extra get to the guest page
        # For that, the tab template needs to know the correct path to ui files
        data = {}
        data['ui_dir'] = paths.ui_dir

        if page.endswith('.html'):
            return template.render('tabs/' + page, data)
        raise cherrypy.HTTPError(404)


class KimchiRoot(Root):
    def __init__(self, model, dev_env):
        super(KimchiRoot, self).__init__(model, dev_env)
        self.default_page = 'kimchi-ui.html'
        for ident, node in sub_nodes.items():
            setattr(self, ident, node(model))
        self.api_schema = json.load(open(os.path.join(paths.src_dir,
                                                      'API.json')))
        self.paths = paths
        self.domain = 'kimchi'
        self.messages = messages

    @cherrypy.expose
    def login(self, *args):
        params = parse_request()
        try:
            userid = params['userid']
            password = params['password']
        except KeyError, item:
            e = MissingParameter('KCHAUTH0003E', {'item': str(item)})
            raise cherrypy.HTTPError(400, e.message)

        try:
            user_info = auth.login(userid, password)
        except OperationFailed:
            raise cherrypy.HTTPError(401)

        return json.dumps(user_info)

    @cherrypy.expose
    def logout(self):
        auth.logout()
        return '{}'
