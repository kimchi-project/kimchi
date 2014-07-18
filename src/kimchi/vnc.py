#!/usr/bin/python
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import base64
import errno
import os
import subprocess


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

    cmd = os.path.join(os.path.dirname(__file__), 'websockify.py')
    args = ['python', cmd, config.get('display', 'display_proxy_port'),
            '--target-config', WS_TOKENS_DIR, '--cert', cert, '--key', key,
            '--web', os.path.join(paths.ui_dir, 'pages/websockify'),
            '--ssl-only']
    p = subprocess.Popen(args, close_fds=True)
    return p


def add_proxy_token(name, port):
    with open(os.path.join(WS_TOKENS_DIR, name), 'w') as f:
        name = base64.urlsafe_b64encode(name)
        f.write('%s: localhost:%s' % (name.encode('utf-8'), port))


def remove_proxy_token(name):
    try:
        os.unlink(os.path.join(WS_TOKENS_DIR, name))
    except OSError:
        pass
