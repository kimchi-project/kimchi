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

import libvirt
import os
import platform
import psutil
import time
from cherrypy.process.plugins import BackgroundTask
from collections import defaultdict
from lxml import objectify

from wok.basemodel import Singleton
from wok.exception import InvalidOperation, InvalidParameter
from wok.exception import NotFoundError, OperationFailed
from wok.utils import add_task, wok_log
from wok.xmlutils.utils import xpath_get_text
from wok.model.tasks import TaskModel

import hostdev
from .. import disks
from .. import netinfo
from ..repositories import Repositories
from ..swupdate import SoftwareUpdate
from config import CapabilitiesModel
from vms import DOM_STATE_MAP, VMModel, VMsModel


HOST_STATS_INTERVAL = 1


class HostModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)
        self.host_info = self._get_host_info()

    def _get_ppc_cpu_info(self):
        res = {}
        with open('/proc/cpuinfo') as f:
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

    def _get_host_info(self):
        res = {}
        if platform.machine().startswith('ppc'):
            res['cpu_model'] = self._get_ppc_cpu_info()
        else:
            with open('/proc/cpuinfo') as f:
                for line in f.xreadlines():
                    if "model name" in line:
                        res['cpu_model'] = line.split(':')[1].strip()
                        break

        res['cpus'] = 0
        res['memory'] = 0L

        # Include IBM PowerKVM name to supported distro names
        _sup_distros = platform._supported_dists + ('ibm_powerkvm',)
        # 'fedora' '17' 'Beefy Miracle'
        distro, version, codename = platform.linux_distribution(
            supported_dists=_sup_distros)
        res['os_distro'] = distro
        res['os_version'] = version
        res['os_codename'] = unicode(codename, "utf-8")

        return res

    def lookup(self, *name):
        cpus = 0

        # psutil is unstable on how to get the number of
        # cpus, different versions call it differently
        if hasattr(psutil, 'cpu_count'):
            cpus = psutil.cpu_count()

        elif hasattr(psutil, 'NUM_CPUS'):
            cpus = psutil.NUM_CPUS

        elif hasattr(psutil, '_psplatform'):
            for method_name in ['_get_num_cpus', 'get_num_cpus']:

                method = getattr(psutil._psplatform, method_name, None)
                if method is not None:
                    cpus = method()
                    break

        self.host_info['cpus'] = cpus
        if hasattr(psutil, 'phymem_usage'):
            self.host_info['memory'] = psutil.phymem_usage().total
        elif hasattr(psutil, 'virtual_memory'):
            self.host_info['memory'] = psutil.virtual_memory().total
        return self.host_info

    def swupdate(self, *name):
        try:
            swupdate = SoftwareUpdate()
        except:
            raise OperationFailed('KCHPKGUPD0004E')

        pkgs = swupdate.getNumOfUpdates()
        if pkgs == 0:
            raise OperationFailed('KCHPKGUPD0001E')

        wok_log.debug('Host is going to be updated.')
        taskid = add_task('/plugins/kimchi/host/swupdate', swupdate.doUpdate,
                          self.objstore, None)
        return self.task.lookup(taskid)

    def shutdown(self, args=None):
        # Check for running vms before shutdown
        running_vms = self._get_vms_list_by_state('running')
        if len(running_vms) > 0:
            raise OperationFailed("KCHHOST0001E")

        wok_log.info('Host is going to shutdown.')
        os.system('shutdown -h now')

    def reboot(self, args=None):
        # Find running VMs
        running_vms = self._get_vms_list_by_state('running')
        if len(running_vms) > 0:
            raise OperationFailed("KCHHOST0002E")

        wok_log.info('Host is going to reboot.')
        os.system('reboot')

    def _get_vms_list_by_state(self, state):
        conn = self.conn.get()
        return [dom.name().decode('utf-8')
                for dom in conn.listAllDomains(0)
                if (DOM_STATE_MAP[dom.info()[0]]) == state]


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
        # So only this producer can call psutil.cpu_percent in kimchi.
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
        for key in set(netinfo.nics() +
                       netinfo.wlans()) & set(net_ios.iterkeys()):
            recv_bytes = recv_bytes + net_ios[key].bytes_recv
            sent_bytes = sent_bytes + net_ios[key].bytes_sent

        rx_rate = int(float(recv_bytes - prev_recv_bytes) / seconds + 0.5)
        tx_rate = int(float(sent_bytes - prev_sent_bytes) / seconds + 0.5)

        self.host_stats['net_recv_rate'].append(rx_rate)
        self.host_stats['net_sent_rate'].append(tx_rate)
        self.host_stats['net_recv_bytes'].append(recv_bytes)
        self.host_stats['net_sent_bytes'].append(sent_bytes)


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
        return disks.get_partition_details(name)


class DevicesModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.caps = CapabilitiesModel(**kargs)
        self.cap_map = \
            {'net': libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_NET,
             'pci': libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_PCI_DEV,
             'scsi': libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_SCSI,
             'scsi_host': libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_SCSI_HOST,
             'storage': libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_STORAGE,
             'usb_device': libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_USB_DEV,
             'usb':
             libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_USB_INTERFACE}
        # TODO: when no longer supporting Libvirt < 1.0.5 distros
        # (like RHEL6) remove this verification and insert the
        # key 'fc_host' with the libvirt variable in the hash
        # declaration above.
        try:
            self.cap_map['fc_host'] = \
                libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_FC_HOST
        except AttributeError:
            self.cap_map['fc_host'] = None

    def _get_unavailable_devices(self):
        vm_list = VMsModel.get_vms(self.conn)
        unavailable_devs = []
        for vm in vm_list:
            dom = VMModel.get_vm(vm, self.conn)
            xmlstr = dom.XMLDesc(0)
            root = objectify.fromstring(xmlstr)
            try:
                hostdev = root.devices.hostdev
            except AttributeError:
                continue

            vm_devs = [DeviceModel.deduce_dev_name(e, self.conn)
                       for e in hostdev]

            for dev in vm_devs:
                unavailable_devs.append(dev)

        return unavailable_devs

    def get_list(self, _cap=None, _passthrough=None,
                 _passthrough_affected_by=None,
                 _available_only=None):
        if _passthrough_affected_by is not None:
            # _passthrough_affected_by conflicts with _cap and _passthrough
            if (_cap, _passthrough) != (None, None):
                raise InvalidParameter("KCHHOST0004E")
            return sorted(
                self._get_passthrough_affected_devs(_passthrough_affected_by))

        if _cap == 'fc_host':
            dev_names = self._get_devices_fc_host()
        else:
            dev_names = self._get_devices_with_capability(_cap)

        if _passthrough is not None and _passthrough.lower() == 'true':
            conn = self.conn.get()
            passthrough_names = [
                dev['name'] for dev in hostdev.get_passthrough_dev_infos(conn)]

            dev_names = list(set(dev_names) & set(passthrough_names))

            if _available_only is not None and _available_only.lower() \
                    == 'true':
                unavailable_devs = self._get_unavailable_devices()
                dev_names = [dev for dev in dev_names
                             if dev not in unavailable_devs]

        dev_names.sort()
        return dev_names

    def _get_devices_with_capability(self, cap):
        conn = self.conn.get()
        if cap is None:
            cap_flag = 0
        else:
            cap_flag = self.cap_map.get(cap)
            if cap_flag is None:
                return []
        return [name.name() for name in conn.listAllDevices(cap_flag)]

    def _get_passthrough_affected_devs(self, dev_name):
        conn = self.conn.get()
        info = DeviceModel(conn=self.conn).lookup(dev_name)
        affected = hostdev.get_affected_passthrough_devices(conn, info)
        return [dev_info['name'] for dev_info in affected]

    def _get_devices_fc_host(self):
        conn = self.conn.get()
        # Libvirt < 1.0.5 does not support fc_host capability
        if not self.caps.fc_host_support:
            ret = []
            scsi_hosts = self._get_devices_with_capability('scsi_host')
            for host in scsi_hosts:
                xml = conn.nodeDeviceLookupByName(host).XMLDesc(0)
                path = '/device/capability/capability/@type'
                if 'fc_host' in xpath_get_text(xml, path):
                    ret.append(host)
            return ret
        # Double verification to catch the case where the libvirt
        # supports fc_host but does not, for some reason, recognize
        # the libvirt.VIR_CONNECT_LIST_NODE_DEVICES_CAP_FC_HOST
        # attribute.
        if not self.cap_map['fc_host']:
            return conn.listDevices('fc_host', 0)
        return self._get_devices_with_capability('fc_host')


class DeviceModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def lookup(self, nodedev_name):
        conn = self.conn.get()
        try:
            dev = conn.nodeDeviceLookupByName(nodedev_name)
        except:
            raise NotFoundError('KCHHOST0003E', {'name': nodedev_name})
        return hostdev.get_dev_info(dev)

    @staticmethod
    def _toint(num_str):
        if num_str.startswith('0x'):
            return int(num_str, 16)
        elif num_str.startswith('0'):
            return int(num_str, 8)
        else:
            return int(num_str)

    @staticmethod
    def deduce_dev_name(e, conn):
        if e.attrib['type'] == 'pci':
            return DeviceModel._deduce_dev_name_pci(e)
        elif e.attrib['type'] == 'scsi':
            return DeviceModel._deduce_dev_name_scsi(e)
        elif e.attrib['type'] == 'usb':
            return DeviceModel._deduce_dev_name_usb(e, conn)
        return None

    @staticmethod
    def _deduce_dev_name_pci(e):
        attrib = {}
        for field in ('domain', 'bus', 'slot', 'function'):
            attrib[field] = DeviceModel._toint(e.source.address.attrib[field])
        return 'pci_%(domain)04x_%(bus)02x_%(slot)02x_%(function)x' % attrib

    @staticmethod
    def _deduce_dev_name_scsi(e):
        attrib = {}
        for field in ('bus', 'target', 'unit'):
            attrib[field] = DeviceModel._toint(e.source.address.attrib[field])
        attrib['host'] = DeviceModel._toint(
            e.source.adapter.attrib['name'][len('scsi_host'):])
        return 'scsi_%(host)d_%(bus)d_%(target)d_%(unit)d' % attrib

    @staticmethod
    def _deduce_dev_name_usb(e, conn):
        dev_names = DevicesModel(conn=conn).get_list(_cap='usb_device')
        usb_infos = [DeviceModel(conn=conn).lookup(dev_name)
                     for dev_name in dev_names]

        unknown_dev = None

        try:
            evendor = DeviceModel._toint(e.source.vendor.attrib['id'])
            eproduct = DeviceModel._toint(e.source.product.attrib['id'])
        except AttributeError:
            evendor = 0
            eproduct = 0
        else:
            unknown_dev = 'usb_vendor_%s_product_%s' % (evendor, eproduct)

        try:
            ebus = DeviceModel._toint(e.source.address.attrib['bus'])
            edevice = DeviceModel._toint(e.source.address.attrib['device'])
        except AttributeError:
            ebus = -1
            edevice = -1
        else:
            unknown_dev = 'usb_bus_%s_device_%s' % (ebus, edevice)

        for usb_info in usb_infos:
            ivendor = DeviceModel._toint(usb_info['vendor']['id'])
            iproduct = DeviceModel._toint(usb_info['product']['id'])
            if evendor == ivendor and eproduct == iproduct:
                return usb_info['name']
            ibus = usb_info['bus']
            idevice = usb_info['device']
            if ebus == ibus and edevice == idevice:
                return usb_info['name']
        return unknown_dev


class PackagesUpdateModel(object):
    def __init__(self, **kargs):
        try:
            self.host_swupdate = SoftwareUpdate()
        except:
            self.host_swupdate = None

    def get_list(self):
        if self.host_swupdate is None:
            raise OperationFailed('KCHPKGUPD0004E')

        return self.host_swupdate.getUpdates()


class PackageUpdateModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        try:
            swupdate = SoftwareUpdate()
        except Exception:
            raise OperationFailed('KCHPKGUPD0004E')

        return swupdate.getUpdate(name)


class RepositoriesModel(object):
    def __init__(self, **kargs):
        try:
            self.host_repositories = Repositories()
        except:
            self.host_repositories = None

    def get_list(self):
        if self.host_repositories is None:
            raise InvalidOperation('KCHREPOS0014E')

        return sorted(self.host_repositories.getRepositories())

    def create(self, params):
        if self.host_repositories is None:
            raise InvalidOperation('KCHREPOS0014E')

        return self.host_repositories.addRepository(params)


class RepositoryModel(object):
    def __init__(self, **kargs):
        try:
            self._repositories = Repositories()
        except:
            self._repositories = None

    def lookup(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('KCHREPOS0014E')

        return self._repositories.getRepository(repo_id)

    def enable(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('KCHREPOS0014E')

        return self._repositories.enableRepository(repo_id)

    def disable(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('KCHREPOS0014E')

        return self._repositories.disableRepository(repo_id)

    def update(self, repo_id, params):
        if self._repositories is None:
            raise InvalidOperation('KCHREPOS0014E')

        return self._repositories.updateRepository(repo_id, params)

    def delete(self, repo_id):
        if self._repositories is None:
            raise InvalidOperation('KCHREPOS0014E')

        return self._repositories.removeRepository(repo_id)
