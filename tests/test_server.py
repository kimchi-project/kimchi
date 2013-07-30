#
# Project Kimchi
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

import unittest
import json
import os

import utils

import kimchi.mockmodel

#utils.silence_server()

class ServerTests(unittest.TestCase):
    def test_server_start(self):
        """
        Test that we can start a server and receive HTTP:200.
        """
        host = '127.0.0.1'
        port = utils.get_free_port()
        model = kimchi.mockmodel.MockModel('/tmp/obj-store-test')
        s = utils.run_server(host, port, test_mode=True, model=model)
        try:
            resp = utils.request(host, port, '/')
            self.assertEquals(200, resp.status)
        except:
            raise
        finally:
            os.unlink('/tmp/obj-store-test')
            s.stop()


