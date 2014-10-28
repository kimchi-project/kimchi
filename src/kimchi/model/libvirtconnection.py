#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
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
    _connections = {}
    _connectionLock = threading.Lock()

    def __init__(self, uri):
        self.uri = uri
        if self.uri not in LibvirtConnection._connections:
            LibvirtConnection._connections[self.uri] = {}
        self._connections = LibvirtConnection._connections[self.uri]
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
                        with LibvirtConnection._connectionLock:
                            self._connections[conn_id] = None
                    raise
            wrapper.__name__ = f.__name__
            wrapper.__doc__ = f.__doc__
            return wrapper

        with LibvirtConnection._connectionLock:
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
                            kimchi_log.error("Unable to establish connection "
                                             "with libvirt. Please check "
                                             "your libvirt URI which is often "
                                             "defined in "
                                             "/etc/libvirt/libvirt.conf")
                            cherrypy.engine.stop()
                            exit(1)
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

    def isQemuURI(self):
        """
        This method will return True or Value when the system libvirt
        URI is a qemu based URI.  For example:
        qemu:///system or qemu+tcp://someipaddress/system
        """
        if self.get().getURI().startswith('qemu'):
            return True
        else:
            return False
