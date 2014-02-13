#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

from kimchi.basemodel import Singleton
from kimchi.config import config as kconfig
from kimchi.distroloader import DistroLoader
from kimchi.exception import NotFoundError
from kimchi.featuretests import FeatureTests
from kimchi.model.debugreports import DebugReportsModel
from kimchi.screenshot import VMScreenshot
from kimchi.swupdate import SoftwareUpdate
from kimchi.utils import kimchi_log


class ConfigModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        proxy_port = kconfig.get('display', 'display_proxy_port')
        return {'http_port': cherrypy.server.socket_port,
                'display_proxy_port': proxy_port}


class CapabilitiesModel(object):
    __metaclass__ = Singleton

    def __init__(self, **kargs):
        self.qemu_stream = False
        self.qemu_stream_dns = False
        self.libvirt_stream_protocols = []
        self.fc_host_support = False

        # Subscribe function to set host capabilities to be run when cherrypy
        # server is up
        # It is needed because some features tests depends on the server
        cherrypy.engine.subscribe('start', self._set_capabilities)

    def _set_capabilities(self):
        kimchi_log.info("*** Running feature tests ***")
        self.qemu_stream = FeatureTests.qemu_supports_iso_stream()
        self.qemu_stream_dns = FeatureTests.qemu_iso_stream_dns()
        self.nfs_target_probe = FeatureTests.libvirt_support_nfs_probe()
        self.fc_host_support = FeatureTests.libvirt_support_fc_host()

        self.libvirt_stream_protocols = []
        for p in ['http', 'https', 'ftp', 'ftps', 'tftp']:
            if FeatureTests.libvirt_supports_iso_stream(p):
                self.libvirt_stream_protocols.append(p)

        kimchi_log.info("*** Feature tests completed ***")
    _set_capabilities.priority = 90

    def lookup(self, *ident):
        report_tool = DebugReportsModel.get_system_report_tool()
        try:
            SoftwareUpdate()
        except Exception:
            update_tool = False
        else:
            update_tool = True

        return {'libvirt_stream_protocols': self.libvirt_stream_protocols,
                'qemu_stream': self.qemu_stream,
                'screenshot': VMScreenshot.get_stream_test_result(),
                'system_report_tool': bool(report_tool),
                'update_tool': update_tool}


class DistrosModel(object):
    def __init__(self, **kargs):
        distroloader = DistroLoader()
        self.distros = distroloader.get()

    def get_list(self):
        return self.distros.keys()


class DistroModel(object):
    def __init__(self, **kargs):
        self._distros = DistrosModel()

    def lookup(self, name):
        try:
            return self._distros.distros[name]
        except KeyError:
            raise NotFoundError("KCHDISTRO0001E", {'name': name})
