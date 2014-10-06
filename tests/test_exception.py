#
# Kimchi
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

import json
import os
import unittest


import kimchi.mockmodel
import kimchi.server
from utils import get_free_port, patch_auth, request, run_server


test_server = None
model = None
host = None
port = None
ssl_port = None


def setup_server(environment='development'):
    global test_server, model, host, port, ssl_port

    patch_auth()
    model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    test_server = run_server(host, port, ssl_port, test_mode=True, model=model,
                             environment=environment)


class ExceptionTests(unittest.TestCase):
    def tearDown(self):
        test_server.stop()
        os.unlink('/tmp/obj-store-test')

    def test_production_env(self):
        """
        Test reasons sanitized in production env
        """
        setup_server('production')
        # test 404
        resp = json.loads(request(host, ssl_port, '/vms/blah').read())
        self.assertEquals('404 Not Found', resp.get('code'))

        # test 405 wrong method
        resp = json.loads(request(host, ssl_port, '/', None, 'DELETE').read())
        msg = u'KCHAPI0002E: Delete is not allowed for kimchiroot'
        self.assertEquals('405 Method Not Allowed', resp.get('code'))
        self.assertEquals(msg, resp.get('reason'))

        # test 400 parse error
        resp = json.loads(request(host, ssl_port, '/vms', '{', 'POST').read())
        msg = u'KCHAPI0006E: Unable to parse JSON request'
        self.assertEquals('400 Bad Request', resp.get('code'))
        self.assertEquals(msg, resp.get('reason'))
        self.assertNotIn('call_stack', resp)

        # test 400 missing required parameter
        req = json.dumps({})
        resp = json.loads(request(host, ssl_port, '/vms', req, 'POST').read())
        self.assertEquals('400 Bad Request', resp.get('code'))
        m = u"KCHVM0016E: Specify a template to create a virtual machine from"
        self.assertEquals(m, resp.get('reason'))
        self.assertNotIn('call_stack', resp)

    def test_development_env(self):
        """
        Test traceback thrown in development env
        """
        setup_server()
        # test 404
        resp = json.loads(request(host, ssl_port, '/vms/blah').read())
        self.assertEquals('404 Not Found', resp.get('code'))

        # test 405 wrong method
        resp = json.loads(request(host, ssl_port, '/', None, 'DELETE').read())
        msg = u'KCHAPI0002E: Delete is not allowed for kimchiroot'
        self.assertEquals('405 Method Not Allowed', resp.get('code'))
        self.assertEquals(msg, resp.get('reason'))

        # test 400 parse error
        resp = json.loads(request(host, ssl_port, '/vms', '{', 'POST').read())
        msg = u'KCHAPI0006E: Unable to parse JSON request'
        self.assertEquals('400 Bad Request', resp.get('code'))
        self.assertEquals(msg, resp.get('reason'))
        self.assertIn('call_stack', resp)

        # test 400 missing required parameter
        req = json.dumps({})
        resp = json.loads(request(host, ssl_port, '/vms', req, 'POST').read())
        m = u"KCHVM0016E: Specify a template to create a virtual machine from"
        self.assertEquals('400 Bad Request', resp.get('code'))
        self.assertEquals(m, resp.get('reason'))
        self.assertIn('call_stack', resp)
