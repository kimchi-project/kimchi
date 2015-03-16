#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
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

import cherrypy
import re
import socket

from kimchi.config import config
from kimchi.utils import kimchi_log, run_command


class PeersModel(object):
    def __init__(self, **kargs):
        # check federation feature is enabled on Kimchi server
        if config.get("server", "federation") == "off":
            return

        # register server on openslp
        hostname = socket.getfqdn(config.get("server", "host"))
        port = config.get("server", "ssl_port")
        self.url = hostname + ":" + port

        cmd = ["slptool", "register",
               "service:kimchid://%s" % self.url]
        out, error, ret = run_command(cmd)
        if out and len(out) != 0:
            kimchi_log.error("Unable to register server on openSLP."
                             " Details: %s" % out)
        cherrypy.engine.subscribe('exit', self._peer_deregister)

    def _peer_deregister(self):
        cmd = ["slptool", "deregister",
               "service:kimchid://%s" % self.url]
        out, error, ret = run_command(cmd)
        if out and len(out) != 0:
            kimchi_log.error("Unable to deregister server on openSLP."
                             " Details: %s" % out)

    def get_list(self):
        # check federation feature is enabled on Kimchi server
        if config.get("server", "federation") == "off":
            return []

        cmd = ["slptool", "findsrvs", "service:kimchid"]
        out, error, ret = run_command(cmd)
        if ret != 0:
            return []

        peers = []
        for server in out.strip().split("\n"):
            match = re.match("service:kimchid://(.*?),.*", server)
            peer = match.group(1)
            if peer != self.url:
                peers.append("https://" + peer)

        return peers
