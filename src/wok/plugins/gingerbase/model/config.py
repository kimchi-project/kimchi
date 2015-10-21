#
# Project Ginger Base
#
# Copyright IBM, Corp. 2014-2015
#
# Code derived from Project Kimchi
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

from wok.basemodel import Singleton
from wok.config import config as kconfig
from wok.config import get_version
from wok.utils import wok_log

from ..repositories import Repositories
from ..swupdate import SoftwareUpdate
from debugreports import DebugReportsModel


class ConfigModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        proxy_port = kconfig.get('display', 'display_proxy_port')
        return {'display_proxy_port': proxy_port,
                'version': get_version()}


class CapabilitiesModel(object):
    __metaclass__ = Singleton

    def __init__(self, **kargs):
        # Subscribe function to set host capabilities to be run when cherrypy
        # server is up
        # It is needed because some features tests depends on the server
        cherrypy.engine.subscribe('start', self._set_capabilities)

        # Subscribe function to clean any Kimchi leftovers
        cherrypy.engine.subscribe('stop', self._clean_leftovers)

    def _clean_leftovers(self):
        pass

    def _set_capabilities(self):
        wok_log.info("*** Running feature tests ***")
        wok_log.info("*** Feature tests completed ***")
    _set_capabilities.priority = 90

    def lookup(self, *ident):
        report_tool = DebugReportsModel.get_system_report_tool()
        try:
            SoftwareUpdate()
        except Exception:
            update_tool = False
        else:
            update_tool = True

        try:
            repo = Repositories()
        except Exception:
            repo_mngt_tool = None
        else:
            repo_mngt_tool = repo._pkg_mnger.TYPE

        return {'system_report_tool': bool(report_tool),
                'update_tool': update_tool,
                'repo_mngt_tool': repo_mngt_tool,
                }
