#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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
import stat
import time
import urlparse
import uuid

from lxml import etree
from lxml.builder import E

from kimchi import imageinfo
from kimchi import osinfo
from kimchi.exception import InvalidParameter, IsoFormatError, MissingParameter
from kimchi.exception import ImageFormatError, OperationFailed
from kimchi.isoinfo import IsoImage
from kimchi.utils import check_url_path, pool_name_from_uri
from kimchi.xmlutils.cpu import get_cpu_xml
from kimchi.xmlutils.disk import get_disk_xml
from kimchi.xmlutils.graphics import get_graphics_xml
from kimchi.xmlutils.interface import get_iface_xml
from kimchi.xmlutils.qemucmdline import get_qemucmdline_xml


class VMTemplate(object):
    def __init__(self, args, scan=False):
        """
        Construct a VM Template from a widely variable amount of information.
        The only required parameter is a name for the VMTemplate.  If present,
        the os_distro and os_version fields are used to lookup recommended
        settings.  Any parameters provided by the caller will override the
        defaults.  If scan is True and a cdrom or a base img is present, the
        operating system will be detected by probing the installation media.
        """
        self.info = {}
        self.fc_host_support = args.get('fc_host_support')

        # Fetch defaults based on the os distro and version
        try:
            distro, version = self._get_os_info(args, scan)
        except ImageFormatError as e:
            raise OperationFailed('KCHTMPL0020E', {'err': e.message})
        os_distro = args.get('os_distro', distro)
        os_version = args.get('os_version', version)
        entry = osinfo.lookup(os_distro, os_version)
        self.info.update(entry)

        # Auto-generate a template name and no one is passed
        if 'name' not in args or args['name'] == '':
            args['name'] = self._gen_name(distro, version)
        self.name = args['name']

        # Override with the passed in parameters
        graph_args = args.get('graphics')
        if graph_args:
            graphics = dict(self.info['graphics'])
            graphics.update(graph_args)
            args['graphics'] = graphics
        self.info.update(args)

        # Assign right disk format to logical and [i]scsi storagepools
        if self._get_storage_type() in ['logical', 'iscsi', 'scsi']:
            for i, disk in enumerate(self.info['disks']):
                self.info['disks'][i]['format'] = 'raw'

    def _get_os_info(self, args, scan):
        distro = version = 'unknown'

        # Identify the cdrom if present
        iso = args.get('cdrom', '')
        if len(iso) > 0:
            if not iso.startswith('/'):
                self.info.update({'iso_stream': True})

            if scan:
                distro, version = self.get_iso_info(iso)

            return distro, version

        # CDROM is not presented: check for base image
        base_imgs = []
        for d in args.get('disks', []):
            if 'base' in d.keys():
                base_imgs.append(d)
                if scan:
                    distro, version = imageinfo.probe_image(d['base'])

                if 'size' not in d.keys():
                    d_info = imageinfo.probe_img_info(d['base'])
                    d['size'] = d_info['virtual-size']

        if len(base_imgs) == 0:
            raise MissingParameter("KCHTMPL0016E")

        return distro, version

    def _gen_name(self, distro, version):
        if distro == 'unknown':
            name = str(uuid.uuid4())
        else:
            name = distro + version + '.' + str(int(time.time() * 1000))
        return name

    def get_iso_info(self, iso):
        iso_prefixes = ['/', 'http', 'https', 'ftp', 'ftps', 'tftp']
        if len(filter(iso.startswith, iso_prefixes)) == 0:
            raise InvalidParameter("KCHTMPL0006E", {'param': iso})
        try:
            iso_img = IsoImage(iso)
            return iso_img.probe()
        except IsoFormatError:
            raise InvalidParameter("KCHISO0001E", {'filename': iso})

    def _get_cdrom_xml(self, libvirt_stream_protocols):
        if 'cdrom' not in self.info:
            return ''

        params = {}
        params['type'] = 'cdrom'
        params['format'] = 'raw'
        params['bus'] = self.info['cdrom_bus']
        params['index'] = self.info['cdrom_index']
        params['path'] = self.info['cdrom']

        if self.info.get('iso_stream', False):
            protocol = urlparse.urlparse(params['path']).scheme
            if protocol not in libvirt_stream_protocols:
                driveOpt = 'file=%(path)s,if=none,id=drive-%(bus)s0-1-0,'
                driveOpt += 'readonly=on,format=%(format)s'

                deviceOpt = '%(bus)s-cd,bus=%(bus)s.1,unit=0,'
                deviceOpt += 'drive=drive-%(bus)s0-1-0,id=%(bus)s0-1-0'

                args = {}
                args['-drive'] = driveOpt % params
                args['-device'] = deviceOpt % params
                # return qemucmdline XML
                return get_qemucmdline_xml(args)

        dev, xml = get_disk_xml(params)
        return xml

    def _get_disks_xml(self, vm_uuid):
        # Current implementation just allows to create disk in one single
        # storage pool, so we cannot mix the types (scsi volumes vs img file)
        storage_type = self._get_storage_type()
        storage_path = self._get_storage_path()

        base_disk_params = {'type': 'disk', 'disk': 'file',
                            'bus': self.info['disk_bus'], 'format': 'qcow2'}
        logical_disk_params = {'format': 'raw'}
        iscsi_disk_params = {'disk': 'block', 'format': 'raw'}

        scsi_disk = 'volume' if self.fc_host_support else 'block'
        scsi_disk_params = {'disk': scsi_disk, 'type': 'lun',
                            'format': 'raw', 'bus': 'scsi'}

        disks_xml = ''
        pool_name = pool_name_from_uri(self.info['storagepool'])
        for index, disk in enumerate(self.info['disks']):
            params = dict(base_disk_params)
            params['format'] = disk.get('format', params['format'])
            params.update(locals().get('%s_disk_params' % storage_type, {}))
            params['index'] = index

            volume = disk.get('volume')
            if volume is not None:
                params['path'] = self._get_volume_path(pool_name, volume)
            else:
                volume = "%s-%s.img" % (vm_uuid, params['index'])
                params['path'] = os.path.join(storage_path, volume)

            disks_xml += get_disk_xml(params)[1]

        return unicode(disks_xml, 'utf-8')

    def to_volume_list(self, vm_uuid):
        storage_path = self._get_storage_path()
        fmt = 'raw' if self._get_storage_type() in ['logical'] else 'qcow2'
        ret = []
        for i, d in enumerate(self.info['disks']):
            index = d.get('index', i)
            volume = "%s-%s.img" % (vm_uuid, index)

            info = {'name': volume,
                    'capacity': d['size'],
                    'format': fmt,
                    'path': '%s/%s' % (storage_path, volume)}

            if 'logical' == self._get_storage_type() or \
               fmt not in ['qcow2', 'raw']:
                info['allocation'] = info['capacity']
            else:
                info['allocation'] = 0

            if 'base' in d:
                info['base'] = dict()
                base_fmt = imageinfo.probe_img_info(d['base'])['format']
                if base_fmt is None:
                    raise InvalidParameter("KCHTMPL0024E", {'path': d['base']})
                info['base']['path'] = d['base']
                info['base']['format'] = base_fmt

            v_tree = E.volume(E.name(info['name']))
            v_tree.append(E.allocation(str(info['allocation']), unit='G'))
            v_tree.append(E.capacity(str(info['capacity']), unit='G'))
            target = E.target(
                E.format(type=info['format']), E.path(info['path']))
            if 'base' in d:
                v_tree.append(E.backingStore(
                    E.path(info['base']['path']),
                    E.format(type=info['base']['format'])))
            v_tree.append(target)
            info['xml'] = etree.tostring(v_tree)
            ret.append(info)
        return ret

    def _get_networks_xml(self):
        networks = ""
        params = {'type': 'network',
                  'model': self.info['nic_model']}
        for nw in self.info['networks']:
            params['network'] = nw
            networks += get_iface_xml(params, self.info['arch'],
                                      self.info['os_distro'],
                                      self.info['os_version'])
        return unicode(networks, 'utf-8')

    def _get_input_output_xml(self):
        sound = """
            <sound model='%(sound_model)s' />
        """
        mouse = """
            <input type='mouse' bus='%(mouse_bus)s'/>
        """

        keyboard = """
            <input type='%(kbd_type)s' bus='%(kbd_bus)s'> </input>
        """

        tablet = """
            <input type='tablet' bus='%(kbd_bus)s'> </input>
        """

        video = """
            <video>
                <model type='%(video_model)s'/>
            </video>
        """

        input_output = ""
        if 'mouse_bus' in self.info.keys():
            input_output += mouse % self.info
        if 'kbd_bus' in self.info.keys():
            input_output += keyboard % self.info
        if 'tablet_bus' in self.info.keys():
            input_output += tablet % self.info
        if 'sound_model' in self.info.keys():
            input_output += sound % self.info
        if 'video_model' in self.info.keys():
            input_output += video % self.info
        return input_output

    def _get_cpu_xml(self):
        # Include CPU topology, if provided
        cpu_info = self.info.get('cpu_info')
        if cpu_info is not None:
            cpu_topo = cpu_info.get('topology')
        return get_cpu_xml(self.info.get('cpus'),
                           self.info.get('memory') << 10,
                           cpu_topo)

    def to_vm_xml(self, vm_name, vm_uuid, **kwargs):
        params = dict(self.info)
        params['name'] = vm_name
        params['uuid'] = vm_uuid
        params['networks'] = self._get_networks_xml()
        params['input_output'] = self._get_input_output_xml()
        params['qemu-namespace'] = ''
        params['cdroms'] = ''
        params['qemu-stream-cmdline'] = ''
        params['cpu_info'] = self._get_cpu_xml()
        params['disks'] = self._get_disks_xml(vm_uuid)

        graphics = dict(self.info['graphics'])
        graphics.update(kwargs.get('graphics', {}))
        params['graphics'] = get_graphics_xml(graphics)

        libvirt_stream_protocols = kwargs.get('libvirt_stream_protocols', [])
        cdrom_xml = self._get_cdrom_xml(libvirt_stream_protocols)

        if not urlparse.urlparse(self.info.get('cdrom', "")).scheme in \
                libvirt_stream_protocols and \
                params.get('iso_stream', False):
            params['qemu-stream-cmdline'] = cdrom_xml
        else:
            params['cdroms'] = cdrom_xml

        # Setting maximum number of slots to avoid errors when hotplug memory
        # Number of slots are the numbers of chunks of 1GB that fit inside
        # the max_memory of the host minus memory assigned to the VM
        params['slots'] = ((params['max_memory'] >> 10) -
                           params['memory']) >> 10
        if params['slots'] < 0:
            raise OperationFailed("KCHVM0041E")
        elif params['slots'] == 0:
            params['slots'] = 1

        xml = """
        <domain type='%(domain)s'>
          %(qemu-stream-cmdline)s
          <name>%(name)s</name>
          <uuid>%(uuid)s</uuid>
          <maxMemory slots='%(slots)s' unit='KiB'>%(max_memory)s</maxMemory>
          <memory unit='MiB'>%(memory)s</memory>
          <vcpu>%(cpus)s</vcpu>
          %(cpu_info)s
          <os>
            <type arch='%(arch)s'>hvm</type>
            <boot dev='hd'/>
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
            %(disks)s
            %(cdroms)s
            %(networks)s
            %(graphics)s
            %(input_output)s
            <memballoon model='virtio' />
          </devices>
        </domain>
        """ % params

        # Adding PPC console configuration
        if params['arch'] in ['ppc', 'ppc64']:
            ppc_console = """<memballoon model='virtio' />
            <console type='pty'>
              <target type='serial' port='1'/>
              <address type='spapr-vio' reg='0x30001000'/>
            </console>"""
            xml = xml.replace("<memballoon model='virtio' />", ppc_console)

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

    def _get_storage_type(self):
        return ''

    def _get_volume_path(self):
        return ''

    def _get_all_networks_name(self):
        return []

    def _get_all_storagepools_name(self):
        return []

    def validate_integrity(self):
        invalid = {}
        # validate networks integrity
        invalid_networks = list(set(self.info['networks']) -
                                set(self._get_all_networks_name()))
        if invalid_networks:
            invalid['networks'] = invalid_networks

        # validate storagepools integrity
        pool_uri = self.info['storagepool']
        pool_name = pool_name_from_uri(pool_uri)
        if pool_name not in self._get_all_storagepools_name():
            invalid['storagepools'] = [pool_name]

        # validate iso integrity
        # FIXME when we support multiples cdrom devices
        iso = self.info.get('cdrom')
        if iso:
            if os.path.exists(iso):
                st_mode = os.stat(iso).st_mode
                if not (stat.S_ISREG(st_mode) or stat.S_ISBLK(st_mode)):
                    invalid['cdrom'] = [iso]
            elif not check_url_path(iso):
                invalid['cdrom'] = [iso]

        self.info['invalid'] = invalid

        return self.info
