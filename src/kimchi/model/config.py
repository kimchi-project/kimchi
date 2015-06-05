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

from multiprocessing.pool import ThreadPool

import cherrypy

from kimchi.basemodel import Singleton
from kimchi.config import config as kconfig
from kimchi.config import find_qemu_binary, get_version
from kimchi.distroloader import DistroLoader
from kimchi.exception import NotFoundError
from kimchi.model.debugreports import DebugReportsModel
from kimchi.model.featuretests import FeatureTests, FEATURETEST_POOL_NAME
from kimchi.model.featuretests import FEATURETEST_VM_NAME
from kimchi.repositories import Repositories
from kimchi.screenshot import VMScreenshot
from kimchi.swupdate import SoftwareUpdate
from kimchi.utils import check_url_path, kimchi_log, run_command


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
        self.conn = kargs['conn']
        self.qemu_stream = False
        self.libvirt_stream_protocols = []
        self.fc_host_support = False
        self.metadata_support = False
        self.kernel_vfio = False
        self.mem_hotplug_support = False

        # Subscribe function to set host capabilities to be run when cherrypy
        # server is up
        # It is needed because some features tests depends on the server
        cherrypy.engine.subscribe('start', self._set_capabilities)

        # Subscribe function to clean any Kimchi leftovers
        cherrypy.engine.subscribe('stop', self._clean_leftovers)

    def _clean_leftovers(self):
        conn = self.conn.get()
        FeatureTests.disable_libvirt_error_logging()
        try:
            dom = conn.lookupByName(FEATURETEST_VM_NAME)
            dom.undefine()
        except Exception:
            # Any exception can be ignored here
            pass

        try:
            pool = conn.storagePoolLookupByName(FEATURETEST_POOL_NAME)
            pool.undefine()
        except Exception:
            # Any exception can be ignored here
            pass

        FeatureTests.enable_libvirt_error_logging()

    def _set_capabilities(self):
        kimchi_log.info("*** Running feature tests ***")
        conn = self.conn.get()
        self.qemu_stream = FeatureTests.qemu_supports_iso_stream()
        self.nfs_target_probe = FeatureTests.libvirt_support_nfs_probe(conn)
        self.fc_host_support = FeatureTests.libvirt_support_fc_host(conn)
        self.metadata_support = FeatureTests.has_metadata_support(conn)
        self.kernel_vfio = FeatureTests.kernel_support_vfio()
        self.mem_hotplug_support = FeatureTests.has_mem_hotplug_support(conn)

        self.libvirt_stream_protocols = []
        for p in ['http', 'https', 'ftp', 'ftps', 'tftp']:
            if FeatureTests.libvirt_supports_iso_stream(conn, p):
                self.libvirt_stream_protocols.append(p)

        kimchi_log.info("*** Feature tests completed ***")
    _set_capabilities.priority = 90

    def _qemu_support_spice(self):
        qemu_path = find_qemu_binary(find_emulator=True)
        out, err, rc = run_command(['ldd', qemu_path])
        if rc != 0:
            kimchi_log.error('Failed to find qemu binary dependencies: %s',
                             err)
            return False
        for line in out.split('\n'):
            if line.lstrip().startswith('libspice-server.so'):
                return True
        return False

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

        return {'libvirt_stream_protocols': self.libvirt_stream_protocols,
                'qemu_spice': self._qemu_support_spice(),
                'qemu_stream': self.qemu_stream,
                'screenshot': VMScreenshot.get_stream_test_result(),
                'system_report_tool': bool(report_tool),
                'update_tool': update_tool,
                'repo_mngt_tool': repo_mngt_tool,
                'federation': kconfig.get("server", "federation"),
                'auth': kconfig.get("authentication", "method"),
                'kernel_vfio': self.kernel_vfio,
                'nm_running': FeatureTests.is_nm_running(),
                'mem_hotplug_support': self.mem_hotplug_support
                }


class DistrosModel(object):
    def __init__(self, **kargs):
        distroloader = DistroLoader()
        self.distros = distroloader.get()

    def get_list(self):
        def validate_distro(distro):
            if check_url_path(distro['path']):
                return distro['name']

        n_processes = len(self.distros.keys())
        pool = ThreadPool(processes=n_processes)
        map_res = pool.map_async(validate_distro, self.distros.values())
        pool.close()
        pool.join()
        res = list(set(map_res.get()) - set([None]))
        return sorted(res)


class DistroModel(object):
    def __init__(self, **kargs):
        self._distros = DistrosModel()

    def lookup(self, name):
        try:
            return self._distros.distros[name]
        except KeyError:
            raise NotFoundError("KCHDISTRO0001E", {'name': name})
