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

import glob
import libvirt
import os
import platform
from lxml import etree, objectify
from lxml.builder import E
from operator import itemgetter

from wok.exception import InvalidOperation, InvalidParameter, NotFoundError
from wok.exception import OperationFailed
from wok.rollbackcontext import RollbackContext
from wok.utils import run_command, wok_log

from wok.plugins.kimchi.model.config import CapabilitiesModel
from wok.plugins.kimchi.model.host import DeviceModel, DevicesModel
from wok.plugins.kimchi.model.utils import get_vm_config_flag
from wok.plugins.kimchi.model.vms import DOM_STATE_MAP, VMModel


class VMHostDevsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.caps = CapabilitiesModel(**kargs)

    def get_list(self, vmid):
        dom = VMModel.get_vm(vmid, self.conn)
        xmlstr = dom.XMLDesc(0)
        root = objectify.fromstring(xmlstr)
        try:
            hostdev = root.devices.hostdev
        except AttributeError:
            return []

        return [DeviceModel.deduce_dev_name(e, self.conn) for e in hostdev]

    def _passthrough_device_validate(self, dev_name):
        eligible_dev_names = \
            DevicesModel(conn=self.conn).get_list(_passthrough='true')
        if dev_name not in eligible_dev_names:
            raise InvalidParameter('KCHVMHDEV0002E', {'dev_name': dev_name})

    def create(self, vmid, params):
        dev_name = params['name']
        self._passthrough_device_validate(dev_name)
        dev_info = DeviceModel(conn=self.conn).lookup(dev_name)

        if dev_info['device_type'] == 'pci':
            return self._attach_pci_device(vmid, dev_info)

        with RollbackContext() as rollback:
            try:
                dev = self.conn.get().nodeDeviceLookupByName(dev_name)
                dev.dettach()
            except Exception:
                raise OperationFailed('KCHVMHDEV0005E', {'name': dev_name})
            else:
                rollback.prependDefer(dev.reAttach)

            attach_device = getattr(
                self, '_attach_%s_device' % dev_info['device_type'])

            info = attach_device(vmid, dev_info)
            rollback.commitAll()

        return info

    def _get_pci_device_xml(self, dev_info, slot, is_multifunction):
        if 'detach_driver' not in dev_info:
            dev_info['detach_driver'] = 'kvm'

        source = E.source(E.address(domain=str(dev_info['domain']),
                                    bus=str(dev_info['bus']),
                                    slot=str(dev_info['slot']),
                                    function=str(dev_info['function'])))
        driver = E.driver(name=dev_info['detach_driver'])

        if is_multifunction:
            multi = E.address(type='pci',
                              domain='0',
                              bus='0',
                              slot=str(slot),
                              function=str(dev_info['function']))

            if dev_info['function'] == 0:
                multi = E.address(type='pci',
                                  domain='0',
                                  bus='0',
                                  slot=str(slot),
                                  function=str(dev_info['function']),
                                  multifunction='on')

            host_dev = E.hostdev(source, driver, multi,
                                 mode='subsystem', type='pci', managed='yes')

        else:
            host_dev = E.hostdev(source, driver,
                                 mode='subsystem', type='pci', managed='yes')

        return etree.tostring(host_dev)

    @staticmethod
    def _validate_pci_passthrough_env():
        # Linux kernel < 3.5 doesn't provide /sys/kernel/iommu_groups
        if os.path.isdir('/sys/kernel/iommu_groups'):
            if not glob.glob('/sys/kernel/iommu_groups/*'):
                raise InvalidOperation("KCHVMHDEV0003E")

        # Enable virt_use_sysfs on RHEL6 and older distributions
        # In recent Fedora, there is no virt_use_sysfs.
        out, err, rc = run_command(['getsebool', 'virt_use_sysfs'],
                                   silent=True)
        if rc == 0 and out.rstrip('\n') != "virt_use_sysfs --> on":
            out, err, rc = run_command(['setsebool', '-P',
                                        'virt_use_sysfs=on'])
            if rc != 0:
                wok_log.warning("Unable to turn on sebool virt_use_sysfs")

    def _available_slot(self, dom):
        xmlstr = dom.XMLDesc(0)
        root = objectify.fromstring(xmlstr)
        slots = []
        try:
            devices = root.devices
            slots = [DeviceModel._toint(dev.attrib['slot'])
                     for dev in devices.findall('.//address')
                     if 'slot' in dev.attrib]

        except AttributeError:
            return 1

        slots = sorted(slots)

        for free, slot in enumerate(slots, start=1):
            if free < slot:
                return free

        return free+1

    def _attach_pci_device(self, vmid, dev_info):
        self._validate_pci_passthrough_env()

        dom = VMModel.get_vm(vmid, self.conn)
        # Due to libvirt limitation, we don't support live assigne device to
        # vfio driver.
        driver = ('vfio' if DOM_STATE_MAP[dom.info()[0]] == "shutoff" and
                  self.caps.kernel_vfio else 'kvm')

        # on powerkvm systems it must be vfio driver.
        distro, _, _ = platform.linux_distribution()
        if distro == 'IBM_PowerKVM':
            driver = 'vfio'

        # Attach all PCI devices in the same IOMMU group
        dev_model = DeviceModel(conn=self.conn)
        devs_model = DevicesModel(conn=self.conn)
        affected_names = devs_model.get_list(
            _passthrough_affected_by=dev_info['name'])
        passthrough_names = devs_model.get_list(
            _cap='pci', _passthrough='true')
        group_names = list(set(affected_names) & set(passthrough_names))
        pci_infos = [dev_model.lookup(dev_name) for dev_name in group_names]
        pci_infos.append(dev_info)

        is_multifunction = len(pci_infos) > 1 and \
            DOM_STATE_MAP[dom.info()[0]] == "shutoff"
        pci_infos = sorted(pci_infos, key=itemgetter('name'))

        # all devices in the group that is going to be attached to the vm
        # must be detached from the host first
        with RollbackContext() as rollback:
            for pci_info in pci_infos:
                try:
                    dev = self.conn.get().nodeDeviceLookupByName(
                        pci_info['name'])
                    dev.dettach()
                except Exception:
                    raise OperationFailed('KCHVMHDEV0005E',
                                          {'name': pci_info['name']})
                else:
                    rollback.prependDefer(dev.reAttach)

            rollback.commitAll()

        device_flags = get_vm_config_flag(dom, mode='all')

        slot = 0
        if is_multifunction:
            slot = self._available_slot(dom)
        with RollbackContext() as rollback:
            for pci_info in pci_infos:
                pci_info['detach_driver'] = driver
                xmlstr = self._get_pci_device_xml(pci_info,
                                                  slot,
                                                  is_multifunction)
                try:
                    dom.attachDeviceFlags(xmlstr, device_flags)
                except libvirt.libvirtError:
                    wok_log.error(
                        'Failed to attach host device %s to VM %s: \n%s',
                        pci_info['name'], vmid, xmlstr)
                    raise
                rollback.prependDefer(dom.detachDeviceFlags,
                                      xmlstr, device_flags)
            rollback.commitAll()

        return dev_info['name']

    def _get_scsi_device_xml(self, dev_info):
        adapter = E.adapter(name=('scsi_host%s' % dev_info['host']))
        address = E.address(type='scsi', bus=str(dev_info['bus']),
                            target=str(dev_info['target']),
                            unit=str(dev_info['lun']))
        host_dev = E.hostdev(E.source(adapter, address),
                             mode='subsystem', type='scsi', sgio='unfiltered')
        return etree.tostring(host_dev)

    def _attach_scsi_device(self, vmid, dev_info):
        xmlstr = self._get_scsi_device_xml(dev_info)
        dom = VMModel.get_vm(vmid, self.conn)
        dom.attachDeviceFlags(xmlstr, get_vm_config_flag(dom, mode='all'))
        return dev_info['name']

    def _get_usb_device_xml(self, dev_info):
        source = E.source(
            E.vendor(id=dev_info['vendor']['id']),
            E.product(id=dev_info['product']['id']),
            E.address(bus=str(dev_info['bus']),
                      device=str(dev_info['device'])),
            startupPolicy='optional')
        host_dev = E.hostdev(source, mode='subsystem',
                             ype='usb', managed='yes')
        return etree.tostring(host_dev)

    def _attach_usb_device(self, vmid, dev_info):
        xmlstr = self._get_usb_device_xml(dev_info)
        dom = VMModel.get_vm(vmid, self.conn)
        dom.attachDeviceFlags(xmlstr, get_vm_config_flag(dom, mode='all'))
        return dev_info['name']


class VMHostDevModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def lookup(self, vmid, dev_name):
        dom = VMModel.get_vm(vmid, self.conn)
        xmlstr = dom.XMLDesc(0)
        root = objectify.fromstring(xmlstr)
        try:
            hostdev = root.devices.hostdev
        except AttributeError:
            raise NotFoundError('KCHVMHDEV0001E',
                                {'vmid': vmid, 'dev_name': dev_name})

        dev_model = DeviceModel(conn=self.conn)
        for e in hostdev:
            deduced_name = DeviceModel.deduce_dev_name(e, self.conn)
            if deduced_name == dev_name:
                dev_info = dev_model.lookup(dev_name)
                return {'name': dev_name,
                        'type': e.attrib['type'],
                        'product': dev_info.get('product', None),
                        'vendor': dev_info.get('vendor', None)}

        raise NotFoundError('KCHVMHDEV0001E',
                            {'vmid': vmid, 'dev_name': dev_name})

    def delete(self, vmid, dev_name):
        dom = VMModel.get_vm(vmid, self.conn)
        xmlstr = dom.XMLDesc(0)
        root = objectify.fromstring(xmlstr)

        try:
            hostdev = root.devices.hostdev
        except AttributeError:
            raise NotFoundError('KCHVMHDEV0001E',
                                {'vmid': vmid, 'dev_name': dev_name})

        pci_devs = [(DeviceModel.deduce_dev_name(e, self.conn), e)
                    for e in hostdev if e.attrib['type'] == 'pci']

        for e in hostdev:
            if DeviceModel.deduce_dev_name(e, self.conn) == dev_name:
                xmlstr = etree.tostring(e)
                dom.detachDeviceFlags(
                    xmlstr, get_vm_config_flag(dom, mode='all'))
                if e.attrib['type'] == 'pci':
                    self._delete_affected_pci_devices(dom, dev_name, pci_devs)
                break
        else:
            raise NotFoundError('KCHVMHDEV0001E',
                                {'vmid': vmid, 'dev_name': dev_name})

    def _delete_affected_pci_devices(self, dom, dev_name, pci_devs):
        dev_model = DeviceModel(conn=self.conn)
        try:
            dev_model.lookup(dev_name)
        except NotFoundError:
            return

        affected_names = set(
            DevicesModel(
                conn=self.conn).get_list(_passthrough_affected_by=dev_name))

        for pci_name, e in pci_devs:
            if pci_name in affected_names:
                xmlstr = etree.tostring(e)
                dom.detachDeviceFlags(
                    xmlstr, get_vm_config_flag(dom, mode='all'))


class VMHoldersModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def get_list(self, device_id):
        devsmodel = VMHostDevsModel(conn=self.conn)

        conn = self.conn.get()
        doms = conn.listAllDomains(0)

        res = []
        for dom in doms:
            dom_name = dom.name()
            if device_id in devsmodel.get_list(dom_name):
                state = DOM_STATE_MAP[dom.info()[0]]
                res.append({"name": dom_name, "state": state})
        return res
