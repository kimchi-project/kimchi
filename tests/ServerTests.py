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

import utils

utils.silence_server()

class ServerTests(unittest.TestCase):
    def test_server_start(self):
        """
        Test that we can start a server and receive a response.  Right now we
        have no content so we expect HTTP:404
        """
        try:
            host = '127.0.0.1'
            port = utils.get_free_port()
            s = utils.run_server(host, port)
            resp = utils.request(host, port, '/')
            self.assertEquals(200, resp.status)
        finally:
            s.stop()


