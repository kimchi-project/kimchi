#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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

from wok.exception import InvalidParameter, ImageFormatError, IsoFormatError
from wok.exception import MissingParameter, OperationFailed

from wok.plugins.kimchi import imageinfo
from wok.plugins.kimchi import osinfo
from wok.plugins.kimchi.isoinfo import IsoImage
from wok.plugins.kimchi.utils import check_url_path, is_s390x
from wok.plugins.kimchi.utils import pool_name_from_uri
from wok.plugins.kimchi.xmlutils.bootorder import get_bootorder_xml
from wok.plugins.kimchi.xmlutils.cpu import get_cpu_xml
from wok.plugins.kimchi.xmlutils.disk import get_disk_xml
from wok.plugins.kimchi.xmlutils.graphics import get_graphics_xml
from wok.plugins.kimchi.xmlutils.interface import get_iface_xml
from wok.plugins.kimchi.xmlutils.qemucmdline import get_qemucmdline_xml
from wok.plugins.kimchi.xmlutils.serial import get_serial_xml


class VMTemplate(object):

    def __init__(self, args, scan=False, netboot=False):
        """
        Construct a VM Template from a widely variable amount of information.
        The only required parameter is a name for the VMTemplate.  If present,
        the os_distro and os_version fields are used to lookup recommended
        settings.  Any parameters provided by the caller will override the
        defaults.  If scan is True and a cdrom or a base img is present, the
        operating system will be detected by probing the installation media.
        If netboot is True, no cdrom or base img will be used to boot the VM.
        """
        self.info = {}
        self.fc_host_support = args.get('fc_host_support')

        # Fetch defaults based on the os distro and version
        if netboot:
            distro = version = 'unknown'
        else:
            try:
                distro, version = self._get_os_info(args, scan)
            except ImageFormatError as e:
                raise OperationFailed('KCHTMPL0020E', {'err': e.message})

        os_distro = args.get('os_distro', distro)
        os_version = args.get('os_version', version)
        entry = osinfo.lookup(os_distro, os_version)
        self.info.update(entry)

        # Auto-generate a template name if no one is passed
        if 'name' not in args or args['name'] == '':
            args['name'] = self._gen_name(distro, version)
        self.name = args['name']

        # Merge graphics settings
        graph_args = args.get('graphics')
        if graph_args:
            graphics = dict(self.info['graphics'])
            graphics.update(graph_args)
            args['graphics'] = graphics

        default_disk = self.info['disks'][0]

        # Complete memory args, because dict method update is not recursive
        if 'memory' in args:
            if 'current' not in args['memory']:
                args['memory']['current'] = self.info['memory']['current']
            if 'maxmemory' not in args['memory']:
                args['memory']['maxmemory'] = self.info['memory']['maxmemory']

        # Override template values according to 'args'
        self.info.update(args)
        disks = self.info.get('disks')

        basic_disk = ['index', 'format', 'pool', 'size']
        basic_path_disk = ['index', 'format', 'path', 'size']
        ro_disk = ['index', 'format', 'pool', 'volume']
        base_disk = ['index', 'base', 'pool', 'size', 'format']
        base_path_disk = ['index', 'base', 'path', 'size', 'format']

        for index, disk in enumerate(disks):
            disk_info = dict(default_disk)
            # on s390x/s390 either pool or path should be present in
            # default disk.
            if is_s390x() and 'pool' not in default_disk and \
               'path' not in default_disk:
                raise InvalidParameter('KCHTMPL0040E')

            # On s390x/s390 pool is optional attribute for disk.
            pool = disk.get('pool', default_disk.get('pool'))

            if pool:
                pool_type = self._get_storage_type(pool['name'])
                if pool_type in ['iscsi', 'scsi']:
                    disk_info = {'index': 0, 'format': 'raw', 'volume': None}

                # This check is required where 'pool' disk
                # has to be added and hence default path
                # has to be removed during template update.
                if 'path' in disk_info:
                    del disk_info['path']

                disk_info.update(disk)
                pool_name = disk_info.get('pool', {}).get('name')
                if pool_name is None:
                    raise MissingParameter('KCHTMPL0028E')

                keys = sorted(disk_info.keys())

                if ((keys != sorted(basic_disk)) and
                        (keys != sorted(ro_disk)) and
                        (keys != sorted(base_disk))):
                    # Addition check required only on s390x
                    if not is_s390x() or (keys != sorted(basic_path_disk)):
                        raise MissingParameter('KCHTMPL0028E')

                if pool_type in ['logical', 'iscsi', 'scsi']:
                    if disk_info['format'] != 'raw':
                        raise InvalidParameter('KCHTMPL0029E')

                disk_info['pool']['type'] = pool_type
                disk_info['index'] = disk_info.get('index', index)
                self.info['disks'][index] = disk_info
            elif is_s390x():
                # For now support 'path' only on s390x
                path = disk.get('path', default_disk.get('path'))
                disk_info.update(disk)
                keys = sorted(disk_info.keys())
                if ((keys != sorted(basic_path_disk)) and
                   (keys != sorted(base_path_disk))):
                    raise MissingParameter('KCHTMPL0042E')

                disk_info['path'] = path
                disk_info['index'] = disk_info.get('index', index)
                self.info['disks'][index] = disk_info

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
            return None

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
        base_disk_params = {'type': 'disk', 'disk': 'file',
                            'bus': self.info['disk_bus']}
        logical_disk_params = {'format': 'raw'}
        iscsi_disk_params = {'disk': 'block', 'format': 'raw'}

        scsi_disk = 'volume' if self.fc_host_support else 'block'
        scsi_disk_params = {'disk': scsi_disk, 'type': 'lun',
                            'format': 'raw', 'bus': 'scsi'}

        disks_xml = ''
        for index, disk in enumerate(self.info['disks']):
            params = dict(base_disk_params)
            params['format'] = disk['format']
            params['index'] = index
            if disk.get('pool'):
                params.update(locals().get('%s_disk_params' %
                                           disk['pool']['type'], {}))

            volume = disk.get('volume')
            if volume is not None:
                params['path'] = self._get_volume_path(disk['pool']['name'],
                                                       volume)
            else:
                img = "%s-%s.img" % (vm_uuid, params['index'])
                if disk.get('pool'):
                    storage_path = self._get_storage_path(disk['pool']['name'])
                    params['pool_type'] = disk['pool']['type']
                elif disk.get('path'):
                    storage_path = disk.get('path')
                    params['pool_type'] = None
                params['path'] = os.path.join(storage_path, img)
            disks_xml += get_disk_xml(params)[1]

        return unicode(disks_xml, 'utf-8')

    def to_volume_list(self, vm_uuid):
        ret = []
        for i, d in enumerate(self.info['disks']):
            # Create only .img. If storagepool is (i)SCSI, volumes will be LUNs
            if 'pool' in d and d['pool']['type'] in ["iscsi", "scsi"]:
                continue

            index = d.get('index', i)
            volume = "%s-%s.img" % (vm_uuid, index)

            if 'path' in d:
                storage_path = d['path']
            else:
                storage_path = self._get_storage_path(d['pool']['name'])

            info = {'name': volume,
                    'capacity': d['size'],
                    'format': d['format'],
                    'path': '%s/%s' % (storage_path, volume),
                    'pool': d['pool']['name'] if 'pool' in d else None}

            if ('pool' in d and 'logical' == d['pool']['type']) or \
               info['format'] not in ['qcow2', 'raw']:
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

            target_fmt = info['format']
            if 'base' in d:
                # target must be qcow2 in order to use a backing file
                target_fmt = 'qcow2'

                v_tree.append(E.backingStore(
                    E.path(info['base']['path']),
                    E.format(type=info['base']['format'])))

            target = E.target(
                E.format(type=target_fmt), E.path(info['path']))
            v_tree.append(target)
            info['xml'] = etree.tostring(v_tree)
            ret.append(info)
        return ret

    def _get_networks_xml(self):
        networks = ""
        params = {'type': 'network',
                  'model': self.info['nic_model']}

        info_networks = self.info.get('networks', [])

        for nw in info_networks:
            params['network'] = nw
            networks += get_iface_xml(params, self.info['arch'],
                                      self.info['os_distro'],
                                      self.info['os_version'])
        return unicode(networks, 'utf-8')

    def _get_interfaces_xml(self):
        interfaces = ""
        params = {'model': self.info['nic_model']}
        for interface in self.info.get('interfaces', []):
            typ = interface['type']
            if typ == 'macvtap':
                params['type'] = 'direct'
                params['mode'] = interface.get('mode', None)
            elif typ == 'ovs':
                params['type'] = 'bridge'
                params['virtualport_type'] = 'openvswitch'

            params['name'] = interface['name']
            interfaces += get_iface_xml(params, self.info['arch'],
                                        self.info['os_distro'],
                                        self.info['os_version'])
        return unicode(interfaces, 'utf-8')

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
        cpu_topo = self.info.get('cpu_info', {}).get('topology', {})
        return get_cpu_xml(0, (self.info.get('memory').get('current')) << 10,
                           cpu_topo)

    def to_vm_xml(self, vm_name, vm_uuid, **kwargs):
        params = dict(self.info)
        params['name'] = vm_name
        params['uuid'] = vm_uuid
        params['networks'] = self._get_networks_xml()
        params['interfaces'] = self._get_interfaces_xml()
        params['input_output'] = self._get_input_output_xml()
        params['qemu-namespace'] = ''
        params['cdroms'] = ''
        params['qemu-stream-cmdline'] = ''
        params['disks'] = self._get_disks_xml(vm_uuid)
        params['serial'] = get_serial_xml(params)
        params['title'] = kwargs.get('title', '')
        params['description'] = kwargs.get('description', '')
        graphics = dict(self.info['graphics'])
        graphics.update(kwargs.get('graphics', {}))
        # Graphics is not supported on s390x, this check will
        # not add graphics tag in domain xml.
        if params.get('arch') != 's390x':
            params['graphics'] = get_graphics_xml(graphics)

        libvirt_stream_protocols = kwargs.get('libvirt_stream_protocols', [])
        cdrom_xml = self._get_cdrom_xml(libvirt_stream_protocols)

        # Add information of CD-ROM device only if template have info about it.
        if cdrom_xml is not None:
            if not urlparse.urlparse(self.info.get('cdrom', "")).scheme in \
                    libvirt_stream_protocols and \
                    params.get('iso_stream', False):
                params['qemu-stream-cmdline'] = cdrom_xml
            else:
                params['cdroms'] = cdrom_xml

        # Set the boot order of VM
        # TODO: need modify this when boot order edition feature came upstream.
        params['boot_order'] = get_bootorder_xml()

        # Setting maximum number of memory slots
        slots = str(self.info['mem_dev_slots'])

        # Rearrange memory parameters
        memory = self.info['memory'].get('current')
        maxmemory = self.info['memory'].get('maxmemory')
        if maxmemory < memory:
            raise OperationFailed("KCHVM0041E",
                                  {'maxmem': str(maxmemory)})

        params['memory'] = self.info['memory'].get('current')
        params['max_memory'] = ""
        # if there is not support to memory hotplug in Libvirt or qemu, we
        # cannot add the tag maxMemory
        if memory != maxmemory and kwargs.get('mem_hotplug_support', True):
            maxmem_xml = "<maxMemory slots='%s' unit='MiB'>%s</maxMemory>"
            params['max_memory'] = maxmem_xml % (slots, maxmemory)

        # set a hard limit using max_memory + 1GiB
        params['hard_limit'] = maxmemory + 1024

        # vcpu element
        cpus = params['cpu_info']['vcpus']
        maxvcpus = params['cpu_info']['maxvcpus']
        params['vcpus_xml'] = "<vcpu current='%d'>%d</vcpu>" % (cpus, maxvcpus)

        # cpu_info element
        params['cpu_info_xml'] = self._get_cpu_xml()

        xml = """
        <domain type='%(domain)s'>
          %(qemu-stream-cmdline)s
          <name>%(name)s</name>
          <title>%(title)s</title>
          <description>%(description)s</description>
          <uuid>%(uuid)s</uuid>
          <memtune>
            <hard_limit unit='MiB'>%(hard_limit)s</hard_limit>
          </memtune>
          %(max_memory)s
          <memory unit='MiB'>%(memory)s</memory>
          %(vcpus_xml)s
          %(cpu_info_xml)s
          <os>
            <type arch='%(arch)s'>hvm</type>
            %(boot_order)s
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
            %(interfaces)s
            %(graphics)s
            %(input_output)s
            %(serial)s
            <memballoon model='virtio' />
          </devices>
        </domain>
        """ % params

        return xml

    def validate(self):
        for disk in self.info.get('disks'):
            if 'pool' in disk:
                pool_uri = disk.get('pool', {}).get('name')
                self._get_storage_pool(pool_uri)
        self._network_validate()
        self._iso_validate()
        self.cpuinfo_validate()
        self._validate_memory()

    def cpuinfo_validate(self):
        pass

    def _iso_validate(self):
        pass

    def _network_validate(self):
        pass

    def _get_storage_pool(self):
        pass

    def fork_vm_storage(self, vm_uuid):
        pass

    def _get_storage_path(self, pool_uri=None):
        return ''

    def _get_storage_type(self, pool=None):
        return ''

    def _get_volume_path(self):
        return ''

    def _get_all_networks_name(self):
        return []

    def _get_all_storagepools_name(self):
        return []

    def _get_active_storagepools_name(self):
        return []

    def validate_integrity(self):
        invalid = {}
        # validate networks integrity
        networks = self.info.get('networks', [])

        invalid_networks = list(set(networks) -
                                set(self._get_all_networks_name()))
        if invalid_networks:
            invalid['networks'] = invalid_networks

        # validate storagepools and image-based templates integrity
        for disk in self.info['disks']:
            if 'pool' in disk:
                pool_uri = disk['pool']['name']
                pool_name = pool_name_from_uri(pool_uri)
                if pool_name not in self._get_active_storagepools_name():
                    invalid['storagepools'] = [pool_name]

            if disk.get("base") is None:
                continue

            if os.path.exists(disk.get("base")) is False:
                invalid['vm-image'] = disk["base"]

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
