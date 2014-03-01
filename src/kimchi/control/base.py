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
import urllib2


import kimchi.template
from kimchi.control.utils import get_class_name, internal_redirect, model_fn
from kimchi.control.utils import parse_request, validate_method
from kimchi.control.utils import validate_params
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import MissingParameter, NotFoundError,  OperationFailed


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
        self.update_params = []

    def _redirect(self, ident, code=303):
        if ident is not None and ident != self.ident:
            uri_params = list(self.model_args[:-1])
            uri_params += [urllib2.quote(ident.encode('utf-8'), safe="")]
            raise cherrypy.HTTPRedirect(self.uri_fmt % tuple(uri_params), code)

    def generate_action_handler(self, action_name, action_args=None):
        def wrapper(*args, **kwargs):
            validate_method(('POST'))
            try:
                model_args = list(self.model_args)
                if action_args is not None:
                    request = parse_request()
                    model_args.extend(request[key] for key in action_args)
                fn = getattr(self.model, model_fn(self, action_name))
                ident = fn(*model_args)
                self._redirect(ident)
                uri_params = []
                for arg in self.model_args:
                    if arg is None:
                        arg = ''
                    uri_params.append(urllib2.quote(arg.encode('utf-8'),
                                      safe=""))
                raise internal_redirect(self.uri_fmt % tuple(uri_params))
            except MissingParameter, e:
                raise cherrypy.HTTPError(400, e.message)
            except InvalidParameter, e:
                raise cherrypy.HTTPError(400, e.message)
            except InvalidOperation, e:
                raise cherrypy.HTTPError(400, e.message)
            except OperationFailed, e:
                raise cherrypy.HTTPError(500, e.message)
            except NotFoundError, e:
                raise cherrypy.HTTPError(404, e.message)

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
    def index(self):
        method = validate_method(('GET', 'DELETE', 'PUT'))
        if method == 'GET':
            try:
                return self.get()
            except NotFoundError, e:
                raise cherrypy.HTTPError(404, e.message)
            except InvalidOperation, e:
                raise cherrypy.HTTPError(400, e.message)
            except OperationFailed, e:
                raise cherrypy.HTTPError(406, e.message)
        elif method == 'DELETE':
            try:
                return self.delete()
            except NotFoundError, e:
                raise cherrypy.HTTPError(404, e.message)
        elif method == 'PUT':
            try:
                return self.update()
            except InvalidParameter, e:
                raise cherrypy.HTTPError(400, e.message)
            except InvalidOperation, e:
                raise cherrypy.HTTPError(400, e.message)
            except NotFoundError, e:
                raise cherrypy.HTTPError(404, e.message)

    def update(self):
        try:
            update = getattr(self.model, model_fn(self, 'update'))
        except AttributeError:
            e = InvalidOperation('KCHAPI0003E', {'resource':
                                                 get_class_name(self)})
            raise cherrypy.HTTPError(405, e.message)

        params = parse_request()
        validate_params(params, self, 'update')

        if self.update_params is not None:
            invalids = [v for v in params.keys() if
                        v not in self.update_params]
            if invalids:
                msg_args = {'params': ", ".join(invalids),
                            'resource': get_class_name(self)}
                e = InvalidOperation('KCHAPI0004E', msg_args)
                raise cherrypy.HTTPError(405, e.message)

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
            if all(key in res.data and res.data[key] == val
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
        method = validate_method(('GET', 'POST'))
        if method == 'GET':
            try:
                filter_params = cherrypy.request.params
                validate_params(filter_params, self, 'get_list')
                return self.get(filter_params)
            except InvalidOperation, e:
                raise cherrypy.HTTPError(400, e.message)
            except NotFoundError, e:
                raise cherrypy.HTTPError(404, e.message)

        elif method == 'POST':
            try:
                return self.create(parse_request(), *args)
            except MissingParameter, e:
                raise cherrypy.HTTPError(400, e.message)
            except InvalidParameter, e:
                raise cherrypy.HTTPError(400, e.message)
            except OperationFailed, e:
                raise cherrypy.HTTPError(500, e.message)
            except InvalidOperation, e:
                raise cherrypy.HTTPError(400, e.message)
            except NotFoundError, e:
                raise cherrypy.HTTPError(404, e.message)


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
