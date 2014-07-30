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
#

import base64
import cherrypy
import httplib
import os
import socket
import sys
import threading
import unittest


from contextlib import closing
from lxml import etree


import kimchi.mockmodel
import kimchi.server
from kimchi.exception import OperationFailed

_ports = {}

# provide missing unittest decorators and API for python 2.6; these decorators
# do not actually work, just avoid the syntax failure
if sys.version_info[:2] == (2, 6):
    def skipUnless(condition, reason):
        if not condition:
            sys.stderr.write('[expected failure] ')
            raise Exception(reason)
        return lambda obj: obj

    unittest.skipUnless = skipUnless
    unittest.expectedFailure = lambda obj: obj

    def assertGreater(self, a, b, msg=None):
        if not a > b:
            self.fail('%s not greater than %s' % (repr(a), repr(b)))

    def assertGreaterEqual(self, a, b, msg=None):
        if not a >= b:
            self.fail('%s not greater than or equal to %s'
                      % (repr(a), repr(b)))

    def assertIsInstance(self, obj, cls, msg=None):
        if not isinstance(obj, cls):
            self.fail('%s is not an instance of %r' % (repr(obj), cls))

    def assertIn(self, a, b, msg=None):
        if a not in b:
            self.fail("%s is not in %b" % (repr(a), repr(b)))

    def assertNotIn(self, a, b, msg=None):
        if a in b:
            self.fail("%s is in %b" % (repr(a), repr(b)))

    unittest.TestCase.assertGreaterEqual = assertGreaterEqual
    unittest.TestCase.assertGreater = assertGreater
    unittest.TestCase.assertIsInstance = assertIsInstance
    unittest.TestCase.assertIn = assertIn
    unittest.TestCase.assertNotIn = assertNotIn


def get_free_port(name='http'):
    global _ports
    if _ports.get(name) is not None:
        return _ports[name]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with closing(sock):
        try:
            sock.bind(("0.0.0.0", 0))
        except:
            raise Exception("Could not find a free port")
        _ports[name] = sock.getsockname()[1]
        return _ports[name]


def run_server(host, port, ssl_port, test_mode, cherrypy_port=None,
               model=None, environment='development'):

    if cherrypy_port is None:
        cherrypy_port = get_free_port('cherrypy_port')

    if ssl_port is None:
        ssl_port = get_free_port('https')

    args = type('_', (object,),
                {'host': host, 'port': port, 'ssl_port': ssl_port,
                 'cherrypy_port': cherrypy_port,
                 'ssl_cert': '', 'ssl_key': '',
                 'test': test_mode, 'access_log': '/dev/null',
                 'error_log': '/dev/null', 'environment': environment,
                 'log_level': 'debug'})()
    if model is not None:
        setattr(args, 'model', model)

    s = kimchi.server.Server(args)
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


def _request(conn, path, data, method, headers):
    if headers is None:
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
    if 'AUTHORIZATION' not in headers.keys():
        user, pw = kimchi.mockmodel.fake_user.items()[0]
        hdr = "Basic " + base64.b64encode("%s:%s" % (user, pw))
        headers['AUTHORIZATION'] = hdr
    conn.request(method, path, data, headers)
    return conn.getresponse()


def request(host, port, path, data=None, method='GET', headers=None):
    conn = httplib.HTTPSConnection(host, port)
    return _request(conn, path, data, method, headers)


def patch_auth(sudo=True):
    """
    Override the authenticate function with a simple test against an
    internal dict of users and passwords.
    """

    def _get_groups(self):
        return ['groupA', 'groupB', 'wheel']

    def _has_sudo(self, result):
        result.value = sudo

    def _authenticate(username, password, service="passwd"):
        try:
            return kimchi.mockmodel.fake_user[username] == password
        except KeyError, e:
            raise OperationFailed("KCHAUTH0001E", {'username': 'username',
                                                   'code': e.message})

    import kimchi.auth
    kimchi.auth.authenticate = _authenticate
    kimchi.auth.User.get_groups = _get_groups
    kimchi.auth.User._has_sudo = _has_sudo


def normalize_xml(xml_str):
    return etree.tostring(etree.fromstring(xml_str,
                          etree.XMLParser(remove_blank_text=True)))
