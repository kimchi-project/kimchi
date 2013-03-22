#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.
#

from argparse import ArgumentParser
from root import Root
import cherrypy

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
               'request.methods_with_bodies': ('POST', 'PUT'),
               'tools.nocache.on': True },
        }

    def __init__(self, args):
        cherrypy.tools.nocache = cherrypy.Tool('on_end_resource', set_no_cache)
        cherrypy.server.socket_host = args.host
        cherrypy.server.socket_port = args.port
        self.app = cherrypy.tree.mount(Root(), config=self.CONFIG)

    def start(self):
        cherrypy.quickstart(self.app)

    def stop(self):
        cherrypy.engine.exit()

def main(args):
    parser = ArgumentParser()
    parser.add_argument('--host', type=str, default="localhost",
                        help="Hostname to listen on")
    parser.add_argument('--port', type=int, default=8000,
                        help="Port to listen on")

    args = parser.parse_args(args)
    srv = Server(args)
    srv.start()

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
