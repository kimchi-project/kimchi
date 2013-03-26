#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.

import unittest
import json

import utils

#utils.silence_server()

class ServerTests(unittest.TestCase):
    def test_server_start(self):
        """
        Test that we can start a server and receive a response.  Right now we
        have no content so we expect HTTP:404
        """
        host = '127.0.0.1'
        port = utils.get_free_port()
        s = utils.run_server(host, port, test_mode=True)
        try:
            resp = utils.request(host, port, '/')
            data = json.loads(resp.read())
            self.assertEquals(200, resp.status)
            self.assertEquals('localhost', data['hostname'])
        except:
            raise
        finally:
            s.stop()


