#
# Project Ginger Base
#
# Copyright IBM, Corp. 2015
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
import logging
import platform

from wok.utils import run_command
from wok.exception import NotFoundError

ARCH = platform.machine()


class LsCpu(object):
    """
    Get CPU information about a CPU hyper threading/architecture on x86
    """
    def log_error(e):
        """
            param e: error details to be logged
        """
        log = logging.getLogger('Util')
        log.warning('Exception in fetching the CPU architecture details: %s',
                    e)

    def __init__(self):
        self.lsCpuInfo = {}
        try:
            # lscpu - display information about the CPU architecture
            out, error, rc = run_command(['lscpu'])
            # Output of lscpu on x86 is expected to be:
            # Architecture:          x86_64
            # CPU op-mode(s):        32-bit, 64-bit
            # Byte Order:            Little Endian
            # CPU(s):                4
            # On-line CPU(s) list:   0-3
            # Thread(s) per core:    2
            # Core(s) per socket:    2
            # Socket(s):             1
            # NUMA node(s):          1
            # Vendor ID:             GenuineIntel
            # CPU family:            6
            # Model:                 42
            # Model name:            Intel(R) Core(TM) i5-2540M CPU @ 2.60GHz
            # Stepping:              7
            # CPU MHz:               976.421
            # CPU max MHz:           3300.0000
            # CPU min MHz:           800.0000
            # BogoMIPS:              5182.99
            # Virtualization:        VT-x
            # L1d cache:             32K
            # L1i cache:             32K
            # L2 cache:              256K
            # L3 cache:              3072K
            # NUMA node0 CPU(s):     0-3
            #
            # Output of lscpu in s390x is expected to be
            # Architecture:          s390x
            # CPU op-mode(s):        32-bit, 64-bit
            # Byte Order:            Big Endian
            # CPU(s):                4
            # On-line CPU(s) list:   0,1
            # Off-line CPU(s) list:  2,3
            # Thread(s) per core:    1
            # Core(s) per socket:    6
            # Socket(s) per book:    6
            # Book(s):               4
            # Vendor ID:             IBM/S390
            # BogoMIPS:              18115.00
            # Hypervisor:            PR/SM
            # Hypervisor vendor:     IBM
            # Virtualization type:   full
            # Dispatching mode:      horizontal
            # L1d cache:             96K
            # L1i cache:             64K
            # L2d cache:             1024K
            # L2i cache:             1024K

            if not rc and (not out.isspace()):
                lscpuout = out.split('\n')
                if lscpuout and len(lscpuout) > 0:
                    for line in lscpuout:
                        if ":" in line and (len(line.split(':')) == 2):
                            self.lsCpuInfo[line.split(':')[0].strip()] = \
                                line.split(':')[1].strip()
                        else:
                            continue
        except Exception, e:
            self.log_error(e)
            raise NotFoundError("GGBCPUINF0004E")

    def get_sockets(self):
        """
            param self: object of the class self
            return: Socket(s) (information about the CPU architecture)
        """
        try:
            sockets = "Socket(s)"
            if ARCH.startswith('s390x'):
                sockets = "Socket(s) per book"
            if len(self.lsCpuInfo) > 0 and sockets in self.lsCpuInfo.keys():
                return int(self.lsCpuInfo[sockets])
            else:
                raise NotFoundError("GGBCPUINF0005E")
        except IndexError, e:
            self.log_error(e)
            raise NotFoundError("GGBCPUINF0005E")

    def get_cores_per_socket(self):
        """
            param self: object of the class self
            return: Core(s) per socket (information about the CPU architecture)
        """
        try:
            cores_per_socket = "Core(s) per socket"
            if len(self.lsCpuInfo) > 0 and cores_per_socket \
                    in self.lsCpuInfo.keys():
                return int(self.lsCpuInfo[cores_per_socket])
            else:
                raise NotFoundError("GGBCPUINF0006E")
        except IndexError, e:
            self.log_error(e)
            raise NotFoundError("GGBCPUINF0006E")

    def get_threads_per_core(self):
        """
            param self: object of the class self
            return: Thread(s) per core (information about the CPU architecture)
        """
        try:
            threads_per_core = "Thread(s) per core"
            if len(self.lsCpuInfo) > 0 and threads_per_core \
                    in self.lsCpuInfo.keys():
                return int(self.lsCpuInfo[threads_per_core])
            else:
                raise NotFoundError("GGBCPUINF0007E")
        except IndexError, e:
            self.log_error(e)
            raise NotFoundError("GGBCPUINF0007E")

    def get_total_cpus(self):
        """
        method to get total cpus retrieved from CPU(s) field of lscpu
        :return: total cpus
        """
        total_cpus = 'CPU(s)'
        if len(self.lsCpuInfo) > 0 and total_cpus in self.lsCpuInfo.keys():
            return int(self.lsCpuInfo[total_cpus])
        else:
            self.log_error("Failed to fetch total cpus count in lscpu output")
            raise NotFoundError("GGBCPUINF0008E")

    def get_hypervisor(self):
        """
        method to get hypervisor name if present in lscpu o/p
        :return: Hypervisor Name
        """
        hypervisor = 'Hypervisor'
        if len(self.lsCpuInfo) > 0 and hypervisor in self.lsCpuInfo.keys():
            return self.lsCpuInfo[hypervisor]
        return None

    def get_hypervisor_vendor(self):
        """
        method to get hypervisor vendor if present in lscpu o/p
        :return: Hypervisor Vendor
        """
        hypervisor_vendor = 'Hypervisor vendor'
        if len(self.lsCpuInfo) > 0 and hypervisor_vendor in \
                self.lsCpuInfo.keys():
            return self.lsCpuInfo[hypervisor_vendor]
        return None
