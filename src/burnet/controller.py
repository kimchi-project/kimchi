#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.

import cherrypy
import json
from functools import wraps

import burnet.model
import burnet.template


def get_class_name(cls):
    try:
        sub_class = cls.__subclasses__()[0]
    except AttributeError:
        sub_class = cls.__class__.__name__
    return sub_class.lower()


def model_fn(cls, fn_name):
    return '%s_%s' % (get_class_name(cls), fn_name)


def validate_method(allowed):
    method = cherrypy.request.method.upper()
    if method not in allowed:
        raise cherrypy.HTTPError(405)
    return method


def mime_in_header(header, mime):
    if not header in cherrypy.request.headers:
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
    rawbody = cherrypy.request.body.read()

    if mime_in_header('Content-Type', 'application/json'):
        try:
            return json.loads(rawbody)
        except ValueError:
            raise cherrypy.HTTPError(400, "Unable to parse JSON request")
    else:
        raise cherrypy.HTTPError(415, "This API only supports"
                                      " 'application/json'")


def action(f):
    @wraps(f)
    @cherrypy.expose
    def wrapper(*args, **kwargs):
        validate_method(('POST'))
        try:
            f(*args, **kwargs)
        except burnet.model.MissingParameter, param:
            raise cherrypy.HTTPError(400, "Missing parameter: '%s'" % param)
        except burnet.model.InvalidParameter, param:
            raise cherrypy.HTTPError(400, "Invalid parameter: '%s'" % param)
        except burnet.model.InvalidOperation, msg:
            raise cherrypy.HTTPError(400, "Invalid operation: '%s'" % msg)
        except burnet.model.OperationFailed, msg:
            raise cherrypy.HTTPError(500, "Operation Failed: '%s'" % msg)
    return wrapper


class Resource(object):
    """
    A Resource represents a single entity in the API (such as a Virtual Machine)

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
            raise cherrypy.HTTPError(405)

    @cherrypy.expose
    def index(self):
        method = validate_method(('GET', 'DELETE'))
        if method == 'GET':
            try:
                return self.get()
            except burnet.model.NotFoundError:
                raise cherrypy.HTTPError(404)
        elif method == 'DELETE':
            return self.delete()

    def get(self):
        self.lookup()
        return burnet.template.render(get_class_name(self), self.data)

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

    def create(self, *args):
        try:
            create = getattr(self.model, model_fn(self, 'create'))
        except AttributeError:
            raise cherrypy.HTTPError(405)
        params = parse_request()
        args = self.model_args + [params]
        create(*args)
        cherrypy.response.status = 201
        args = self.resource_args + [params['name']]
        res = self.resource(self.model, *args)
        return res.get()

    def _get_resources(self):
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            idents = get_list(*self.model_args)
            res_list = []
            for ident in idents:
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
            args = self.resource_args + [ident]
            return self.resource(self.model, *args)

    def get(self):
        resources = self._get_resources()
        data = []
        for res in resources:
            data.append(res.data)
        return burnet.template.render(get_class_name(self), data)

    @cherrypy.expose
    def index(self, *args):
        method = validate_method(('GET', 'POST'))
        if method == 'GET':
            return self.get()
        elif method == 'POST':
            try:
                return self.create(*args)
            except burnet.model.MissingParameter, param:
                raise cherrypy.HTTPError(400, "Missing parameter: '%s'" % param)
            except burnet.model.InvalidParameter, param:
                raise cherrypy.HTTPError(400, "Invalid parameter: '%s'" % param)


class VMs(Collection):
    def __init__(self, model):
        super(VMs, self).__init__(model)
        self.resource = VM


class VM(Resource):
    def __init__(self, model, ident):
        super(VM, self).__init__(model, ident)

    @action
    def start(self):
        getattr(self.model, model_fn(self, 'start'))(self.ident)
        raise cherrypy.HTTPRedirect('/vms/%s' % self.ident, 303)

    @action
    def stop(self):
        getattr(self.model, model_fn(self, 'stop'))(self.ident)
        raise cherrypy.HTTPRedirect('/vms/%s' % self.ident, 303)

    @property
    def data(self):
        return {'name': self.ident,
                'memory': self.info['memory'],
                'state': self.info['state'],
                'screenshot': self.info['screenshot']}


class Templates(Collection):
    def __init__(self, model):
        super(Templates, self).__init__(model)
        self.resource = Template


class Template(Resource):
    def __init__(self, model, ident):
        super(Template, self).__init__(model, ident)

    @property
    def data(self):
        return {'name': self.ident,
                'icon': self.info['icon'],
                'os_distro': self.info['os_distro'],
                'os_version': self.info['os_version'],
                'cpus': self.info['cpus'],
                'memory': self.info['memory'],
                'cdrom': self.info['cdrom'],
                'disks': self.info['disks']}


class StorageVolume(Resource):
    def __init__(self, model, pool, ident):
        super(StorageVolume, self).__init__(model, ident)
        self.pool = pool
        self.ident = ident
        self.info = {}
        self.model_args = [self.pool, self.ident]

    @action
    def resize(self):
        params = parse_request()
        size = params['size']
        getattr(self.model, model_fn(self, 'resize'))(self.pool,
                                                      self.ident, size)
        raise cherrypy.HTTPRedirect('/storagepools/%s/storagevolumes/%s'
                                    % (self.pool, self.ident), 303)

    @action
    def wipe(self):
        getattr(self.model, model_fn(self, 'wipe'))(self.pool, self.ident)
        raise cherrypy.HTTPRedirect('/storagepools/%s/storagevolumes/%s'
                                    % (self.pool, self.ident), 303)

    @property
    def data(self):
        return {'name': self.ident,
                'type': self.info['type'],
                'capacity': self.info['capacity'],
                'allocation': self.info['allocation'],
                'format': self.info['format']}


class StorageVolumes(Collection):
    def __init__(self, model, pool):
        super(StorageVolumes, self).__init__(model)
        self.resource = StorageVolume
        self.pool = pool
        self.resource_args = [self.pool, ]
        self.model_args = [self.pool, ]


class StoragePool(Resource):
    def __init__(self, model, ident):
        super(StoragePool, self).__init__(model, ident)

    @action
    def activate(self):
        getattr(self.model, model_fn(self, 'activate'))(self.ident)
        raise cherrypy.HTTPRedirect('/storagepools/%s' % self.ident, 303)

    @action
    def deactivate(self):
        getattr(self.model, model_fn(self, 'deactivate'))(self.ident)
        raise cherrypy.HTTPRedirect('/storagepools/%s' % self.ident, 303)

    @property
    def data(self):
        return {'name': self.ident,
                'state': self.info['state'],
                'capacity': self.info['capacity'],
                'allocated': self.info['allocated'],
                'path': self.info['path'],
                'type': self.info['type']}

    def _cp_dispatch(self, vpath):
        if vpath:
            subcollection = vpath.pop(0)
            if subcollection == 'storagevolumes':
                return StorageVolumes(self.model, self.ident)


class StoragePools(Collection):
    def __init__(self, model):
        super(StoragePools, self).__init__(model)
        self.resource = StoragePool
