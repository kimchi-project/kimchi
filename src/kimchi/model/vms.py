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
import uuid
from xml.etree import ElementTree

import libvirt
from cherrypy.process.plugins import BackgroundTask

from kimchi import vnc
from kimchi import xmlutils
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.model.config import CapabilitiesModel
from kimchi.model.templates import TemplateModel
from kimchi.model.utils import get_vm_name
from kimchi.screenshot import VMScreenshot
from kimchi.utils import run_setfacl_set_attr, template_name_from_uri


DOM_STATE_MAP = {0: 'nostate',
                 1: 'running',
                 2: 'blocked',
                 3: 'paused',
                 4: 'shutdown',
                 5: 'shutoff',
                 6: 'crashed'}

GUESTS_STATS_INTERVAL = 5
VM_STATIC_UPDATE_PARAMS = {'name': './name'}
VM_LIVE_UPDATE_PARAMS = {}

stats = {}


class VMsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.caps = CapabilitiesModel()
        self.guests_stats_thread = BackgroundTask(GUESTS_STATS_INTERVAL,
                                                  self._update_guests_stats)
        self.guests_stats_thread.start()

    def _update_guests_stats(self):
        vm_list = self.get_list()

        for name in vm_list:
            dom = VMModel.get_vm(name, self.conn)
            vm_uuid = dom.UUIDString()
            info = dom.info()
            state = DOM_STATE_MAP[info[0]]

            if state != 'running':
                stats[vm_uuid] = {}
                continue

            if stats.get(vm_uuid, None) is None:
                stats[vm_uuid] = {}

            timestamp = time.time()
            prevStats = stats.get(vm_uuid, {})
            seconds = timestamp - prevStats.get('timestamp', 0)
            stats[vm_uuid].update({'timestamp': timestamp})

            self._get_percentage_cpu_usage(vm_uuid, info, seconds)
            self._get_network_io_rate(vm_uuid, dom, seconds)
            self._get_disk_io_rate(vm_uuid, dom, seconds)

    def _get_percentage_cpu_usage(self, vm_uuid, info, seconds):
        prevCpuTime = stats[vm_uuid].get('cputime', 0)

        cpus = info[3]
        cpuTime = info[4] - prevCpuTime

        base = (((cpuTime) * 100.0) / (seconds * 1000.0 * 1000.0 * 1000.0))
        percentage = max(0.0, min(100.0, base / cpus))

        stats[vm_uuid].update({'cputime': info[4], 'cpu': percentage})

    def _get_network_io_rate(self, vm_uuid, dom, seconds):
        prevNetRxKB = stats[vm_uuid].get('netRxKB', 0)
        prevNetTxKB = stats[vm_uuid].get('netTxKB', 0)
        currentMaxNetRate = stats[vm_uuid].get('max_net_io', 100)

        rx_bytes = 0
        tx_bytes = 0

        tree = ElementTree.fromstring(dom.XMLDesc(0))
        for target in tree.findall('devices/interface/target'):
            dev = target.get('dev')
            io = dom.interfaceStats(dev)
            rx_bytes += io[0]
            tx_bytes += io[4]

        netRxKB = float(rx_bytes) / 1000
        netTxKB = float(tx_bytes) / 1000

        rx_stats = (netRxKB - prevNetRxKB) / seconds
        tx_stats = (netTxKB - prevNetTxKB) / seconds

        rate = rx_stats + tx_stats
        max_net_io = round(max(currentMaxNetRate, int(rate)), 1)

        stats[vm_uuid].update({'net_io': rate, 'max_net_io': max_net_io,
                               'netRxKB': netRxKB, 'netTxKB': netTxKB})

    def _get_disk_io_rate(self, vm_uuid, dom, seconds):
        prevDiskRdKB = stats[vm_uuid].get('diskRdKB', 0)
        prevDiskWrKB = stats[vm_uuid].get('diskWrKB', 0)
        currentMaxDiskRate = stats[vm_uuid].get('max_disk_io', 100)

        rd_bytes = 0
        wr_bytes = 0

        tree = ElementTree.fromstring(dom.XMLDesc(0))
        for target in tree.findall("devices/disk/target"):
            dev = target.get("dev")
            io = dom.blockStats(dev)
            rd_bytes += io[1]
            wr_bytes += io[3]

        diskRdKB = float(rd_bytes) / 1024
        diskWrKB = float(wr_bytes) / 1024

        rd_stats = (diskRdKB - prevDiskRdKB) / seconds
        wr_stats = (diskWrKB - prevDiskWrKB) / seconds

        rate = rd_stats + wr_stats
        max_disk_io = round(max(currentMaxDiskRate, int(rate)), 1)

        stats[vm_uuid].update({'disk_io': rate,
                               'max_disk_io': max_disk_io,
                               'diskRdKB': diskRdKB,
                               'diskWrKB': diskWrKB})

    def create(self, params):
        conn = self.conn.get()
        t_name = template_name_from_uri(params['template'])
        vm_uuid = str(uuid.uuid4())
        vm_list = self.get_list()
        name = get_vm_name(params.get('name'), t_name, vm_list)
        # incoming text, from js json, is unicode, do not need decode
        if name in vm_list:
            raise InvalidOperation("KCHVM0001E", {'name': name})

        vm_overrides = dict()
        pool_uri = params.get('storagepool')
        if pool_uri:
            vm_overrides['storagepool'] = pool_uri
        t = TemplateModel.get_template(t_name, self.objstore, self.conn,
                                       vm_overrides)

        if not self.caps.qemu_stream and t.info.get('iso_stream', False):
            raise InvalidOperation("KCHVM0005E")

        t.validate()
        vol_list = t.fork_vm_storage(vm_uuid)

        # Store the icon for displaying later
        icon = t.info.get('icon')
        if icon:
            with self.objstore as session:
                session.store('vm', vm_uuid, {'icon': icon})

        libvirt_stream = False
        if len(self.caps.libvirt_stream_protocols) == 0:
            libvirt_stream = True

        graphics = params.get('graphics')
        xml = t.to_vm_xml(name, vm_uuid,
                          libvirt_stream=libvirt_stream,
                          qemu_stream_dns=self.caps.qemu_stream_dns,
                          graphics=graphics)

        try:
            conn.defineXML(xml.encode('utf-8'))
        except libvirt.libvirtError as e:
            for v in vol_list:
                vol = conn.storageVolLookupByPath(v['path'])
                vol.delete(0)
            raise OperationFailed("KCHVM0007E", {'name': name,
                                                 'err': e.get_error_message()})

        return name

    def get_list(self):
        conn = self.conn.get()
        names = [dom.name().decode('utf-8') for dom in conn.listAllDomains(0)]
        return sorted(names, key=unicode.lower)


class VMModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.vms = VMsModel(**kargs)
        self.vmscreenshot = VMScreenshotModel(**kargs)

    def update(self, name, params):
        dom = self.get_vm(name, self.conn)
        dom = self._static_vm_update(dom, params)
        self._live_vm_update(dom, params)
        return dom.name().decode('utf-8')

    def _static_vm_update(self, dom, params):
        state = DOM_STATE_MAP[dom.info()[0]]

        old_xml = new_xml = dom.XMLDesc(0)

        for key, val in params.items():
            if key in VM_STATIC_UPDATE_PARAMS:
                xpath = VM_STATIC_UPDATE_PARAMS[key]
                new_xml = xmlutils.xml_item_update(new_xml, xpath, val)

        try:
            if 'name' in params:
                if state == 'running':
                    msg_args = {'name': dom.name(), 'new_name': params['name']}
                    raise InvalidParameter("KCHVM0003E", msg_args)
                else:
                    dom.undefine()
            conn = self.conn.get()
            dom = conn.defineXML(new_xml)
        except libvirt.libvirtError as e:
            dom = conn.defineXML(old_xml)
            raise OperationFailed("KCHVM0008E", {'name': dom.name(),
                                                 'err': e.get_error_message()})
        return dom

    def _live_vm_update(self, dom, params):
        pass

    def lookup(self, name):
        dom = self.get_vm(name, self.conn)
        info = dom.info()
        state = DOM_STATE_MAP[info[0]]
        screenshot = None
        graphics = self._vm_get_graphics(name)
        graphics_type, graphics_listen, graphics_port = graphics
        graphics_port = graphics_port if state == 'running' else None
        try:
            if state == 'running':
                screenshot = self.vmscreenshot.lookup(name)
            elif state == 'shutoff':
                # reset vm stats when it is powered off to avoid sending
                # incorrect (old) data
                stats[dom.UUIDString()] = {}
        except NotFoundError:
            pass

        with self.objstore as session:
            try:
                extra_info = session.get('vm', dom.UUIDString())
            except NotFoundError:
                extra_info = {}
        icon = extra_info.get('icon')

        vm_stats = stats.get(dom.UUIDString(), {})
        res = {}
        res['cpu_utilization'] = vm_stats.get('cpu', 0)
        res['net_throughput'] = vm_stats.get('net_io', 0)
        res['net_throughput_peak'] = vm_stats.get('max_net_io', 100)
        res['io_throughput'] = vm_stats.get('disk_io', 0)
        res['io_throughput_peak'] = vm_stats.get('max_disk_io', 100)

        return {'state': state,
                'stats': str(res),
                'uuid': dom.UUIDString(),
                'memory': info[2] >> 10,
                'cpus': info[3],
                'screenshot': screenshot,
                'icon': icon,
                'graphics': {"type": graphics_type,
                             "listen": graphics_listen,
                             "port": graphics_port}
                }

    def _vm_get_disk_paths(self, dom):
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='disk']/source/@file"
        return xmlutils.xpath_get_text(xml, xpath)

    def _vm_exists(self, name):
        try:
            self.get_vm(name, self.conn)
            return True
        except NotFoundError:
            return False
        except Exception, e:
            raise OperationFailed("KCHVM0009E", {'name': name,
                                                 'err': e.message})

    @staticmethod
    def get_vm(name, conn):
        conn = conn.get()
        try:
            # outgoing text to libvirt, encode('utf-8')
            return conn.lookupByName(name.encode("utf-8"))
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
                raise NotFoundError("KCHVM0002E", {'name': name})
            else:
                raise

    def delete(self, name):
        if self._vm_exists(name):
            conn = self.conn.get()
            dom = self.get_vm(name, self.conn)
            self._vmscreenshot_delete(dom.UUIDString())
            paths = self._vm_get_disk_paths(dom)
            info = self.lookup(name)

            if info['state'] == 'running':
                self.stop(name)

            dom.undefine()

            for path in paths:
                vol = conn.storageVolLookupByPath(path)
                vol.delete(0)

            with self.objstore as session:
                session.delete('vm', dom.UUIDString(), ignore_missing=True)

            vnc.remove_proxy_token(name)

    def start(self, name):
        # make sure the ISO file has read permission
        dom = self.get_vm(name, self.conn)
        xml = dom.XMLDesc(0)
        xpath = "/domain/devices/disk[@device='cdrom']/source/@file"
        isofiles = xmlutils.xpath_get_text(xml, xpath)
        for iso in isofiles:
            run_setfacl_set_attr(iso)

        dom = self.get_vm(name, self.conn)
        dom.create()

    def stop(self, name):
        if self._vm_exists(name):
            dom = self.get_vm(name, self.conn)
            dom.destroy()

    def _vm_get_graphics(self, name):
        dom = self.get_vm(name, self.conn)
        xml = dom.XMLDesc(0)
        expr = "/domain/devices/graphics/@type"
        res = xmlutils.xpath_get_text(xml, expr)
        graphics_type = res[0] if res else None
        expr = "/domain/devices/graphics/@listen"
        res = xmlutils.xpath_get_text(xml, expr)
        graphics_listen = res[0] if res else None
        graphics_port = None
        if graphics_type:
            expr = "/domain/devices/graphics[@type='%s']/@port" % graphics_type
            res = xmlutils.xpath_get_text(xml, expr)
            graphics_port = int(res[0]) if res else None
        return graphics_type, graphics_listen, graphics_port

    def connect(self, name):
        graphics = self._vm_get_graphics(name)
        graphics_type, graphics_listen, graphics_port = graphics
        if graphics_port is not None:
            vnc.add_proxy_token(name, graphics_port)
        else:
            raise OperationFailed("KCHVM0010E", {'name': name})

    def _vmscreenshot_delete(self, vm_uuid):
        screenshot = VMScreenshotModel.get_screenshot(vm_uuid, self.objstore,
                                                      self.conn)
        screenshot.delete()
        with self.objstore as session:
            session.delete('screenshot', vm_uuid)


class VMScreenshotModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.conn = kargs['conn']

    def lookup(self, name):
        dom = VMModel.get_vm(name, self.conn)
        d_info = dom.info()
        vm_uuid = dom.UUIDString()
        if DOM_STATE_MAP[d_info[0]] != 'running':
            raise NotFoundError("KCHVM0004E", {'name': name})

        screenshot = self.get_screenshot(vm_uuid, self.objstore, self.conn)
        img_path = screenshot.lookup()
        # screenshot info changed after scratch generation
        with self.objstore as session:
            session.store('screenshot', vm_uuid, screenshot.info)
        return img_path

    @staticmethod
    def get_screenshot(vm_uuid, objstore, conn):
        with objstore as session:
            try:
                params = session.get('screenshot', vm_uuid)
            except NotFoundError:
                params = {'uuid': vm_uuid}
                session.store('screenshot', vm_uuid, params)
        return LibvirtVMScreenshot(params, conn)


class LibvirtVMScreenshot(VMScreenshot):
    def __init__(self, vm_uuid, conn):
        VMScreenshot.__init__(self, vm_uuid)
        self.conn = conn

    def _generate_scratch(self, thumbnail):
        def handler(stream, buf, opaque):
            fd = opaque
            os.write(fd, buf)

        fd = os.open(thumbnail, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0644)
        try:
            conn = self.conn.get()
            dom = conn.lookupByUUIDString(self.vm_uuid)
            vm_name = dom.name()
            stream = conn.newStream(0)
            dom.screenshot(stream, 0, 0)
            stream.recvAll(handler, fd)
        except libvirt.libvirtError:
            try:
                stream.abort()
            except:
                pass
            raise NotFoundError("KCHVM0006E", {'name': vm_name})
        else:
            stream.finish()
        finally:
            os.close(fd)
