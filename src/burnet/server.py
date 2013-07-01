#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
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
#

from optparse import OptionParser
from root import Root

import logging.handlers
import logging
import model
import mockmodel
import config
import cherrypy

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
    CONFIG = {
        '/': { 'tools.trailing_slash.on': False,
               'tools.staticdir.root': config.get_prefix(),
               'request.methods_with_bodies': ('POST', 'PUT'),
               'tools.nocache.on': True },
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'ui/css',
            'tools.nocache.on': False },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'ui/js',
            'tools.nocache.on': False },
        '/libs': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'ui/libs',
            'tools.nocache.on': False },
        '/images': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'ui/images',
            'tools.nocache.on': False },
        '/data/screenshots': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'data/screenshots',
            'tools.nocache.on': False },
        }

    def __init__(self, options):
        cherrypy.tools.nocache = cherrypy.Tool('on_end_resource', set_no_cache)
        cherrypy.server.socket_host = options.host
        cherrypy.server.socket_port = options.port
        cherrypy.log.screen = True
        cherrypy.log.access_file = options.access_log
        cherrypy.log.error_file = options.error_log

        logLevel = LOGGING_LEVEL.get(options.log_level, logging.DEBUG)

        # Create handler to rotate access log file
        h = logging.handlers.RotatingFileHandler(options.access_log, 'a', 10000000, 1000)
        h.setLevel(logLevel)
        h.setFormatter(cherrypy._cplogging.logfmt)

        # Add access log file to cherrypy configuration
        cherrypy.log.access_log.addHandler(h)

        # Create handler to rotate error log file
        h = logging.handlers.RotatingFileHandler(options.error_log, 'a', 10000000, 1000)
        h.setLevel(logLevel)
        h.setFormatter(cherrypy._cplogging.logfmt)

        # Add rotating log file to cherrypy configuration
        cherrypy.log.error_log.addHandler(h)

        if hasattr(options, 'model'):
            model_instance = options.model
        elif options.test:
            model_instance = mockmodel.get_mock_environment()
        else:
            model_instance = model.Model()

        self.app = cherrypy.tree.mount(Root(model_instance), config=self.CONFIG)

    def start(self):
        cherrypy.quickstart(self.app)

    def stop(self):
        cherrypy.engine.exit()

def main(options):
    srv = Server(options)
    srv.start()

