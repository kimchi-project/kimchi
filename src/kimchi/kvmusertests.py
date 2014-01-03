#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  ShaoHe Feng <shaohef@linux.vnet.ibm.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import libvirt
import psutil
import uuid


from kimchi.rollbackcontext import RollbackContext


class UserTests(object):
    SIMPLE_VM_XML = """
    <domain type='kvm'>
      <name>%s</name>
      <uuid>%s</uuid>
      <memory unit='KiB'>10240</memory>
      <os>
        <type arch='x86_64' machine='pc'>hvm</type>
        <boot dev='hd'/>
      </os>
    </domain>"""

    def __init__(self):
        self.vm_uuid = uuid.uuid3(uuid.NAMESPACE_DNS, 'vm-test.kimchi.org')
        self.vm_name = "kimchi_test_%s" % self.vm_uuid

    def probe_user(self):
        xml = self.SIMPLE_VM_XML % (self.vm_name, self.vm_uuid)
        user = None
        with RollbackContext() as rollback:
            conn = libvirt.open('qemu:///system')
            rollback.prependDefer(conn.close)
            dom = conn.defineXML(xml)
            rollback.prependDefer(dom.undefine)
            dom.create()
            rollback.prependDefer(dom.destroy)
            with open('/var/run/libvirt/qemu/%s.pid' % self.vm_name) as f:
                pidStr = f.read()
            p = psutil.Process(int(pidStr))
            user = p.username
        return user


if __name__ == '__main__':
    ut = UserTests()
    print ut.probe_user()
