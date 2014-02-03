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

import os
import time
import platform
from collections import defaultdict

import psutil
from cherrypy.process.plugins import BackgroundTask

from kimchi import disks
from kimchi import netinfo
from kimchi.basemodel import Singleton
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.model.vms import DOM_STATE_MAP
from kimchi.utils import kimchi_log


HOST_STATS_INTERVAL = 1


class HostModel(object):
    def __init__(self, **kargs):
        self.host_info = self._get_host_info()

    def _get_host_info(self):
        res = {}
        with open('/proc/cpuinfo') as f:
            for line in f.xreadlines():
                if "model name" in line:
                    res['cpu'] = line.split(':')[1].strip()
                    break

        res['memory'] = psutil.TOTAL_PHYMEM
        # 'fedora' '17' 'Beefy Miracle'
        distro, version, codename = platform.linux_distribution()
        res['os_distro'] = distro
        res['os_version'] = version
        res['os_codename'] = unicode(codename, "utf-8")

        return res

    def lookup(self, *name):
        return self.host_info

    def shutdown(self, args=None):
        # Check for running vms before shutdown
        running_vms = self._get_vms_list_by_state('running')
        if len(running_vms) > 0:
            raise OperationFailed("Shutdown not allowed: VMs are running!")
        kimchi_log.info('Host is going to shutdown.')
        os.system('shutdown -h now')

    def reboot(self, args=None):
        # Find running VMs
        running_vms = self._get_vms_list_by_state('running')
        if len(running_vms) > 0:
            raise OperationFailed("Reboot not allowed: VMs are running!")
        kimchi_log.info('Host is going to reboot.')
        os.system('reboot')

    def _get_vms_list_by_state(self, state):
        ret_list = []
        for name in self.vms_get_list():
            info = self._get_vm(name).info()
            if (DOM_STATE_MAP[info[0]]) == state:
                ret_list.append(name)
        return ret_list


class HostStatsModel(object):
    __metaclass__ = Singleton

    def __init__(self, **kargs):
        self.host_stats = defaultdict(int)
        self.host_stats_thread = BackgroundTask(HOST_STATS_INTERVAL,
                                                self._update_host_stats)
        self.host_stats_thread.start()

    def lookup(self, *name):
        return {'cpu_utilization': self.host_stats['cpu_utilization'],
                'memory': self.host_stats.get('memory'),
                'disk_read_rate': self.host_stats['disk_read_rate'],
                'disk_write_rate': self.host_stats['disk_write_rate'],
                'net_recv_rate': self.host_stats['net_recv_rate'],
                'net_sent_rate': self.host_stats['net_sent_rate']}

    def _update_host_stats(self):
        preTimeStamp = self.host_stats['timestamp']
        timestamp = time.time()
        # FIXME when we upgrade psutil, we can get uptime by psutil.uptime
        # we get uptime by float(open("/proc/uptime").readline().split()[0])
        # and calculate the first io_rate after the OS started.
        seconds = (timestamp - preTimeStamp if preTimeStamp else
                   float(open("/proc/uptime").readline().split()[0]))

        self.host_stats['timestamp'] = timestamp
        self._get_host_disk_io_rate(seconds)
        self._get_host_network_io_rate(seconds)

        self._get_percentage_host_cpu_usage()
        self._get_host_memory_stats()

    def _get_percentage_host_cpu_usage(self):
        # This is cpu usage producer. This producer will calculate the usage
        # at an interval of HOST_STATS_INTERVAL.
        # The psutil.cpu_percent works as non blocking.
        # psutil.cpu_percent maintains a cpu time sample.
        # It will update the cpu time sample when it is called.
        # So only this producer can call psutil.cpu_percent in kimchi.
        self.host_stats['cpu_utilization'] = psutil.cpu_percent(None)

    def _get_host_memory_stats(self):
        virt_mem = psutil.virtual_memory()
        # available:
        #  the actual amount of available memory that can be given
        #  instantly to processes that request more memory in bytes; this
        #  is calculated by summing different memory values depending on
        #  the platform (e.g. free + buffers + cached on Linux)
        memory_stats = {'total': virt_mem.total,
                        'free': virt_mem.free,
                        'cached': virt_mem.cached,
                        'buffers': virt_mem.buffers,
                        'avail': virt_mem.available}
        self.host_stats['memory'] = memory_stats

    def _get_host_disk_io_rate(self, seconds):
        prev_read_bytes = self.host_stats['disk_read_bytes']
        prev_write_bytes = self.host_stats['disk_write_bytes']

        disk_io = psutil.disk_io_counters(False)
        read_bytes = disk_io.read_bytes
        write_bytes = disk_io.write_bytes

        rd_rate = int(float(read_bytes - prev_read_bytes) / seconds + 0.5)
        wr_rate = int(float(write_bytes - prev_write_bytes) / seconds + 0.5)

        self.host_stats.update({'disk_read_rate': rd_rate,
                                'disk_write_rate': wr_rate,
                                'disk_read_bytes': read_bytes,
                                'disk_write_bytes': write_bytes})

    def _get_host_network_io_rate(self, seconds):
        prev_recv_bytes = self.host_stats['net_recv_bytes']
        prev_sent_bytes = self.host_stats['net_sent_bytes']

        net_ios = psutil.network_io_counters(True)
        recv_bytes = 0
        sent_bytes = 0
        for key in set(netinfo.nics() +
                       netinfo.wlans()) & set(net_ios.iterkeys()):
            recv_bytes = recv_bytes + net_ios[key].bytes_recv
            sent_bytes = sent_bytes + net_ios[key].bytes_sent

        rx_rate = int(float(recv_bytes - prev_recv_bytes) / seconds + 0.5)
        tx_rate = int(float(sent_bytes - prev_sent_bytes) / seconds + 0.5)

        self.host_stats.update({'net_recv_rate': rx_rate,
                                'net_sent_rate': tx_rate,
                                'net_recv_bytes': recv_bytes,
                                'net_sent_bytes': sent_bytes})


class PartitionsModel(object):
    def __init__(self, **kargs):
        pass

    def get_list(self):
        result = disks.get_partitions_names()
        return result


class PartitionModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        if name not in disks.get_partitions_names():
            raise NotFoundError("Partition %s not found in the host"
                                % name)
        return disks.get_partition_details(name)
