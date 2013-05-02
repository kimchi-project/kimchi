#!/usr/bin/python
#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.

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
    args = [cmd, str(src_port), '--timeout', '10',
            '--idle-timeout', '10', 'localhost:%s' % target_port]
    p = subprocess.Popen(args, close_fds=True)

    return src_port
