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
#

import cherrypy
import json


from jsonschema import Draft3Validator, ValidationError, FormatChecker


from kimchi.auth import USER_ROLES
from kimchi.exception import InvalidParameter, OperationFailed
from kimchi.utils import import_module, listPathModules


def get_class_name(cls):
    try:
        sub_class = cls.__subclasses__()[0]
    except AttributeError:
        sub_class = cls.__class__.__name__
    return sub_class.lower()


def model_fn(cls, fn_name):
    return '%s_%s' % (get_class_name(cls), fn_name)


def validate_method(allowed, role_key, admin_methods):
    method = cherrypy.request.method.upper()
    if method not in allowed:
        raise cherrypy.HTTPError(405)

    user_role = cherrypy.session.get(USER_ROLES, {}).get(role_key)
    if user_role and user_role != 'admin' and method in admin_methods:
        raise cherrypy.HTTPError(403)

    return method


def mime_in_header(header, mime):
    if header not in cherrypy.request.headers:
        accepts = 'application/json'
    else:
        accepts = cherrypy.request.headers[header]

    if accepts.find(';') != -1:
        accepts, _ = accepts.split(';', 1)

    if mime in accepts.split(','):
        return True

    return False


def parse_request():
    if 'Content-Length' not in cherrypy.request.headers:
        return {}

    if mime_in_header('Content-Type', 'application/json'):
        if cherrypy.request.body.length == 0:
            return {}

        rawbody = cherrypy.request.body.read()
        try:
            return json.loads(rawbody)
        except ValueError:
            e = OperationFailed('KCHAPI0006E')
            raise cherrypy.HTTPError(400, e.message)
    elif mime_in_header('Content-Type', 'multipart/form-data'):
        return cherrypy.request.params
    else:
        e = OperationFailed('KCHAPI0007E')
        raise cherrypy.HTTPError(415, e.message)


def internal_redirect(url):
    raise cherrypy.InternalRedirect(url.encode("utf-8"))


def validate_params(params, instance, action):
    root = cherrypy.request.app.root

    if hasattr(root, 'api_schema'):
        api_schema = root.api_schema
    else:
        return

    operation = model_fn(instance, action)
    validator = Draft3Validator(api_schema, format_checker=FormatChecker())
    request = {operation: params}

    try:
        validator.validate(request)
    except ValidationError, e:
        if e.schema.get('error'):
            raise InvalidParameter(e.schema['error'], {'value':
                                                       str(e.instance)})
        else:
            raise InvalidParameter("KCHAPI0008E", {"err": str(e.message)})


class UrlSubNode(object):

    def __init__(self, name, auth=False):
        """
        admin_methods must be None, or a list containing zero or more of the
        string values ['GET', 'POST', 'PUT', 'DELETE']
        """
        self.name = name
        self.auth = auth

    def __call__(self, fun):
        fun._url_sub_node_name = {"name": self.name}
        fun.url_auth = self.auth
        return fun


def load_url_sub_node(path, package_name, expect_attr="_url_sub_node_name"):
    sub_nodes = {}
    for mod_name in listPathModules(path):
        if mod_name.startswith("_"):
            continue

        module = import_module(package_name + '.' + mod_name)

        for node in [getattr(module, x) for x in dir(module)]:
            if not hasattr(node, expect_attr):
                continue
            name = getattr(node, expect_attr)["name"]
            sub_nodes.update({name: node})

    return sub_nodes
