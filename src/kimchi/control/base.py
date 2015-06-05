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

import cherrypy
import re
import urllib2


import kimchi.template
from kimchi.auth import USER_GROUPS, USER_NAME, USER_ROLES
from kimchi.control.utils import get_class_name, internal_redirect, model_fn
from kimchi.control.utils import parse_request, validate_method
from kimchi.control.utils import validate_params
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import KimchiException, MissingParameter, NotFoundError
from kimchi.exception import OperationFailed, UnauthorizedError


class Resource(object):
    """
    A Resource represents a single entity in the API (such as a Virtual
    Machine)

    To create new Resource types, subclass this and change the following things
    in the child class:

    - If the Resource requires more than one identifier set self.model_args as
      appropriate.  This should only be necessary if this Resource is logically
      nested.  For example: A Storage Volume belongs to a Storage Pool so the
      Storage Volume would set model args to (pool_ident, volume_ident).

    - Implement the base operations of 'lookup' and 'delete' in the model(s).

    - Set the 'data' property to a JSON-serializable representation of the
      Resource.
    """
    def __init__(self, model, ident=None):
        self.model = model
        self.ident = ident
        self.model_args = (ident,)
        self.role_key = None
        self.admin_methods = []

    def _redirect(self, action_result, code=303):
        if isinstance(action_result, list):
            uri_params = []
            for arg in action_result:
                if arg is None:
                    arg = ''
                uri_params.append(urllib2.quote(arg.encode('utf-8'), safe=""))
            raise cherrypy.HTTPRedirect(self.uri_fmt % tuple(uri_params), code)
        elif action_result is not None and action_result != self.ident:
            uri_params = list(self.model_args[:-1])
            uri_params += [urllib2.quote(action_result.encode('utf-8'),
                           safe="")]
            raise cherrypy.HTTPRedirect(self.uri_fmt % tuple(uri_params), code)

    def generate_action_handler(self, action_name, action_args=None,
                                destructive=False):
        def _render_element(self, ident):
            self._redirect(ident)
            uri_params = []
            for arg in self.model_args:
                if arg is None:
                    arg = ''
                uri_params.append(urllib2.quote(arg.encode('utf-8'),
                                  safe=""))
            raise internal_redirect(self.uri_fmt % tuple(uri_params))

        return self._generate_action_handler_base(action_name, _render_element,
                                                  destructive=destructive,
                                                  action_args=action_args)

    def generate_action_handler_task(self, action_name, action_args=None):
        def _render_task(self, task):
            cherrypy.response.status = 202
            return kimchi.template.render('Task', task)

        return self._generate_action_handler_base(action_name, _render_task,
                                                  action_args=action_args)

    def _generate_action_handler_base(self, action_name, render_fn,
                                      destructive=False, action_args=None):
        def wrapper(*args, **kwargs):
            validate_method(('POST'), self.role_key, self.admin_methods)
            try:
                self.lookup()
                if not self.is_authorized():
                    raise UnauthorizedError('KCHAPI0009E')

                model_args = list(self.model_args)
                if action_args is not None:
                    request = parse_request()
                    model_args.extend(request[key] for key in action_args)

                action_fn = getattr(self.model, model_fn(self, action_name))
                action_result = action_fn(*model_args)
                if destructive is False or \
                    ('persistent' in self.info.keys() and
                     self.info['persistent'] is True):
                    return render_fn(self, action_result)
            except MissingParameter, e:
                raise cherrypy.HTTPError(400, e.message)
            except InvalidParameter, e:
                raise cherrypy.HTTPError(400, e.message)
            except InvalidOperation, e:
                raise cherrypy.HTTPError(400, e.message)
            except UnauthorizedError, e:
                raise cherrypy.HTTPError(403, e.message)
            except NotFoundError, e:
                raise cherrypy.HTTPError(404, e.message)
            except OperationFailed, e:
                raise cherrypy.HTTPError(500, e.message)
            except KimchiException, e:
                raise cherrypy.HTTPError(500, e.message)

        wrapper.__name__ = action_name
        wrapper.exposed = True
        return wrapper

    def lookup(self):
        try:
            lookup = getattr(self.model, model_fn(self, 'lookup'))
            self.info = lookup(*self.model_args)
        except AttributeError:
            self.info = {}

    def delete(self):
        try:
            fn = getattr(self.model, model_fn(self, 'delete'))
            fn(*self.model_args)
            cherrypy.response.status = 204
        except AttributeError:
            e = InvalidOperation('KCHAPI0002E', {'resource':
                                                 get_class_name(self)})
            raise cherrypy.HTTPError(405, e.message)
        except OperationFailed, e:
            raise cherrypy.HTTPError(500, e.message)
        except InvalidOperation, e:
            raise cherrypy.HTTPError(400, e.message)

    @cherrypy.expose
    def index(self, *args, **kargs):
        method = validate_method(('GET', 'DELETE', 'PUT'),
                                 self.role_key, self.admin_methods)

        try:
            self.lookup()
            if not self.is_authorized():
                raise UnauthorizedError('KCHAPI0009E')

            return {'GET': self.get,
                    'DELETE': self.delete,
                    'PUT': self.update}[method](*args, **kargs)
        except InvalidOperation, e:
            raise cherrypy.HTTPError(400, e.message)
        except InvalidParameter, e:
            raise cherrypy.HTTPError(400, e.message)
        except UnauthorizedError, e:
            raise cherrypy.HTTPError(403, e.message)
        except NotFoundError, e:
            raise cherrypy.HTTPError(404, e.message)
        except OperationFailed, e:
            raise cherrypy.HTTPError(500, e.message)
        except KimchiException, e:
            raise cherrypy.HTTPError(500, e.message)

    def is_authorized(self):
        user_name = cherrypy.session.get(USER_NAME, '')
        user_groups = cherrypy.session.get(USER_GROUPS, [])
        user_role = cherrypy.session.get(USER_ROLES, {}).get(self.role_key)

        users = self.data.get("users", None)
        groups = self.data.get("groups", None)

        if (users is None and groups is None) or user_role == 'admin':
            return True

        return user_name in users or len(set(user_groups) & set(groups)) > 0

    def update(self, *args, **kargs):
        try:
            update = getattr(self.model, model_fn(self, 'update'))
        except AttributeError:
            e = InvalidOperation('KCHAPI0003E', {'resource':
                                                 get_class_name(self)})
            raise cherrypy.HTTPError(405, e.message)

        params = parse_request()
        validate_params(params, self, 'update')

        args = list(self.model_args) + [params]
        ident = update(*args)
        self._redirect(ident)

        return self.get()

    def get(self):
        self.lookup()
        return kimchi.template.render(get_class_name(self), self.data)

    @property
    def data(self):
        """
        Override this in inherited classes to provide the Resource
        representation as a python dictionary.
        """
        return {}


class Collection(object):
    """
    A Collection is a container for Resource objects.  To create a new
    Collection type, subclass this and make the following changes to the child
    class:

    - Set self.resource to the type of Resource that this Collection contains

    - Set self.resource_args.  This can remain an empty list if the Resources
      can be initialized with only one identifier.  Otherwise, include
      additional values as needed (eg. to identify a parent resource).

    - Set self.model_args.  Similar to above, this is needed only if the model
      needs additional information to identify this Collection.

    - Implement the base operations of 'create' and 'get_list' in the model.
    """
    def __init__(self, model):
        self.model = model
        self.resource = Resource
        self.resource_args = []
        self.model_args = []
        self.role_key = None
        self.admin_methods = []

    def create(self, params, *args):
        try:
            create = getattr(self.model, model_fn(self, 'create'))
        except AttributeError:
            e = InvalidOperation('KCHAPI0005E', {'resource':
                                                 get_class_name(self)})
            raise cherrypy.HTTPError(405, e.message)

        validate_params(params, self, 'create')
        args = self.model_args + [params]
        name = create(*args)
        cherrypy.response.status = 201
        args = self.resource_args + [name]
        res = self.resource(self.model, *args)

        return res.get()

    def _get_resources(self, flag_filter):
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            idents = get_list(*self.model_args, **flag_filter)
            res_list = []
            for ident in idents:
                # internal text, get_list changes ident to unicode for sorted
                args = self.resource_args + [ident]
                res = self.resource(self.model, *args)
                res.lookup()
                res_list.append(res)
            return res_list
        except AttributeError:
            return []

    def _cp_dispatch(self, vpath):
        if vpath:
            ident = vpath.pop(0)
            ident = urllib2.unquote(ident)
            # incoming text, from URL, is not unicode, need decode
            args = self.resource_args + [ident.decode("utf-8")]
            return self.resource(self.model, *args)

    def filter_data(self, resources, fields_filter):
        data = []
        for res in resources:
            if not res.is_authorized():
                continue

            if all(key in res.data and
                   (res.data[key] == val or res.data[key] in val or
                    re.match(str(val), res.data[key]))
                   for key, val in fields_filter.iteritems()):
                data.append(res.data)
        return data

    def get(self, filter_params):
        def _split_filter(params):
            flag_filter = dict()
            fields_filter = params
            for key, val in params.items():
                if key.startswith('_'):
                    flag_filter[key] = fields_filter.pop(key)
            return flag_filter, fields_filter

        flag_filter, fields_filter = _split_filter(filter_params)
        resources = self._get_resources(flag_filter)
        data = self.filter_data(resources, fields_filter)
        return kimchi.template.render(get_class_name(self), data)

    @cherrypy.expose
    def index(self, *args, **kwargs):
        method = validate_method(('GET', 'POST'),
                                 self.role_key, self.admin_methods)

        try:
            if method == 'GET':
                filter_params = cherrypy.request.params
                validate_params(filter_params, self, 'get_list')
                return self.get(filter_params)
            elif method == 'POST':
                return self.create(parse_request(), *args)
        except InvalidOperation, e:
            raise cherrypy.HTTPError(400, e.message)
        except InvalidParameter, e:
            raise cherrypy.HTTPError(400, e.message)
        except MissingParameter, e:
            raise cherrypy.HTTPError(400, e.message)
        except NotFoundError, e:
            raise cherrypy.HTTPError(404, e.message)
        except OperationFailed, e:
            raise cherrypy.HTTPError(500, e.message)
        except KimchiException, e:
            raise cherrypy.HTTPError(500, e.message)


class AsyncCollection(Collection):
    """
    A Collection to create it's resource by asynchronous task
    """
    def __init__(self, model):
        super(AsyncCollection, self).__init__(model)

    def create(self, params, *args):
        try:
            create = getattr(self.model, model_fn(self, 'create'))
        except AttributeError:
            e = InvalidOperation('KCHAPI0005E', {'resource':
                                                 get_class_name(self)})
            raise cherrypy.HTTPError(405, e.message)

        validate_params(params, self, 'create')
        args = self.model_args + [params]
        task = create(*args)
        cherrypy.response.status = 202
        return kimchi.template.render("Task", task)


class SimpleCollection(Collection):
    """
    A Collection without Resource definition
    """
    def __init__(self, model):
        super(SimpleCollection, self).__init__(model)

    def get(self, filter_params):
        res_list = []
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            res_list = get_list(*self.model_args)
        except AttributeError:
            pass
        return kimchi.template.render(get_class_name(self), res_list)
