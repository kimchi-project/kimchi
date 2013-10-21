#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@br.ibm.com>
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

import libvirt
import threading
import subprocess
import os

import config

ISO_STREAM_XML = """
<domain type='kvm'>
  <name>ISO_STREAMING</name>
  <uuid>c7a5fdbd-edaf-9455-926a-d65c16db1809</uuid>
  <memory unit='KiB'>1048576</memory>
  <currentMemory unit='KiB'>1048576</currentMemory>
  <vcpu placement='static'>1</vcpu>
  <os>
    <type arch='x86_64' machine='pc-1.2'>hvm</type>
    <boot dev='cdrom'/>
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
    <emulator>/usr/bin/kvm</emulator>
    <disk type='network' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source protocol='%(protocol)s' name='/url/path/to/iso/file'>
        <host name='host.name' port='1234'/>
      </source>
      <target dev='hdc' bus='ide'/>
      <readonly/>
      <alias name='ide0-1-0'/>
      <address type='drive' controller='0' bus='1' target='0' unit='0'/>
    </disk>
    <controller type='usb' index='0'/>
    <controller type='pci' index='0' model='pci-root'/>
    <controller type='ide' index='0'/>
    <memballoon model='virtio'/>
  </devices>
</domain>"""

class FeatureTests(object):

    @staticmethod
    def libvirt_supports_iso_stream(protocol):
        xml = ISO_STREAM_XML % {'protocol': protocol}

        try:
            conn = libvirt.open('qemu:///system')
            dom = conn.defineXML(xml)
            dom.undefine()
            return True
        except libvirt.libvirtError:
            return False

    @staticmethod
    def qemu_supports_iso_stream():
        cmd = "qemu-io http://127.0.0.1:8000/images/icon-fedora.png -c 'read -v 0 512'"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()

        return len(stderr) == 0

    @staticmethod
    def qemu_iso_stream_dns():
        cmd = "qemu-io http://localhost:8000/images/icon-fedora.png -c 'read -v 0 512'"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
        thread = threading.Thread(target = proc.communicate)
        thread.start()
        thread.join(5)

        if thread.is_alive():
            proc.terminate()
            thread.join()
            return False

        if proc.returncode != 0:
            return False

        return True
