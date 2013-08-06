#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import os
import string

import osinfo
import isoinfo
from kimchi.exception import *

class VMTemplate(object):
    _bus_to_dev = {'ide': 'hd', 'virtio': 'vd', 'scsi': 'sd'}

    def __init__(self, args, scan=False):
        """
        Construct a VM Template from a widely variable amount of information.
        The only required parameter is a name for the VMTemplate.  If present,
        the os_distro and os_version fields are used to lookup recommended
        settings.  Any parameters provided by the caller will override the
        defaults.  If scan is True and a cdrom is present, the operating system
        will be detected by probing the installation media.
        """
        self.name = args['name']
        self.info = {}

        # Identify the cdrom if present
        iso_distro = iso_version = None
        if scan:
            iso = args.get('cdrom')
            if iso is not None and iso.startswith('/'):
                try:
                    iso_distro, iso_version = isoinfo.probe_one(iso)
                except isoinfo.IsoFormatError, e:
                    raise InvalidParameter(e)

        # Fetch defaults based on the os distro and version
        os_distro = args.get('os_distro', iso_distro)
        os_version = args.get('os_version', iso_version)
        name, entry = osinfo.lookup(os_distro, os_version)
        self.info.update(entry)

        # Override with the passed in parameters
        self.info.update(args)

    def _get_cdrom_xml(self):
        bus = self.info['cdrom_bus']
        dev = "%s%s" % (self._bus_to_dev[bus],
                        string.lowercase[self.info['cdrom_index']])
        params = {'src': self.info['cdrom'], 'dev': dev, 'bus': bus}

        xml = """
            <disk type='file' device='cdrom'>
              <driver name='qemu' type='raw'/>
              <source file='%(src)s' />
              <target dev='%(dev)s' bus='%(bus)s'/>
              <readonly/>
            </disk>
        """ % (params)
        return xml

    def _get_disks_xml(self, vm_name, storage_path):
        ret = ""
        for i, disk in enumerate(self.info['disks']):
            index = disk.get('index', i)
            volume = "%s-%s.img" % (vm_name, index)
            src = os.path.join(storage_path, volume)
            dev = "%s%s" % (self._bus_to_dev[self.info['disk_bus']],
                            string.lowercase[index])
            params = {'src': src, 'dev': dev, 'bus': self.info['disk_bus']}
            ret += """
            <disk type='file' device='disk'>
              <driver name='qemu' type='qcow2'/>
              <source file='%(src)s' />
              <target dev='%(dev)s' bus='%(bus)s' />
            </disk>
            """ % params
        return ret

    def to_volume_list(self, vm_name, storage_path):
        ret = []
        for i, d in enumerate(self.info['disks']):
            index = d.get('index', i)
            volume = "%s-%s.img" % (vm_name, index)

            info = {'name': volume,
                    'capacity': d['size'],
                    'type': 'disk',
                    'format': 'qcow2',
                    'path': '%s/%s' % (storage_path, volume)}

            info['xml'] = """
            <volume>
              <name>%(name)s</name>
              <allocation>0</allocation>
              <capacity unit="G">%(capacity)s</capacity>
              <target>
                <format type='%(format)s'/>
                <path>%(path)s</path>
              </target>
            </volume>
            """ % info
            ret.append(info)
        return ret

    def to_vm_xml(self, vm_name, storage_path):
        params = dict(self.info)
        params['name'] = vm_name
        params['disks'] = self._get_disks_xml(vm_name, storage_path)
        params['cdroms'] = self._get_cdrom_xml()

        xml = """
        <domain type='%(domain)s'>
          <name>%(name)s</name>
          <memory unit='MiB'>%(memory)s</memory>
          <vcpu>%(cpus)s</vcpu>
          <os>
            <type arch='%(arch)s'>hvm</type>
          </os>
          <features>
            <acpi/>
            <apic/>
            <pae/>
          </features>
          <clock offset='utc'/>
          <on_poweroff>destroy</on_poweroff>
          <on_reboot>restart</on_reboot>
          <on_crash>restart</on_crash>
          <devices>
            %(disks)s
            %(cdroms)s
            <interface type='network'>
              <source network='%(network)s'/>
              <model type='%(nic_model)s'/>
            </interface>
            <graphics type='vnc' />
            <sound model='ich6' />
            <memballoon model='virtio' />
          </devices>
        </domain>
        """ % params
        return xml
