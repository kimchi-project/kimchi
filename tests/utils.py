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

import httplib
import cherrypy
import threading
import time
import socket
from contextlib import closing

import burnet.server

def get_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with closing(sock):
        try:
            sock.bind(("0.0.0.0", 0))
        except:
            raise Exception("Could not find a free port")
        return sock.getsockname()[1]

def run_server(host, port):
    args = type('_', (object,), {'host': host, 'port': port})()
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

def request(host, port, path, data=None, method='GET', headers=None):
    if headers is None:
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}

    conn = httplib.HTTPConnection(host, port)
    conn.request(method, path, data, headers)
    return conn.getresponse()
