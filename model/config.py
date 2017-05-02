#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2017
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
from multiprocessing.pool import ThreadPool

from wok.basemodel import Singleton
from wok.exception import NotFoundError
from wok.utils import run_command, wok_log

from wok.plugins.kimchi.config import find_qemu_binary
from wok.plugins.kimchi.config import get_kimchi_version
from wok.plugins.kimchi.distroloader import DistroLoader
from wok.plugins.kimchi.model.featuretests import FeatureTests
from wok.plugins.kimchi.model.featuretests import FEATURETEST_POOL_NAME
from wok.plugins.kimchi.model.featuretests import FEATURETEST_VM_NAME
from wok.plugins.kimchi.screenshot import VMScreenshot
from wok.plugins.kimchi.utils import check_url_path, is_libvirtd_up


class ConfigModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        return {'version': get_kimchi_version()}


class CapabilitiesModel(object):
    __metaclass__ = Singleton

    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.qemu_stream = False
        self.libvirt_stream_protocols = []
        self.fc_host_support = False
        self.kernel_vfio = False
        self.nm_running = False
        self.mem_hotplug_support = False
        self.libvirtd_running = False

        # make sure there're no Kimchi leftovers from previous executions
        self._clean_leftovers()

        # run feature tests
        self._set_capabilities()

        # Subscribe function to set host capabilities to be run when cherrypy
        # server is up for features that depends on the server
        cherrypy.engine.subscribe('start', self._set_depend_capabilities)

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

    def _set_depend_capabilities(self):
        wok_log.info("\n*** Kimchi: Running dependable feature tests ***")
        conn = self.conn.get()
        if conn is None:
            wok_log.info("*** Kimchi: Dependable feature tests not completed "
                         "***\n")
            return
        self.qemu_stream = FeatureTests.qemu_supports_iso_stream()
        msg = "QEMU stream support .......: %s"
        wok_log.info(msg % str(self.qemu_stream))

        self.libvirt_stream_protocols = []
        for p in ['http', 'https', 'ftp', 'ftps', 'tftp']:
            if FeatureTests.libvirt_supports_iso_stream(conn, p):
                self.libvirt_stream_protocols.append(p)
        msg = "Libvirt Stream Protocols ..: %s"
        wok_log.info(msg % str(self.libvirt_stream_protocols))
        wok_log.info("*** Kimchi: Dependable feature tests completed ***\n")
    _set_depend_capabilities.priority = 90

    def _set_capabilities(self):
        wok_log.info("\n*** Kimchi: Running feature tests ***")
        self.libvirtd_running = is_libvirtd_up()
        msg = "Service Libvirtd running ...: %s"
        wok_log.info(msg % str(self.libvirtd_running))
        if self.libvirtd_running == False:
            wok_log.info("*** Kimchi: Feature tests not completed ***\n")
            return
        conn = self.conn.get()
        self.nfs_target_probe = FeatureTests.libvirt_support_nfs_probe(conn)
        msg = "NFS Target Probe support ...: %s"
        wok_log.info(msg % str(self.nfs_target_probe))
        self.fc_host_support = FeatureTests.libvirt_support_fc_host(conn)
        msg = "Fibre Channel Host support .: %s"
        wok_log.info(msg % str(self.fc_host_support))
        self.kernel_vfio = FeatureTests.kernel_support_vfio()
        msg = "Kernel VFIO support ........: %s"
        wok_log.info(msg % str(self.kernel_vfio))
        self.nm_running = FeatureTests.is_nm_running()
        msg = "Network Manager running ....: %s"
        wok_log.info(msg % str(self.nm_running))
        self.mem_hotplug_support = FeatureTests.has_mem_hotplug_support(conn)
        msg = "Memory Hotplug support .....: %s"
        wok_log.info(msg % str(self.mem_hotplug_support))
        wok_log.info("*** Kimchi: Feature tests completed ***\n")
    _set_capabilities.priority = 90

    def _qemu_support_spice(self):
        qemu_path = find_qemu_binary(find_emulator=True)
        out, err, rc = run_command(['ldd', qemu_path])
        if rc != 0:
            wok_log.error('Failed to find qemu binary dependencies: %s',
                          err)
            return False
        for line in out.split('\n'):
            if line.lstrip().startswith('libspice-server.so'):
                return True
        return False

    def lookup(self, *ident):
        if not is_libvirtd_up():
            return {'libvirt_stream_protocols': [],
                    'qemu_spice': False,
                    'qemu_stream': False,
                    'screenshot': None,
                    'kernel_vfio': self.kernel_vfio,
                    'nm_running': FeatureTests.is_nm_running(),
                    'mem_hotplug_support': False,
                    'libvirtd_running': False}
        elif self.libvirtd_running == False:
            # Libvirt returned, run tests again
            self._set_capabilities()
            self._set_depend_capabilities()

        return {'libvirt_stream_protocols': self.libvirt_stream_protocols,
                'qemu_spice': self._qemu_support_spice(),
                'qemu_stream': self.qemu_stream,
                'screenshot': VMScreenshot.get_stream_test_result(),
                'kernel_vfio': self.kernel_vfio,
                'nm_running': FeatureTests.is_nm_running(),
                'mem_hotplug_support': self.mem_hotplug_support,
                'libvirtd_running': True}


class DistrosModel(object):
    def __init__(self, **kargs):
        distroloader = DistroLoader()
        self.distros = distroloader.get()

    def get_list(self):
        def validate_distro(distro):
            if check_url_path(distro['path']):
                return distro['name']

        n_processes = len(self.distros.keys())
        # Avoid problems if the for some reason the files are not in the right
        # place, or were deleted, or moved or not supported in the arch
        if n_processes < 1:
            return []
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
