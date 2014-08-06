#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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

import cherrypy
import libvirt
import lxml.etree as ET
import socket
import subprocess
import threading


from lxml.builder import E


from kimchi.rollbackcontext import RollbackContext
from kimchi.utils import kimchi_log


ISO_STREAM_XML = """
<domain type='kvm'>
  <name>ISO_STREAMING</name>
  <memory unit='KiB'>1048576</memory>
  <os>
    <type>hvm</type>
    <boot dev='cdrom'/>
  </os>
  <devices>
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
  </devices>
</domain>"""

SIMPLE_VM_XML = """
<domain type='kvm'>
  <name>A_SIMPLE_VM</name>
  <memory unit='KiB'>10240</memory>
  <os>
    <type>hvm</type>
    <boot dev='hd'/>
  </os>
</domain>"""

SCSI_FC_XML = """
<pool type='scsi'>
  <name>TEST_SCSI_FC_POOL</name>
  <source>
    <adapter type='fc_host' wwnn='1234567890abcdef' wwpn='abcdef1234567890'/>
  </source>
  <target>
    <path>/dev/disk/by-path</path>
  </target>
</pool>
"""


class FeatureTests(object):

    @staticmethod
    def disable_screen_error_logging():
        def libvirt_errorhandler(userdata, error):
            # A libvirt error handler to ignore annoying messages in stderr
            pass

        # Register the error handler to hide libvirt error in stderr
        libvirt.registerErrorHandler(f=libvirt_errorhandler, ctx=None)
        # Disable cherrypy screen logging, in order to log errors on kimchi
        # file without displaying them on screen
        cherrypy.log.screen = False

    @staticmethod
    def enable_screen_error_logging():
        # Unregister the error handler
        libvirt.registerErrorHandler(f=None, ctx=None)
        # Enable cherrypy screen logging
        cherrypy.log.screen = True

    @staticmethod
    def libvirt_supports_iso_stream(protocol):
        xml = ISO_STREAM_XML % {'protocol': protocol}
        conn = None
        try:
            FeatureTests.disable_screen_error_logging()
            conn = libvirt.open('qemu:///system')
            dom = conn.defineXML(xml)
            dom.undefine()
            return True
        except libvirt.libvirtError, e:
            kimchi_log.error(e.message)
            return False
        finally:
            FeatureTests.enable_screen_error_logging()
            conn is None or conn.close()

    @staticmethod
    def libvirt_support_nfs_probe():
        def _get_xml():
            obj = E.source(E.host(name='localhost'), E.format(type='nfs'))
            xml = ET.tostring(obj)
            return xml
        try:
            conn = libvirt.open('qemu:///system')
            FeatureTests.disable_screen_error_logging()
            conn.findStoragePoolSources('netfs', _get_xml(), 0)
        except libvirt.libvirtError as e:
            kimchi_log.error(e.message)
            if e.get_error_code() == 38:
                # if libvirt cannot find showmount,
                # it returns 38--general system call failure
                return False
        finally:
            FeatureTests.enable_screen_error_logging()
            conn is None or conn.close()

        return True

    @staticmethod
    def qemu_supports_iso_stream():
        host = cherrypy.server.socket_host
        port = cherrypy.server.socket_port
        cmd = "qemu-io -r http://%s:%d/images/icon-fedora.png \
              -c 'read -v 0 512'" % (host, port)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()
        return len(stderr) == 0

    @staticmethod
    def qemu_iso_stream_dns():
        host = socket.getfqdn(cherrypy.server.socket_host)
        port = cherrypy.server.socket_port
        cmd = ["qemu-io", "-r", "http://%s:%d/images/icon-fedora.png" %
               (host, port), "-c", "'read -v 0 512'"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        thread = threading.Thread(target=proc.communicate)
        thread.start()
        thread.join(5)

        if thread.is_alive():
            proc.kill()
            thread.join()
            return False

        if proc.returncode != 0:
            return False

        return True

    @staticmethod
    def libvirt_support_fc_host():
        try:
            FeatureTests.disable_screen_error_logging()
            conn = libvirt.open('qemu:///system')
            pool = None
            pool = conn.storagePoolDefineXML(SCSI_FC_XML, 0)
        except libvirt.libvirtError as e:
            if e.get_error_code() == 27:
                # Libvirt requires adapter name, not needed when supports to FC
                return False
        finally:
            FeatureTests.enable_screen_error_logging()
            pool is None or pool.undefine()
            conn is None or conn.close()
        return True

    @staticmethod
    def has_metadata_support():
        KIMCHI_META_URL = "https://github.com/kimchi-project/kimchi/"
        KIMCHI_NAMESPACE = "kimchi"
        with RollbackContext() as rollback:
            FeatureTests.disable_screen_error_logging()
            rollback.prependDefer(FeatureTests.enable_screen_error_logging)
            conn = libvirt.open('qemu:///system')
            rollback.prependDefer(conn.close)
            dom = conn.defineXML(SIMPLE_VM_XML)
            rollback.prependDefer(dom.undefine)
            try:
                dom.setMetadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT,
                                "<metatest/>", KIMCHI_NAMESPACE,
                                KIMCHI_META_URL,
                                flags=libvirt.VIR_DOMAIN_AFFECT_CURRENT)
                return True
            except libvirt.libvirtError:
                return False
