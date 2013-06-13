#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
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
#

import httplib
import cherrypy
import threading
import time
import os
import sys
import socket
from contextlib import closing

import burnet.server

_port = None

def get_free_port():
    global _port
    if _port is not None:
        return _port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with closing(sock):
        try:
            sock.bind(("0.0.0.0", 0))
        except:
            raise Exception("Could not find a free port")
        _port = sock.getsockname()[1]
        return _port

def run_server(host, port, test_mode, model=None):
    args = type('_', (object,),
                {'host': host, 'port': port, 'test': test_mode,
                 'logfile': '/dev/null'})()
    if model is not None:
        setattr(args, 'model', model)
    s = burnet.server.Server(args)
    t = threading.Thread(target=s.start)
    t.setDaemon(True)
    t.start()
    cherrypy.engine.wait(cherrypy.engine.states.STARTED)
    return s

def silence_server():
    """
    Silence server status messages on stdout
    """
    cherrypy.config.update({"environment": "embedded"})

def running_as_root():
    return os.geteuid() == 0

def request(host, port, path, data=None, method='GET', headers=None):
    if headers is None:
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}

    conn = httplib.HTTPConnection(host, port)
    conn.request(method, path, data, headers)
    return conn.getresponse()


class RollbackContext(object):
    '''
    A context manager for recording and playing rollback.
    The first exception will be remembered and re-raised after rollback

    Sample usage:
    with RollbackContext() as rollback:
        step1()
        rollback.prependDefer(lambda: undo step1)
        def undoStep2(arg): pass
        step2()
        rollback.prependDefer(undoStep2, arg)
    '''
    def __init__(self, *args):
        self._finally = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        firstException = exc_value

        for undo, args, kwargs in self._finally:
            try:
                undo(*args, **kwargs)
            except Exception as e:
                # keep the earliest exception info
                if not firstException:
                    firstException = e
                    # keep the original traceback info
                    traceback = sys.exc_info()[2]

        # re-raise the earliest exception
        if firstException is not None:
            raise firstException, None, traceback

    def defer(self, func, *args, **kwargs):
        self._finally.append((func, args, kwargs))

    def prependDefer(self, func, *args, **kwargs):
        self._finally.insert(0, (func, args, kwargs))
