#!/usr/bin/env python2
#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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

import base64
import errno
import os

from multiprocessing import Process
from websockify import WebSocketProxy

from kimchi.config import config, paths


WS_TOKENS_DIR = '/var/lib/kimchi/vnc-tokens'


def new_ws_proxy():
    try:
        os.makedirs(WS_TOKENS_DIR, mode=0755)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass

    cert = config.get('server', 'ssl_cert')
    key = config.get('server', 'ssl_key')
    if not (cert and key):
        cert = '%s/kimchi-cert.pem' % paths.conf_dir
        key = '%s/kimchi-key.pem' % paths.conf_dir

    params = {'web': os.path.join(paths.ui_dir, 'pages/websockify'),
              'listen_port': config.get('display', 'display_proxy_port'),
              'target_cfg': WS_TOKENS_DIR,
              'key': key, 'cert': cert, 'ssl_only': True}

    def start_proxy():
        server = WebSocketProxy(**params)
        server.start_server()

    proc = Process(target=start_proxy)
    proc.start()
    return proc


def add_proxy_token(name, port):
    with open(os.path.join(WS_TOKENS_DIR, name), 'w') as f:
        """
        From python documentation base64.urlsafe_b64encode(s)
        substitutes - instead of + and _ instead of / in the
        standard Base64 alphabet, BUT the result can still
        contain = which is not safe in a URL query component.
        So remove it when needed as base64 can work well without it.
        """
        name = base64.urlsafe_b64encode(name).rstrip('=')
        f.write('%s: localhost:%s' % (name.encode('utf-8'), port))


def remove_proxy_token(name):
    try:
        os.unlink(os.path.join(WS_TOKENS_DIR, name))
    except OSError:
        pass
