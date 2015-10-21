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

import platform

from wok.exception import InvalidParameter, InvalidOperation
from wok.utils import run_command
from wok.plugins.gingerbase.lscpu import LsCpu


ARCH = 'power' if platform.machine().startswith('ppc') else 'x86'


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
        self.lscpu = LsCpu()

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
            self.sockets = int(self.lscpu.get_sockets())
            self.cores_per_socket = int(self.lscpu.get_cores_per_socket())
            self.cores_present = self.cores_per_socket * self.sockets
            self.cores_available = self.cores_present
            self.threads_per_core = self.lscpu.get_threads_per_core()

    def lookup(self, ident):
        return {
            'guest_threads_enabled': self.guest_threads_enabled,
            'sockets': self.sockets,
            'cores_per_socket': self.cores_per_socket,
            'cores_present': self.cores_present,
            'cores_available': self.cores_available,
            'threads_per_core': self.threads_per_core,
            }

    def check_topology(self, vcpus, topology):
        """
            param vcpus: should be an integer
            param iso_path: the path of the guest ISO
            param topology: {'sockets': x, 'cores': x, 'threads': x}
        """
        sockets = topology['sockets']
        cores = topology['cores']
        threads = topology['threads']

        if not self.guest_threads_enabled:
            raise InvalidOperation("GGBCPUINF0003E")
        if vcpus != sockets * cores * threads:
            raise InvalidParameter("GGBCPUINF0002E")
        if vcpus > self.cores_available * self.threads_per_core:
            raise InvalidParameter("GGBCPUINF0001E")
        if threads > self.threads_per_core:
            raise InvalidParameter("GGBCPUINF0002E")
