#
# Project Ginger Base
#
# Copyright IBM, Corp. 2015
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

import os
import platform
import psutil
import re
import time
from cherrypy.process.plugins import BackgroundTask
from collections import defaultdict
import glob

from wok.basemodel import Singleton
from wok.config import config as kconfig
from wok.exception import InvalidOperation
from wok.exception import OperationFailed
from wok.utils import add_task, run_command, wok_log
from wok.model.tasks import TaskModel

from wok.plugins.gingerbase.lscpu import LsCpu
from wok.plugins.gingerbase.model.debugreports import DebugReportsModel
from wok.plugins.gingerbase.repositories import Repositories
from wok.plugins.gingerbase.swupdate import SoftwareUpdate

HOST_STATS_INTERVAL = 1
DOM_STATE_MAP = {0: 'nostate',
                 1: 'running',
                 2: 'blocked',
                 3: 'paused',
                 4: 'shutdown',
                 5: 'shutoff',
                 6: 'crashed',
                 7: 'pmsuspended'}

ARCH = platform.machine()
PROC_CPUINFO = '/proc/cpuinfo'
PROC_SYSINFO = '/proc/sysinfo'
LSMEM = 'lsmem'
CPUS_DEDICATED = 'cpus_dedicated'
CPUS_SHARED = 'cpus_shared'
LPAR_NAME = 'lpar_name'
LPAR_NUMBER = 'lpar_number'


class HostModel(object):
    def __init__(self, **kargs):
        # self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)
        self.lscpu = LsCpu()

    def _get_ppc_cpu_model(self):
        """
        method to get cpu_model for ppc architecture
        """
        res = {}
        with open(PROC_CPUINFO) as f:
            for line in f.xreadlines():
                # Parse CPU, CPU's revision and CPU's clock information
                for key in ['cpu', 'revision', 'clock']:
                    if key in line:
                        info = line.split(':')[1].strip()
                        if key == 'clock':
                            value = float(info.split('MHz')[0].strip()) / 1000
                        else:
                            value = info.split('(')[0].strip()
                        res[key] = value

                        # Power machines show, for each cpu/core, a block with
                        # all cpu information. Here we control the scan of the
                        # necessary information (1st block provides
                        # everything), skipping the function when find all
                        # information.
                        if len(res.keys()) == 3:
                            return "%(cpu)s (%(revision)s) @ %(clock)s GHz\
                                    " % res

        return ""

    def _get_x86_cpu_model(self):
        """
        method to get cpu_model for x86 architecture
        """
        try:
            with open(PROC_CPUINFO) as f:
                for line in f.xreadlines():
                    if "model name" in line:
                        return line.split(':')[1].strip()
                        break
        except Exception as e:
            wok_log.error("Failed to retrive cpu_model for "
                          "%s. Error: %s", ARCH, e.__str__())
        return ""

    def _get_s390x_host_info(self):
        """
        method to get additional host details
        specific to s390x architecture
        :return: dictionary
        """
        host_info = {}
        host_info['cpus'] = self._get_cpus()
        host_info['cpus']['dedicated'] = 0
        host_info['cpus']['shared'] = 0
        host_info['cpu_model'] = ""
        host_info['virtualization'] = {}
        s390x_sysinfo = self._get_s390x_sysinfo()
        if 'manufacturer' in s390x_sysinfo.keys():
            host_info['cpu_model'] = s390x_sysinfo['manufacturer']
        if 'type' in s390x_sysinfo.keys():
            host_info['cpu_model'] = \
                host_info['cpu_model'] + "/" + s390x_sysinfo['type']
        if 'model' in s390x_sysinfo.keys():
            host_info['cpu_model'] = \
                host_info['cpu_model'] + "/" + s390x_sysinfo['model']
        if CPUS_DEDICATED in s390x_sysinfo.keys():
            host_info['cpus']['dedicated'] = s390x_sysinfo[CPUS_DEDICATED]
        if CPUS_SHARED in s390x_sysinfo.keys():
            host_info['cpus']['shared'] = s390x_sysinfo[CPUS_SHARED]
        host_info['virtualization']['hypervisor'] = \
            self.lscpu.get_hypervisor()
        host_info['virtualization']['hypervisor_vendor'] = \
            self.lscpu.get_hypervisor_vendor()
        host_info['virtualization'][LPAR_NAME] = ''
        host_info['virtualization'][LPAR_NUMBER] = ''
        if LPAR_NAME in s390x_sysinfo.keys():
            host_info['virtualization'][LPAR_NAME] = s390x_sysinfo[LPAR_NAME]
        if LPAR_NUMBER in s390x_sysinfo.keys():
            host_info['virtualization'][LPAR_NUMBER] = \
                s390x_sysinfo[LPAR_NUMBER]

        return host_info

    def _get_s390x_sysinfo(self):
        """
        This method retrieves following system information
        for s390 architecture
        * manufacturer: Manufacturer of host machine
        * type: Type of the host machine
        * model:Model of host machine
        * LPAR_NUMBER: LPAR Number of host
        * LPAR_NAME: Name of host LPAR
        * CPUS_DEDICATED: LPAR CPUs Dedicated
        * CPUS_SHARED: LPAR CPUs Shared

        :param self: object of the class self
        :return: dictionary with following keys -
                 'manufacturer', 'type', 'model', CPUS_SHARED,
                 CPUS_DEDICATED, LPAR_NUMBER, LPAR_NAME
        """
        s390x_sysinfo = {}
        try:
            with open(PROC_SYSINFO) as f:
                for line in f.xreadlines():
                    if ":" in line and (len(line.split(':')) == 2):
                        info = line.split(':')
                        if info[0] == 'Model' and (len(info[1].split()) == 2):
                            s390x_sysinfo['model'] = \
                                info[1].split()[0].strip() +\
                                " "+info[1].split()[1].strip()
                        elif info[0] == 'Manufacturer':
                            s390x_sysinfo['manufacturer'] = info[1].strip()
                        elif info[0] == 'Type':
                            s390x_sysinfo['type'] = info[1].strip()
                        elif info[0] == 'LPAR Number':
                            s390x_sysinfo[LPAR_NUMBER] = int(info[1].strip())
                        elif info[0] == 'LPAR Name':
                            s390x_sysinfo[LPAR_NAME] = info[1].strip()
                        elif info[0] == 'LPAR CPUs Dedicated':
                            s390x_sysinfo[CPUS_DEDICATED] =\
                                int(info[1].strip())
                        elif info[0] == 'LPAR CPUs Shared':
                            s390x_sysinfo[CPUS_SHARED] = int(info[1].strip())
        except Exception as e:
            wok_log.error("Failed to retrieve information from %s file. "
                          "Error: %s", PROC_SYSINFO, e.__str__())

        return s390x_sysinfo

    def _get_memory(self):
        """
        method to retrieve memory information for all architecture
        :return: dictionary with keys "online" and "offline"
        """
        memory = {}
        online_memory = 0
        offline_memory = 0
        if ARCH.startswith('s390x'):
            online_mem_pat = r'^Total online memory :\s+(\d+)\s+MB$'
            offline_mem_pat = r'^Total offline memory:\s+(\d+)\s+MB$'
            out, err, rc = run_command(LSMEM)
            # output of lsmem in s390x architecture is expected to be
            # Address Range                          Size (MB)  State\
            #     Removable  Device
            # ========================================================\
            # =======================
            # 0x0000000000000000-0x000000000fffffff        256  online\
            #    no         0
            # 0x0000000010000000-0x000000002fffffff        512  online\
            #    yes        1-2
            # 0x0000000030000000-0x000000007fffffff       1280  online\
            #    no         3-7
            # 0x0000000080000000-0x00000000ffffffff       2048  offline\
            #   -          8-15
            #
            # Memory device size  : 256 MB
            # Memory block size   : 256 MB
            # Total online memory : 2048 MB
            # Total offline memory: 2048 MB
            if not rc:
                online_mem =\
                    re.search(online_mem_pat, out.strip(), re.M | re.I)
                offline_mem =\
                    re.search(offline_mem_pat, out.strip(), re.M | re.I)
                if online_mem and len(online_mem.groups()) == 1:
                    online_memory = int(online_mem.group(1)) * 1024 * 1024
                    # converting MB to bytes
                    # lsmem always returns memory in MB
                if offline_mem and len(offline_mem.groups()) == 1:
                    offline_memory = int(offline_mem.group(1)) * 1024 * 1024
            else:
                wok_log.error('Failed to retrieve memory information with'
                              ' command %s. Error: %s' % (LSMEM, err))
        else:
            if hasattr(psutil, 'phymem_usage'):
                online_memory = psutil.phymem_usage().total
            elif hasattr(psutil, 'virtual_memory'):
                online_memory = psutil.virtual_memory().total

        memory['online'] = online_memory
        memory['offline'] = offline_memory
        return memory

    def _get_cpus(self):
        """
        method to retrieve online cpus count and offline cpus
        count for all architecture
        :return: dictionary with keys "online" and "offline"
        """
        cpus = {}
        total_cpus = int(self.lscpu.get_total_cpus())
        offline_cpus = 0

        online_cpus = psutil.NUM_CPUS
        # psutil is unstable on how to get the number of
        # cpus, different versions call it differently
        if hasattr(psutil, 'cpu_count'):
            online_cpus = psutil.cpu_count()

        elif hasattr(psutil, 'NUM_CPUS'):
            online_cpus = psutil.NUM_CPUS

        elif hasattr(psutil, '_psplatform'):
            for method_name in ['_get_num_cpus', 'get_num_cpus']:

                method = getattr(psutil._psplatform, method_name, None)
                if method is not None:
                    online_cpus = method()
                    break
        if total_cpus >= online_cpus:
            offline_cpus = total_cpus - online_cpus
        cpus['online'] = online_cpus
        cpus['offline'] = offline_cpus
        return cpus

    def _get_base_info(self):
        """
        method to retrieve common host information for all architectures
        :return: dictionary with keys 'os_distro', 'os_version', 'os_codename'
                 'architecture', 'host', memory
        """
        common_info = {}
        # Include IBM PowerKVM name to supported distro names
        _sup_distros = platform._supported_dists + ('ibm_powerkvm',)
        # 'fedora' '17' 'Beefy Miracle'
        distro, version, codename = platform.linux_distribution(
            supported_dists=_sup_distros)
        common_info['os_distro'] = distro
        common_info['os_version'] = version
        common_info['os_codename'] = unicode(codename, "utf-8")
        common_info['architecture'] = ARCH
        common_info['host'] = platform.node()
        common_info['memory'] = self._get_memory()

        return common_info

    def lookup(self, *name):
        """
        method to get basic information for host
        """
        host_info = self._get_base_info()
        if ARCH.startswith('s390x'):
            host_info.update(self._get_s390x_host_info())
        elif ARCH.startswith('ppc'):
            host_info['cpus'] = self._get_cpus()
            host_info['cpu_model'] = self._get_ppc_cpu_model()
        else:
            host_info['cpus'] = self._get_cpus()
            host_info['cpu_model'] = self._get_x86_cpu_model()
        return host_info

    def swupdate(self, *name):
        try:
            swupdate = SoftwareUpdate()
        except:
            raise OperationFailed('GGBPKGUPD0004E')

        pkgs = swupdate.getNumOfUpdates()
        if pkgs == 0:
            raise OperationFailed('GGBPKGUPD0001E')

        wok_log.debug('Host is going to be updated.')
        taskid = add_task('/plugins/gingerbase/host/swupdate',
                          swupdate.doUpdate,
                          self.objstore, None)
        return self.task.lookup(taskid)

    def shutdown(self, args=None):
        # Check for running vms before shutdown
        running_vms = self.get_vmlist_bystate('running')
        if len(running_vms) > 0:
            raise OperationFailed("GGBHOST0001E")

        wok_log.info('Host is going to shutdown.')
        os.system('shutdown -h now')

    def reboot(self, args=None):
        # Check for running vms before reboot
        running_vms = self.get_vmlist_bystate('running')
        if len(running_vms) > 0:
            raise OperationFailed("GGBHOST0002E")

        wok_log.info('Host is going to reboot.')
        os.system('reboot')

    def get_vmlist_bystate(self, state='running'):
        try:
            libvirt_mod = __import__('libvirt')
        except Exception, e:
            wok_log.info("Unable to import libvirt module. Details:",
                         e.message)
            # Ignore any error and assume there is no vm running in the host
            return []

        try:
            conn = libvirt_mod.open(None)
            return [dom.name().decode('utf-8')
                    for dom in conn.listAllDomains(0)
                    if (DOM_STATE_MAP[dom.info()[0]] == state)]
        except Exception, e:
            wok_log.info("Unable to get virtual machines information. "
                         "Details:", e.message)
            raise OperationFailed("GGBHOST0003E")


class SoftwareUpdateProgressModel(object):
    def __init__(self, **kargs):
        self.task = TaskModel(**kargs)
        self.objstore = kargs['objstore']

    def lookup(self, *name):
        try:
            swupdate = SoftwareUpdate()
        except:
            raise OperationFailed('GGBPKGUPD0004E')

        taskid = add_task('/plugins/gingerbase/host/swupdateprogress',
                          swupdate.tailUpdateLogs, self.objstore, None)
        return self.task.lookup(taskid)


class HostStatsModel(object):
    __metaclass__ = Singleton

    def __init__(self, **kargs):
        self.host_stats = defaultdict(list)
        self.host_stats_thread = BackgroundTask(HOST_STATS_INTERVAL,
                                                self._update_host_stats)
        self.host_stats_thread.start()

    def lookup(self, *name):
        return {'cpu_utilization': self.host_stats['cpu_utilization'][-1],
                'memory': self.host_stats['memory'][-1],
                'disk_read_rate': self.host_stats['disk_read_rate'][-1],
                'disk_write_rate': self.host_stats['disk_write_rate'][-1],
                'net_recv_rate': self.host_stats['net_recv_rate'][-1],
                'net_sent_rate': self.host_stats['net_sent_rate'][-1]}

    def _update_host_stats(self):
        preTimeStamp = self.host_stats['timestamp']
        timestamp = time.time()
        # FIXME when we upgrade psutil, we can get uptime by psutil.uptime
        # we get uptime by float(open("/proc/uptime").readline().split()[0])
        # and calculate the first io_rate after the OS started.
        with open("/proc/uptime") as time_f:
            seconds = (timestamp - preTimeStamp if preTimeStamp else
                       float(time_f.readline().split()[0]))

        self.host_stats['timestamp'] = timestamp
        self._get_host_disk_io_rate(seconds)
        self._get_host_network_io_rate(seconds)

        self._get_percentage_host_cpu_usage()
        self._get_host_memory_stats()

        # store only 60 stats (1 min)
        for key, value in self.host_stats.iteritems():
            if isinstance(value, list):
                if len(value) == 60:
                    self.host_stats[key] = value[10:]

    def _get_percentage_host_cpu_usage(self):
        # This is cpu usage producer. This producer will calculate the usage
        # at an interval of HOST_STATS_INTERVAL.
        # The psutil.cpu_percent works as non blocking.
        # psutil.cpu_percent maintains a cpu time sample.
        # It will update the cpu time sample when it is called.
        # So only this producer can call psutil.cpu_percent in gingerbase.
        self.host_stats['cpu_utilization'].append(psutil.cpu_percent(None))

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
        self.host_stats['memory'].append(memory_stats)

    def _get_host_disk_io_rate(self, seconds):
        disk_read_bytes = self.host_stats['disk_read_bytes']
        disk_write_bytes = self.host_stats['disk_write_bytes']
        prev_read_bytes = disk_read_bytes[-1] if disk_read_bytes else 0
        prev_write_bytes = disk_write_bytes[-1] if disk_write_bytes else 0

        disk_io = psutil.disk_io_counters(False)
        read_bytes = disk_io.read_bytes
        write_bytes = disk_io.write_bytes

        rd_rate = int(float(read_bytes - prev_read_bytes) / seconds + 0.5)
        wr_rate = int(float(write_bytes - prev_write_bytes) / seconds + 0.5)

        self.host_stats['disk_read_rate'].append(rd_rate)
        self.host_stats['disk_write_rate'].append(wr_rate)
        self.host_stats['disk_read_bytes'].append(read_bytes)
        self.host_stats['disk_write_bytes'].append(write_bytes)

    def _get_host_network_io_rate(self, seconds):
        net_recv_bytes = self.host_stats['net_recv_bytes']
        net_sent_bytes = self.host_stats['net_sent_bytes']
        prev_recv_bytes = net_recv_bytes[-1] if net_recv_bytes else 0
        prev_sent_bytes = net_sent_bytes[-1] if net_sent_bytes else 0

        net_ios = None
        if hasattr(psutil, 'net_io_counters'):
            net_ios = psutil.net_io_counters(True)
        elif hasattr(psutil, 'network_io_counters'):
            net_ios = psutil.network_io_counters(True)

        recv_bytes = 0
        sent_bytes = 0
        for key in set(self.nics() +
                       self.wlans()) & set(net_ios.iterkeys()):
            recv_bytes = recv_bytes + net_ios[key].bytes_recv
            sent_bytes = sent_bytes + net_ios[key].bytes_sent

        rx_rate = int(float(recv_bytes - prev_recv_bytes) / seconds + 0.5)
        tx_rate = int(float(sent_bytes - prev_sent_bytes) / seconds + 0.5)

        self.host_stats['net_recv_rate'].append(rx_rate)
        self.host_stats['net_sent_rate'].append(tx_rate)
        self.host_stats['net_recv_bytes'].append(recv_bytes)
        self.host_stats['net_sent_bytes'].append(sent_bytes)

    def wlans(self):
        WLAN_PATH = '/sys/class/net/*/wireless'
        return [b.split('/')[-2] for b in glob.glob(WLAN_PATH)]

    # FIXME if we do not want to list usb nic
    def nics(self):
        NIC_PATH = '/sys/class/net/*/device'
        return list(set([b.split('/')[-2] for b in glob.glob(NIC_PATH)]) -
                    set(self.wlans()))


class HostStatsHistoryModel(object):
    def __init__(self, **kargs):
        self.history = HostStatsModel(**kargs)

    def lookup(self, *name):
        return {'cpu_utilization': self.history.host_stats['cpu_utilization'],
                'memory': self.history.host_stats['memory'],
                'disk_read_rate': self.history.host_stats['disk_read_rate'],
                'disk_write_rate': self.history.host_stats['disk_write_rate'],
                'net_recv_rate': self.history.host_stats['net_recv_rate'],
                'net_sent_rate': self.history.host_stats['net_sent_rate']}


class CapabilitiesModel(object):
    __metaclass__ = Singleton

    def __init__(self, **kargs):
        pass

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
                'federation': kconfig.get("server", "federation")
                }


class PackagesUpdateModel(object):
    def __init__(self, **kargs):
        try:
            self.host_swupdate = SoftwareUpdate()
        except:
            self.host_swupdate = None

    def get_list(self):
        if self.host_swupdate is None:
            raise OperationFailed('GGBPKGUPD0004E')

        return self.host_swupdate.getUpdates()


class PackageUpdateModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        try:
            swupdate = SoftwareUpdate()
        except Exception:
            raise OperationFailed('GGBPKGUPD0004E')

        return swupdate.getUpdate(name)


class RepositoriesModel(object):
    def __init__(self, **kargs):
        try:
            self.host_repositories = Repositories()
        except:
            self.host_repositories = None

    def get_list(self):
        if self.host_repositories is None:
            raise InvalidOperation('GGBREPOS0014E')

        return sorted(self.host_repositories.getRepositories())

    def create(self, params):
        if self.host_repositories is None:
            raise InvalidOperation('GGBREPOS0014E')

        return self.host_repositories.addRepository(params)


class RepositoryModel(object):
    def __init__(self, **kargs):
        try:
            self._repositories = Repositories()
        except:
            self._repositories = None

    def lookup(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('GGBREPOS0014E')

        return self._repositories.getRepository(repo_id)

    def enable(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('GGBREPOS0014E')

        return self._repositories.enableRepository(repo_id)

    def disable(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('GGBREPOS0014E')

        return self._repositories.disableRepository(repo_id)

    def update(self, repo_id, params):
        if self._repositories is None:
            raise InvalidOperation('GGBREPOS0014E')

        return self._repositories.updateRepository(repo_id, params)

    def delete(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('GGBREPOS0014E')

        return self._repositories.removeRepository(repo_id)
