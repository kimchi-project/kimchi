#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

import threading
import time

import cherrypy
import libvirt

from kimchi.utils import kimchi_log


class LibvirtConnection(object):
    def __init__(self, uri):
        self.uri = uri
        self._connections = {}
        self._connectionLock = threading.Lock()
        self.wrappables = self.get_wrappable_objects()

    def get_wrappable_objects(self):
        """
        When a wrapped function returns an instance of another libvirt object,
        we also want to wrap that object so we can catch errors that happen
        when calling its methods.
        """
        objs = []
        for name in ('virDomain', 'virDomainSnapshot', 'virInterface',
                     'virNWFilter', 'virNetwork', 'virNodeDevice', 'virSecret',
                     'virStoragePool', 'virStorageVol', 'virStream'):
            try:
                attr = getattr(libvirt, name)
            except AttributeError:
                pass
            objs.append(attr)
        return tuple(objs)

    def get(self, conn_id=0):
        """
        Return current connection to libvirt or open a new one.  Wrap all
        callable libvirt methods so we can catch connection errors and handle
        them by restarting the server.
        """
        def wrapMethod(f):
            def wrapper(*args, **kwargs):
                try:
                    ret = f(*args, **kwargs)
                    return ret
                except libvirt.libvirtError as e:
                    edom = e.get_error_domain()
                    ecode = e.get_error_code()
                    EDOMAINS = (libvirt.VIR_FROM_REMOTE,
                                libvirt.VIR_FROM_RPC)
                    ECODES = (libvirt.VIR_ERR_SYSTEM_ERROR,
                              libvirt.VIR_ERR_INTERNAL_ERROR,
                              libvirt.VIR_ERR_NO_CONNECT,
                              libvirt.VIR_ERR_INVALID_CONN)
                    if edom in EDOMAINS and ecode in ECODES:
                        kimchi_log.error('Connection to libvirt broken. '
                                         'Recycling. ecode: %d edom: %d' %
                                         (ecode, edom))
                        with self._connectionLock:
                            self._connections[conn_id] = None
                    raise
            wrapper.__name__ = f.__name__
            wrapper.__doc__ = f.__doc__
            return wrapper

        with self._connectionLock:
            conn = self._connections.get(conn_id)
            if not conn:
                retries = 5
                while True:
                    retries = retries - 1
                    try:
                        conn = libvirt.open(self.uri)
                        break
                    except libvirt.libvirtError:
                        kimchi_log.error('Unable to connect to libvirt.')
                        if not retries:
                            err = 'Libvirt is not available, exiting.'
                            kimchi_log.error(err)
                            cherrypy.engine.stop()
                            raise
                    time.sleep(2)

                for name in dir(libvirt.virConnect):
                    method = getattr(conn, name)
                    if callable(method) and not name.startswith('_'):
                        setattr(conn, name, wrapMethod(method))

                for cls in self.wrappables:
                    for name in dir(cls):
                        method = getattr(cls, name)
                        if callable(method) and not name.startswith('_'):
                            setattr(cls, name, wrapMethod(method))

                self._connections[conn_id] = conn
                # In case we're running into troubles with keeping the
                # connections alive we should place here:
                # conn.setKeepAlive(interval=5, count=3)
                # However the values need to be considered wisely to not affect
                # hosts which are hosting a lot of virtual machines
            return conn
