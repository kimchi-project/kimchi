#!/usr/bin/python
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

import os
import socket
import subprocess
import sys

from contextlib import closing

def _getFreePort():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with closing(sock):
        try:
            sock.bind(("0.0.0.0", 0))
        except:
            raise Exception("Could not find a free port")

        return sock.getsockname()[1]

def new_ws_proxy(target_port):
    src_port = _getFreePort()
    cmd = os.path.join(os.path.dirname(__file__), 'websockify.py')
    args = ['python', cmd, str(src_port), '--timeout', '10',
            '--idle-timeout', '10', 'localhost:%s' % target_port]
    p = subprocess.Popen(args, close_fds=True)

    return src_port
