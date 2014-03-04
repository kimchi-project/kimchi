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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#

import cherrypy
import logging
import logging.handlers
import os
import sslcert

from kimchi import auth
from kimchi import config
from kimchi.model import model
from kimchi import mockmodel
from kimchi import vnc
from kimchi.config import paths, KimchiConfig, PluginConfig
from kimchi.control import sub_nodes
from kimchi.root import KimchiRoot
from kimchi.utils import get_enabled_plugins, import_class


LOGGING_LEVEL = {"debug": logging.DEBUG,
                 "info": logging.INFO,
                 "warning": logging.WARNING,
                 "error": logging.ERROR,
                 "critical": logging.CRITICAL}


def set_no_cache():
    from time import strftime, gmtime
    h = [('Expires', 'Mon, 26 Jul 1997 05:00:00 GMT'),
         ('Cache-Control',
          'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'),
         ('Pragma', 'no-cache'),
         ('Last-Modified', strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime()))]
    hList = cherrypy.response.header_list
    if isinstance(hList, list):
        hList.extend(h)
    else:
        hList = h


class Server(object):
    def __init__(self, options):
        make_dirs = [
            os.path.dirname(os.path.abspath(options.access_log)),
            os.path.dirname(os.path.abspath(options.error_log)),
            os.path.dirname(os.path.abspath(config.get_object_store())),
            os.path.abspath(config.get_screenshot_path()),
            os.path.abspath(config.get_debugreports_path()),
            os.path.abspath(config.get_distros_store())
        ]
        for directory in make_dirs:
            if not os.path.isdir(directory):
                os.makedirs(directory)

        self.configObj = KimchiConfig()
        cherrypy.tools.nocache = cherrypy.Tool('on_end_resource', set_no_cache)
        cherrypy.tools.kimchiauth = cherrypy.Tool('before_handler',
                                                  auth.kimchiauth)
        cherrypy.server.socket_host = options.host
        cherrypy.server.socket_port = options.port

        # SSL Server
        try:
            if options.ssl_port and options.ssl_port > 0:
                self._init_ssl(options)
        except AttributeError:
            pass

        cherrypy.log.screen = True
        cherrypy.log.access_file = options.access_log
        cherrypy.log.error_file = options.error_log

        logLevel = LOGGING_LEVEL.get(options.log_level, logging.DEBUG)
        dev_env = options.environment != 'production'

        # Create handler to rotate access log file
        h = logging.handlers.RotatingFileHandler(options.access_log, 'a',
                                                 10000000, 1000)
        h.setLevel(logLevel)
        h.setFormatter(cherrypy._cplogging.logfmt)

        # Add access log file to cherrypy configuration
        cherrypy.log.access_log.addHandler(h)

        # Create handler to rotate error log file
        h = logging.handlers.RotatingFileHandler(options.error_log, 'a',
                                                 10000000, 1000)
        h.setLevel(logLevel)
        h.setFormatter(cherrypy._cplogging.logfmt)

        # Add rotating log file to cherrypy configuration
        cherrypy.log.error_log.addHandler(h)

        # Handling running mode
        if not dev_env:
            cherrypy.config.update({'environment': 'production'})

        if hasattr(options, 'model'):
            model_instance = options.model
        elif options.test:
            model_instance = mockmodel.get_mock_environment()
        else:
            model_instance = model.Model()

        if isinstance(model_instance, model.Model):
            vnc_ws_proxy = vnc.new_ws_proxy()
            cherrypy.engine.subscribe('exit', vnc_ws_proxy.kill)

        for ident, node in sub_nodes.items():
            if node.url_auth:
                cfg = self.configObj
                ident = "/%s" % ident
                cfg[ident] = {'tools.kimchiauth.on': True}
                if node.admin_methods:
                    cfg[ident][
                        'tools.kimchiauth.admin_methods'] = node.admin_methods

        self.app = cherrypy.tree.mount(KimchiRoot(model_instance, dev_env),
                                       config=self.configObj)
        self._load_plugins()

        cherrypy.lib.sessions.init()

    def _load_plugins(self):
        for plugin_name, plugin_config in get_enabled_plugins():
            try:
                plugin_class = ('plugins.%s.%s' %
                                (plugin_name,
                                 plugin_config['kimchi']['plugin_class']))
                script_name = plugin_config['kimchi']['uri']
                del plugin_config['kimchi']

                plugin_config.update(PluginConfig(plugin_name))
            except KeyError:
                continue

            try:
                plugin_app = import_class(plugin_class)()
            except ImportError:
                cherrypy.log.error_log.error("Failed to import plugin %s" %
                                             plugin_class)
                continue
            cherrypy.tree.mount(plugin_app, script_name, plugin_config)

    def _init_ssl(self, options):
        ssl_server = cherrypy._cpserver.Server()
        ssl_server.socket_port = options.ssl_port
        ssl_server._socket_host = options.host
        ssl_server.ssl_module = 'builtin'

        cert = options.ssl_cert
        key = options.ssl_key
        if not cert or not key:
            config_dir = paths.conf_dir
            cert = '%s/kimchi-cert.pem' % config_dir
            key = '%s/kimchi-key.pem' % config_dir

            if not os.path.exists(cert) or not os.path.exists(key):
                ssl_gen = sslcert.SSLCert()
                with open(cert, "w") as f:
                    f.write(ssl_gen.cert_pem())
                with open(key, "w") as f:
                    f.write(ssl_gen.key_pem())

        ssl_server.ssl_certificate = cert
        ssl_server.ssl_private_key = key
        ssl_server.subscribe()

    def start(self):
        cherrypy.engine.start()
        cherrypy.engine.block()

    def stop(self):
        cherrypy.engine.exit()


def main(options):
    srv = Server(options)
    srv.start()
