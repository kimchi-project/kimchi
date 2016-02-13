#!/usr/bin/env python2
#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2016
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

from wok.config import config, paths, PluginPaths


try:
    from websockify.token_plugins import TokenFile
    tokenFile = True
except ImportError:
    tokenFile = False

try:
    from websockify import ProxyRequestHandler as request_proxy
except:
    from websockify import WebSocketProxy as request_proxy


WS_TOKENS_DIR = os.path.join(PluginPaths('kimchi').state_dir, 'ws-tokens')


class CustomHandler(request_proxy):

    def get_target(self, target_plugin, path):
        if issubclass(CustomHandler, object):
            target = super(CustomHandler, self).get_target(target_plugin,
                                                           path)
        else:
            target = request_proxy.get_target(self, target_plugin, path)

        if target[0] == 'unix_socket':
            try:
                self.server.unix_target = target[1]
            except:
                self.unix_target = target[1]
        else:
            try:
                self.server.unix_target = None
            except:
                self.unix_target = None
        return target


def new_ws_proxy():
    try:
        os.makedirs(WS_TOKENS_DIR, mode=0755)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass

    cert = config.get('server', 'ssl_cert')
    key = config.get('server', 'ssl_key')
    if not (cert and key):
        cert = '%s/wok-cert.pem' % paths.conf_dir
        key = '%s/wok-key.pem' % paths.conf_dir

    params = {'listen_host': '127.0.0.1',
              'listen_port': config.get('server', 'websockets_port'),
              'ssl_only': False}

    # old websockify: do not use TokenFile
    if not tokenFile:
        params['target_cfg'] = WS_TOKENS_DIR

    # websockify 0.7 and higher: use TokenFile
    else:
        params['token_plugin'] = TokenFile(src=WS_TOKENS_DIR)

    def start_proxy():
        try:
            server = WebSocketProxy(RequestHandlerClass=CustomHandler,
                                    **params)
        except TypeError:
            server = CustomHandler(**params)

        server.start_server()

    proc = Process(target=start_proxy)
    proc.start()
    return proc


def add_proxy_token(name, port, is_unix_socket=False):
    with open(os.path.join(WS_TOKENS_DIR, name), 'w') as f:
        """
        From python documentation base64.urlsafe_b64encode(s)
        substitutes - instead of + and _ instead of / in the
        standard Base64 alphabet, BUT the result can still
        contain = which is not safe in a URL query component.
        So remove it when needed as base64 can work well without it.
        """
        name = base64.urlsafe_b64encode(name).rstrip('=')
        if is_unix_socket:
            f.write('%s: unix_socket:%s' % (name.encode('utf-8'), port))
        else:
            f.write('%s: localhost:%s' % (name.encode('utf-8'), port))


def remove_proxy_token(name):
    try:
        os.unlink(os.path.join(WS_TOKENS_DIR, name))
    except OSError:
        pass
