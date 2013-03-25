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

import unittest
import json

import burnet.mockmodel
import burnet.server
from utils import *

test_server = None
model = None
host = None
port = None

#utils.silence_server()

def setUpModule():
    global test_server, model, host, port

    model = burnet.mockmodel.MockModel()
    host = '127.0.0.1'
    port = get_free_port()
    test_server = run_server(host, port, test_mode=True, model=model)


def tearDownModule():
    test_server.stop()


class RestTests(unittest.TestCase):
    def setUp(self):
        model.reset()

    def assertHTTPStatus(self, code, *args):
        resp = request(*args)
        self.assertEquals(code, resp.status)

    def assertValidJSON(self, txt):
        try:
            json.loads(txt)
        except ValueError:
            self.fail("Invalid JSON: %s" % txt)

    def test_404(self):
        """
        A non-existent path should return HTTP:404
        """
        url_list = ['/doesnotexist']
        for url in url_list:
            self.assertHTTPStatus(404, host, port, url)

    def test_wrong_method(self):
        """
        Using the wrong HTTP method should return HTTP:405
        """
        self.assertHTTPStatus(405, host, port, "/", None, 'DELETE')

    def test_accepts(self):
        """
        Verify the following expectations regarding the client Accept header:
          If omitted, default to html
          If 'application/json', serve the rest api
          If 'text/html', serve the UI
          If both of the above (in any order), serve the rest api
          If neither of the above, HTTP:406
        """
        resp = request(host, port, "/", headers={})
        self.assertTrue('<!doctype html>' in resp.read().lower())

        resp = request(host, port, "/", headers={'Accept': 'application/json'})
        self.assertValidJSON(resp.read())

        resp = request(host, port, "/", headers={'Accept': 'text/html'})
        self.assertTrue('<!doctype html>' in resp.read().lower())

        resp = request(host, port, "/",
                       headers={'Accept': 'application/json, text/html'})
        self.assertValidJSON(resp.read())

        resp = request(host, port, "/",
                       headers={'Accept': 'text/html, application/json'})
        self.assertValidJSON(resp.read())

        h = {'Accept': 'text/plain'}
        self.assertHTTPStatus(406, host, port, "/", None, 'GET', h)
