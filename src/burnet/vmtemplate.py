#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.
#

import os
import string

import osinfo

class VMTemplate(object):
    def __init__(self, args):
        self.name = args['name']
        self.info = {}

        # Fetch defaults based on the os distro and version
        os_distro = args.get('os_distro')
        os_version = args.get('os_version')
        name, entry = osinfo.lookup(os_distro, os_version)
        self.info.update(entry)

        # Override with the passed in parameters
        self.info.update(args)

    def _get_disks_xml(self, vm_name, storage_path):
        bus_to_dev = {'ide': 'hd', 'virtio': 'vd'}

        ret = ""
        for i, disk in enumerate(self.info['disks']):
            index = disk.get('index', i)
            volume = "%s-%s.img" % (vm_name, index)
            src = os.path.join(storage_path, volume)
            dev = "%s%s" % (bus_to_dev[self.info['disk_bus']],
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
        params['arch'] = os.uname()[4]

        xml = """
        <domain type='kvm'>
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
            <disk type='file' device='cdrom'>
              <driver name='qemu' type='raw'/>
              <source file='%(cdrom)s' />
              <target dev='hdc' bus='ide'/>
              <readonly/>
            </disk>
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
