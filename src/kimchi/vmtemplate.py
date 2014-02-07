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
import socket
import urllib
import urlparse


from kimchi import isoinfo
from kimchi import osinfo
from kimchi.exception import InvalidParameter, IsoFormatError
from kimchi.isoinfo import IsoImage


QEMU_NAMESPACE = "xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'"

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
        iso_distro = iso_version = 'unknown'
        iso = args.get('cdrom', '')

        if scan and len(iso) > 0:

            iso_prefixes = ['/', 'http', 'https', 'ftp', 'ftps', 'tftp']
            if len(filter(iso.startswith, iso_prefixes)) == 0:
                raise InvalidParameter("KCHTMPL0006E", {'param': iso})

            if not iso.startswith('/'):
                self.info.update({'iso_stream': True})

            try:
                iso_img = IsoImage(iso)
                iso_distro, iso_version = iso_img.probe()
            except IsoFormatError:
                raise InvalidParameter("KCHISO0001E", {'filename': iso})

        # Fetch defaults based on the os distro and version
        os_distro = args.get('os_distro', iso_distro)
        os_version = args.get('os_version', iso_version)
        entry = osinfo.lookup(os_distro, os_version)
        self.info.update(entry)

        # Override with the passed in parameters
        graph_args = args.get('graphics')
        if graph_args:
            graphics = dict(self.info['graphics'])
            graphics.update(graph_args)
            args['graphics'] = graphics
        self.info.update(args)

    def _get_cdrom_xml(self, libvirt_stream, qemu_stream_dns):
        bus = self.info['cdrom_bus']
        dev = "%s%s" % (self._bus_to_dev[bus],
                        string.lowercase[self.info['cdrom_index']])

        local_file = """
            <disk type='file' device='cdrom'>
              <driver name='qemu' type='raw'/>
              <source file='%(src)s' />
              <target dev='%(dev)s' bus='%(bus)s'/>
              <readonly/>
            </disk>
        """

        network_file = """
            <disk type='network' device='cdrom'>
              <driver name='qemu' type='raw'/>
              <source protocol='%(protocol)s' name='%(url_path)s'>
                <host name='%(hostname)s' port='%(port)s'/>
              </source>
              <target dev='%(dev)s' bus='%(bus)s'/>
              <readonly/>
            </disk>
        """

        qemu_stream_cmdline = """
            <qemu:commandline>
              <qemu:arg value='-drive'/>
              <qemu:arg value='file=%(url)s,if=none,id=drive-%(bus)s0-1-0,readonly=on,format=raw'/>
              <qemu:arg value='-device'/>
              <qemu:arg value='%(bus)s-cd,bus=%(bus)s.1,unit=0,drive=drive-%(bus)s0-1-0,id=%(bus)s0-1-0'/>
            </qemu:commandline>
        """

        if not self.info.get('iso_stream', False):
            params = {'src': self.info['cdrom'], 'dev': dev, 'bus': bus}
            return local_file % (params)

        output = urlparse.urlparse(self.info['cdrom'])
        port = output.port
        protocol = output.scheme
        hostname = output.hostname
        url_path = output.path

        if port is None:
            port = socket.getservbyname(protocol)

        url = self.info['cdrom']
        if not qemu_stream_dns:
            hostname = socket.gethostbyname(hostname)
            url = protocol + "://" + hostname + ":" + str(port) + url_path

        if not libvirt_stream:
            return qemu_stream_cmdline % {'url': url, 'bus': bus}

        params = {'protocol': protocol, 'url_path': url_path,
                  'hostname': hostname, 'port': port, 'dev': dev, 'bus': bus}

        return network_file % (params)

    def _get_disks_xml(self, vm_uuid):
        storage_path = self._get_storage_path()
        ret = ""
        for i, disk in enumerate(self.info['disks']):
            index = disk.get('index', i)
            volume = "%s-%s.img" % (vm_uuid, index)
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

    def _get_graphics_xml(self, params):
        graphics_xml = """
            <graphics type='%(type)s' autoport='yes' listen='%(listen)s'>
            </graphics>
        """
        spicevmc_xml = """
            <channel type='spicevmc'>
              <target type='virtio' name='com.redhat.spice.0'/>
            </channel>
        """
        graphics = dict(self.info['graphics'])
        if params:
            graphics.update(params)
        graphics_xml = graphics_xml % graphics
        if graphics['type'] == 'spice':
            graphics_xml = graphics_xml + spicevmc_xml
        return graphics_xml

    def to_volume_list(self, vm_uuid):
        storage_path = self._get_storage_path()
        ret = []
        for i, d in enumerate(self.info['disks']):
            index = d.get('index', i)
            volume = "%s-%s.img" % (vm_uuid, index)

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

    def _get_networks_xml(self):
        network = """
            <interface type='network'>
              <source network='%(network)s'/>
              <model type='%(nic_model)s'/>
            </interface>
        """
        networks = ""
        net_info = {"nic_model": self.info['nic_model']}
        for nw in self.info['networks']:
            net_info['network'] = nw
            networks += network % net_info
        return networks

    def to_vm_xml(self, vm_name, vm_uuid, **kwargs):
        params = dict(self.info)
        params['name'] = vm_name
        params['uuid'] = vm_uuid
        params['disks'] = self._get_disks_xml(vm_uuid)
        params['networks'] = self._get_networks_xml()
        params['qemu-namespace'] = ''
        params['cdroms'] = ''
        params['qemu-stream-cmdline'] = ''
        graphics = kwargs.get('graphics')
        params['graphics'] = self._get_graphics_xml(graphics)

        qemu_stream_dns = kwargs.get('qemu_stream_dns', False)
        libvirt_stream = kwargs.get('libvirt_stream', False)
        cdrom_xml = self._get_cdrom_xml(libvirt_stream, qemu_stream_dns)
        if not libvirt_stream and params.get('iso_stream', False):
            params['qemu-namespace'] = QEMU_NAMESPACE
            params['qemu-stream-cmdline'] = cdrom_xml
        else:
            params['cdroms'] = cdrom_xml

        xml = """
        <domain type='%(domain)s' %(qemu-namespace)s>
          %(qemu-stream-cmdline)s
          <name>%(name)s</name>
          <uuid>%(uuid)s</uuid>
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
            %(networks)s
            %(graphics)s
            <sound model='ich6' />
            <memballoon model='virtio' />
          </devices>
        </domain>
        """ % params
        return xml

    def validate(self):
        self._storage_validate()
        self._network_validate()
        self._iso_validate()

    def _iso_validate(self):
        pass

    def _network_validate(self):
        pass

    def _storage_validate(self):
        pass

    def fork_vm_storage(self, vm_uuid):
        pass

    def _get_storage_path(self):
        return ''
