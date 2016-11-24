#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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

import platform
from xml.etree import ElementTree as ET

from wok.exception import InvalidParameter, InvalidOperation
from wok.utils import run_command, wok_log


ARCH = 'power' if platform.machine().startswith('ppc') else 'x86'
MAX_PPC_VCPUS = 255


def get_topo_capabilities(connect):
    """
    This helper function exists solely to be overridden for
    mockmodel tests. Since other modules use getCapabilies(),
    it can't be overridden directly.
    """
    xml = connect.getCapabilities()
    capabilities = ET.fromstring(xml)
    return capabilities.find('host').find('cpu').find('topology')


class CPUInfoModel(object):
    """
    Get information about a CPU for hyperthreading (on x86)
    or SMT (on POWER) for logic when creating templates and VMs.
    """

    def __init__(self, **kargs):
        self.guest_threads_enabled = False
        self.sockets = 0
        self.cores_present = 0
        self.cores_available = 0
        self.cores_per_socket = 0
        self.threads_per_core = 0
        self.max_threads = 0

        self.conn = kargs['conn']
        libvirt_topology = None
        try:
            connect = self.conn.get()
            libvirt_topology = get_topo_capabilities(connect)
        except Exception as e:
            wok_log.info("Unable to get CPU topology capabilities: %s"
                         % e.message)
            return
        if libvirt_topology is None:
            wok_log.info("cpu_info topology not supported.")
            return

        if ARCH == 'power':
            # IBM PowerPC
            self.guest_threads_enabled = True
            out, error, rc = run_command(['ppc64_cpu', '--smt'])
            if rc or 'on' in out:
                # SMT has to be disabled for guest to use threads as CPUs.
                # rc is always zero, whether SMT is off or on.
                self.guest_threads_enabled = False
            out, error, rc = run_command(['ppc64_cpu', '--cores-present'])
            if not rc:
                self.cores_present = int(out.split()[-1])
            out, error, rc = run_command(['ppc64_cpu', '--cores-on'])
            if not rc:
                self.cores_available = int(out.split()[-1])
            out, error, rc = run_command(['ppc64_cpu', '--threads-per-core'])
            if not rc:
                self.threads_per_core = int(out.split()[-1])
            self.sockets = self.cores_present/self.threads_per_core
            if self.sockets == 0:
                self.sockets = 1
            self.cores_per_socket = self.cores_present/self.sockets
        else:
            # Intel or AMD
            self.guest_threads_enabled = True
            self.sockets = int(libvirt_topology.get('sockets'))
            self.cores_per_socket = int(libvirt_topology.get('cores'))
            self.cores_present = self.cores_per_socket * self.sockets
            self.cores_available = self.cores_present
            self.threads_per_core = int(libvirt_topology.get('threads'))

    def lookup(self, ident):
        return {
            'guest_threads_enabled': self.guest_threads_enabled,
            'sockets': self.sockets,
            'cores_per_socket': self.cores_per_socket,
            'cores_present': self.cores_present,
            'cores_available': self.cores_available,
            'threads_per_core': self.threads_per_core,
            }

    def check_cpu_info(self, cpu_info):
        """
            param cpu_info: topology definition dict: {
                            'maxvcpus': integer
                            'vcpus':    integer
                            'topology': {
                                'sockets': integer,
                                'cores': integer,
                                'threads': integer
                            }
                  }
        """
        maxvcpus = cpu_info.get('maxvcpus')
        vcpus = cpu_info.get('vcpus')
        topology = cpu_info.get('topology')
        if topology:
            # sockets, cores and threads are required when topology is defined
            if 'sockets' not in topology or 'cores' not in topology or \
               'threads' not in topology:
                raise InvalidOperation("KCHCPUINF0007E")

            sockets = topology['sockets']
            cores = topology['cores']
            threads = topology['threads']

            if not self.guest_threads_enabled:
                raise InvalidOperation("KCHCPUINF0003E")
            if threads > self.threads_per_core:
                raise InvalidParameter("KCHCPUINF0006E")
            if maxvcpus != sockets * cores * threads:
                raise InvalidParameter("KCHCPUINF0002E")
            if vcpus % threads != 0:
                raise InvalidParameter("KCHCPUINF0005E")

        if maxvcpus > self.get_host_max_vcpus():
            raise InvalidParameter("KCHCPUINF0004E")
        if vcpus > maxvcpus:
            raise InvalidParameter("KCHCPUINF0001E")

    def get_host_max_vcpus(self):
        if ARCH == 'power':
            max_vcpus = self.cores_available * self.threads_per_core
            if max_vcpus > MAX_PPC_VCPUS:
                max_vcpus = MAX_PPC_VCPUS
        else:
            max_vcpus = self.conn.get().getMaxVcpus('kvm')

        return max_vcpus
