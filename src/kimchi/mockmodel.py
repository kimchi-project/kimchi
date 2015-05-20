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

import libvirt
import lxml.etree as ET
import os
import random
import time

import kimchi.model.cpuinfo

from lxml import objectify
from lxml.builder import E

from kimchi import config
from kimchi import imageinfo
from kimchi import osinfo
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.model.debugreports import DebugReportsModel
from kimchi.model.host import DeviceModel
from kimchi.model.libvirtstoragepool import IscsiPoolDef, NetfsPoolDef
from kimchi.model.libvirtstoragepool import StoragePoolDef
from kimchi.model.model import Model
from kimchi.model.storagepools import StoragePoolModel
from kimchi.model.storagevolumes import StorageVolumeModel, StorageVolumesModel
from kimchi.model.templates import LibvirtVMTemplate
from kimchi.model.users import PAMUsersModel
from kimchi.model.groups import PAMGroupsModel
from kimchi.objectstore import ObjectStore
from kimchi.utils import add_task, get_next_clone_name, kimchi_log
from kimchi.vmtemplate import VMTemplate
from kimchi.xmlutils.utils import xml_item_update


fake_user = {'root': 'letmein!'}
mockmodel_defaults = {'storagepool': '/storagepools/default-pool',
                      'domain': 'test', 'arch': 'i686'}


class MockModel(Model):
    _mock_vms = {}
    _mock_snapshots = {}
    _XMLDesc = libvirt.virDomain.XMLDesc
    _defineXML = libvirt.virConnect.defineXML
    _undefineDomain = libvirt.virDomain.undefine
    _libvirt_get_vol_path = LibvirtVMTemplate._get_volume_path

    def __init__(self, objstore_loc=None):
        # Override osinfo.defaults to ajust the values according to
        # test:///default driver
        defaults = dict(osinfo.defaults)
        defaults.update(mockmodel_defaults)
        osinfo.defaults = dict(defaults)

        self._mock_devices = MockDevices()
        self._mock_partitions = MockPartitions()
        self._mock_storagevolumes = MockStorageVolumes()
        self._mock_swupdate = MockSoftwareUpdate()
        self._mock_repositories = MockRepositories()

        kimchi.model.cpuinfo.get_topo_capabilities = \
            MockModel.get_topo_capabilities
        libvirt.virConnect.defineXML = MockModel.domainDefineXML
        libvirt.virDomain.XMLDesc = MockModel.domainXMLDesc
        libvirt.virDomain.undefine = MockModel.undefineDomain
        libvirt.virDomain.attachDeviceFlags = MockModel.attachDeviceFlags
        libvirt.virDomain.detachDeviceFlags = MockModel.detachDeviceFlags
        libvirt.virDomain.updateDeviceFlags = MockModel.updateDeviceFlags
        libvirt.virStorageVol.resize = MockModel.volResize
        libvirt.virStorageVol.wipePattern = MockModel.volWipePattern

        IscsiPoolDef.prepare = NetfsPoolDef.prepare = StoragePoolDef.prepare

        PAMUsersModel.auth_type = 'fake'
        PAMGroupsModel.auth_type = 'fake'

        super(MockModel, self).__init__('test:///default', objstore_loc)
        self.objstore_loc = objstore_loc
        self.objstore = ObjectStore(objstore_loc)

        # The MockModel methods are instantiated on runtime according to Model
        # and BaseModel
        # Because that a normal method override will not work here
        # Instead of that we also need to do the override on runtime
        for method in dir(self):
            if method.startswith('_mock_'):
                mock_method = getattr(self, method)
                if not callable(mock_method):
                    continue

                m = method[6:]
                model_method = getattr(self, m)
                setattr(self, '_model_' + m, model_method)
                setattr(self, m, mock_method)

        DeviceModel.lookup = self._mock_device_lookup
        StoragePoolModel._update_lvm_disks = self._update_lvm_disks
        StorageVolumesModel.get_list = self._mock_storagevolumes_get_list
        StorageVolumeModel.doUpload = self._mock_storagevolume_doUpload
        DebugReportsModel._gen_debugreport_file = self._gen_debugreport_file
        LibvirtVMTemplate._get_volume_path = self._get_volume_path
        VMTemplate.get_iso_info = self._probe_image
        imageinfo.probe_image = self._probe_image

    def reset(self):
        MockModel._mock_vms = {}
        MockModel._mock_snapshots = {}
        self._mock_swupdate = MockSoftwareUpdate()
        self._mock_repositories = MockRepositories()

        if hasattr(self, 'objstore'):
            self.objstore = ObjectStore(self.objstore_loc)

        params = {'vms': [u'test'], 'templates': [],
                  'networks': [u'default'], 'storagepools': [u'default-pool']}

        for res, items in params.iteritems():
            resources = getattr(self, '%s_get_list' % res)()
            for i in resources:
                if i in items:
                    continue

                try:
                    getattr(self, '%s_deactivate' % res[:-1])(i)
                except:
                    pass

                getattr(self, '%s_delete' % res[:-1])(i)

        volumes = self.storagevolumes_get_list('default-pool')
        for v in volumes:
            self.storagevolume_delete('default-pool', v)

    @staticmethod
    def get_topo_capabilities(conn):
        # The libvirt test driver doesn't return topology.
        xml = "<topology sockets='1' cores='2' threads='2'/>"
        return ET.fromstring(xml)

    @staticmethod
    def domainDefineXML(conn, xml):
        name = objectify.fromstring(xml).name.text
        try:
            dom = conn.lookupByName(name)
            if not dom.isActive():
                MockModel._mock_vms[name] = xml
        except:
            pass

        return MockModel._defineXML(conn, xml)

    @staticmethod
    def domainXMLDesc(dom, flags=0):
        return MockModel._mock_vms.get(dom.name(),
                                       MockModel._XMLDesc(dom, flags))

    @staticmethod
    def undefineDomain(dom):
        name = dom.name()
        if name in MockModel._mock_vms.keys():
            del MockModel._mock_vms[dom.name()]
        return MockModel._undefineDomain(dom)

    @staticmethod
    def attachDeviceFlags(dom, xml, flags=0):
        old_xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        root = objectify.fromstring(old_xml)
        dev = objectify.fromstring(xml)
        root.devices.append(dev)

        MockModel._mock_vms[dom.name()] = ET.tostring(root, encoding="utf-8")

    @staticmethod
    def _get_device_node(dom, xml):
        xpath_map = {'disk': 'target',
                     'interface': 'mac',
                     'graphics': 'listen'}

        dev = objectify.fromstring(xml)
        dev_id = dev.find(xpath_map[dev.tag]).items()

        dev_filter = ''
        for key, value in dev_id:
            dev_filter += "[@%s='%s']" % (key, value)

        old_xml = dom.XMLDesc(libvirt.VIR_DOMAIN_XML_SECURE)
        root = objectify.fromstring(old_xml)
        devices = root.devices

        dev = devices.find("./%s/%s%s/.." % (dev.tag, xpath_map[dev.tag],
                                             dev_filter))

        return (root, dev)

    @staticmethod
    def detachDeviceFlags(dom, xml, flags=0):
        root, dev = MockModel._get_device_node(dom, xml)
        root.devices.remove(dev)

        MockModel._mock_vms[dom.name()] = ET.tostring(root, encoding="utf-8")

    @staticmethod
    def updateDeviceFlags(dom, xml, flags=0):
        root, old_dev = MockModel._get_device_node(dom, xml)
        root.devices.replace(old_dev, objectify.fromstring(xml))
        MockModel._mock_vms[dom.name()] = ET.tostring(root, encoding="utf-8")

    @staticmethod
    def volResize(vol, size, flags=0):
        new_xml = xml_item_update(vol.XMLDesc(0), './capacity', str(size))
        vol.delete(0)
        pool = vol.storagePoolLookupByVolume()
        pool.createXML(new_xml)

    @staticmethod
    def volWipePattern(vol, algorithm, flags=0):
        new_xml = xml_item_update(vol.XMLDesc(0), './allocation', '0')
        vol.delete(0)
        pool = vol.storagePoolLookupByVolume()
        pool.createXML(new_xml)

    def _probe_image(self, path):
        return ('unknown', 'unknown')

    def _get_volume_path(self, pool, vol):
        pool_info = self.storagepool_lookup(pool)
        if pool_info['type'] == 'scsi':
            return self._mock_storagevolumes.scsi_volumes[vol]['path']

        return MockModel._libvirt_get_vol_path(pool, vol)

    def _gen_debugreport_file(self, name):
        return add_task('/debugreports/%s' % name, self._create_log,
                        self.objstore, name)

    def _create_log(self, cb, name):
        path = config.get_debugreports_path()
        tmpf = os.path.join(path, name + '.tmp')
        realf = os.path.join(path, name + '.txt')
        length = random.randint(1000, 10000)
        with open(tmpf, 'w') as fd:
            while length:
                fd.write('I am logged')
                length = length - 1
        os.rename(tmpf, realf)
        cb("OK", True)

    def _update_lvm_disks(self, pool_name, disks):
        conn = self.conn.get()
        pool = conn.storagePoolLookupByName(pool_name.encode('utf-8'))
        xml = pool.XMLDesc(0)

        root = ET.fromstring(xml)
        source = root.xpath('./source')[0]

        for d in disks:
            dev = E.device(path=d)
            source.append(dev)

        conn.storagePoolDefineXML(ET.tostring(root), 0)

    def _mock_host_shutdown(self, *name):
        kimchi_log.info("The host system will be shutted down")

    def _mock_host_reboot(self, *name):
        kimchi_log.info("The host system will be rebooted")

    def _mock_storagevolumes_create(self, pool, params):
        vol_source = ['url', 'capacity']
        index_list = list(i for i in range(len(vol_source))
                          if vol_source[i] in params)
        create_param = vol_source[index_list[0]]
        name = params.get('name')
        if name is None and create_param == 'url':
            params['name'] = os.path.basename(params['url'])
            del params['url']
            params['capacity'] = 1024

        return self._model_storagevolumes_create(pool, params)

    def _mock_storagevolumes_get_list(self, pool):
        pool_info = self.storagepool_lookup(pool)
        if pool_info['type'] == 'scsi':
            return self._mock_storagevolumes.scsi_volumes.keys()

        return self._model_storagevolumes_get_list(pool)

    def _mock_storagevolume_lookup(self, pool, vol):
        pool_info = self.storagepool_lookup(pool)
        if pool_info['type'] == 'scsi':
            return self._mock_storagevolumes.scsi_volumes[vol]

        return self._model_storagevolume_lookup(pool, vol)

    def _mock_storagevolume_doUpload(self, cb, vol, offset, data, data_size):
        vol_path = vol.path()

        # MockModel does not create the storage volume as a file
        # So create it to do the file upload
        if offset == 0:
            dirname = os.path.dirname(vol_path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            open(vol_path, 'w').close()

        try:
            with open(vol_path, 'a') as fd:
                fd.seek(offset)
                fd.write(data)
        except Exception, e:
            os.remove(vol_path)
            cb('', False)
            raise OperationFailed("KCHVOL0029E", {"err": e.message})

    def _mock_partitions_get_list(self):
        return self._mock_partitions.partitions.keys()

    def _mock_partition_lookup(self, name):
        return self._mock_partitions.partitions[name]

    def _mock_devices_get_list(self, _cap=None, _passthrough=None,
                               _passthrough_affected_by=None):
        if _cap is None:
            return self._mock_devices.devices.keys()

        if _cap == 'fc_host':
            _cap = 'scsi_host'

        return [dev['name'] for dev in self._mock_devices.devices.values()
                if dev['device_type'] == _cap]

    def _mock_device_lookup(self, dev_name):
        return self._mock_devices.devices[dev_name]

    def _mock_packagesupdate_get_list(self):
        return self._mock_swupdate.pkgs.keys()

    def _mock_packageupdate_lookup(self, pkg_name):
        return self._mock_swupdate.pkgs[pkg_name]

    def _mock_host_swupdate(self, args=None):
        task_id = add_task('/host/swupdate', self._mock_swupdate.doUpdate,
                           self.objstore)
        return self.task_lookup(task_id)

    def _mock_repositories_get_list(self):
        return self._mock_repositories.repos.keys()

    def _mock_repositories_create(self, params):
        # Create a repo_id if not given by user. The repo_id will follow
        # the format kimchi_repo_<integer>, where integer is the number of
        # seconds since the Epoch (January 1st, 1970), in UTC.
        repo_id = params.get('repo_id', None)
        if repo_id is None:
            repo_id = "kimchi_repo_%s" % str(int(time.time() * 1000))
            params.update({'repo_id': repo_id})

        config = params.get('config', {})
        info = {'repo_id': repo_id,
                'baseurl': params['baseurl'],
                'enabled': True,
                'config': {'repo_name': config.get('repo_name', repo_id),
                           'gpgkey': config.get('gpgkey', []),
                           'gpgcheck': True,
                           'mirrorlist': params.get('mirrorlist', '')}}
        self._mock_repositories.repos[repo_id] = info
        return repo_id

    def _mock_repository_lookup(self, repo_id):
        return self._mock_repositories.repos[repo_id]

    def _mock_repository_delete(self, repo_id):
        del self._mock_repositories.repos[repo_id]

    def _mock_repository_enable(self, repo_id):
        self._mock_repositories.repos[repo_id]['enabled'] = True

    def _mock_repository_disable(self, repo_id):
        self._mock_repositories.repos[repo_id]['enabled'] = False

    def _mock_repository_update(self, repo_id, params):
        self._mock_repositories.repos[repo_id].update(params)
        return repo_id

    def _mock_vm_clone(self, name):
        new_name = get_next_clone_name(self.vms_get_list(), name)
        snapshots = MockModel._mock_snapshots.get(name, [])
        MockModel._mock_snapshots[new_name] = snapshots
        return self._model_vm_clone(name)

    def _mock_vmsnapshots_create(self, vm_name, params):
        name = params.get('name', unicode(int(time.time())))
        params = {'vm_name': vm_name, 'name': name}
        taskid = add_task(u'/vms/%s/snapshots/%s' % (vm_name, name),
                          self._vmsnapshots_create_task, self.objstore, params)
        return self.task_lookup(taskid)

    def _vmsnapshots_create_task(self, cb, params):
        vm_name = params['vm_name']
        name = params['name']
        parent = u''

        snapshots = MockModel._mock_snapshots.get(vm_name, [])
        for sn in snapshots:
            if sn.current:
                sn.current = False
                parent = sn.name

        snapshots.append(MockVMSnapshot(name, {'parent': parent}))
        MockModel._mock_snapshots[vm_name] = snapshots

        cb('OK', True)

    def _mock_vmsnapshots_get_list(self, vm_name):
        snapshots = MockModel._mock_snapshots.get(vm_name, [])
        return sorted([snap.name for snap in snapshots])

    def _mock_currentvmsnapshot_lookup(self, vm_name):
        for sn in MockModel._mock_snapshots.get(vm_name, []):
            if sn.current:
                return sn.info

    def _mock_vmsnapshot_lookup(self, vm_name, name):
        for sn in MockModel._mock_snapshots.get(vm_name, []):
            if sn.name == name:
                return sn.info

        raise NotFoundError('KCHSNAP0003E', {'name': name, 'vm': vm_name})

    def _mock_vmsnapshot_delete(self, vm_name, name):
        snapshots = MockModel._mock_snapshots.get(vm_name, [])
        for sn in snapshots:
            if sn.name == name:
                del snapshots[snapshots.index(sn)]

        MockModel._mock_snapshots[vm_name] = snapshots

    def _mock_vmsnapshot_revert(self, vm_name, name):
        snapshots = MockModel._mock_snapshots.get(vm_name, [])
        for sn in snapshots:
            if sn.current:
                sn.current = False

        for sn in snapshots:
            if sn.name == name:
                sn.current = True


class MockStorageVolumes(object):
    def __init__(self):
        base_path = "/dev/disk/by-path/pci-0000:0e:00.0-fc-0x20-lun"
        self.scsi_volumes = {'unit:0:0:1': {'capacity': 1024,
                                            'format': 'unknown',
                                            'allocation': 512,
                                            'type': 'block',
                                            'path': base_path + '1',
                                            'used_by': []},
                             'unit:0:0:2': {'capacity': 2048,
                                            'format': 'unknown',
                                            'allocation': 512,
                                            'type': 'block',
                                            'path': base_path + '2',
                                            'used_by': []}}


class MockPartitions(object):
    def __init__(self):
        self.partitions = {"vdx": {"available": True, "name": "vdx",
                                   "fstype": "", "path": "/dev/vdx",
                                   "mountpoint": "", "type": "disk",
                                   "size": "2147483648"},
                           "vdz": {"available": True, "name": "vdz",
                                   "fstype": "", "path": "/dev/vdz",
                                   "mountpoint": "", "type": "disk",
                                   "size": "2147483648"}}


class MockDevices(object):
    def __init__(self):
        self.devices = {
            'computer': {'device_type': 'system',
                         'firmware': {'release_date': '01/01/2012',
                                      'vendor': 'LENOVO',
                                      'version': 'XXXXX (X.XX )'},
                         'hardware': {'serial': 'PXXXXX',
                                      'uuid':
                                      '9d660370-820f-4241-8731-5a60c97e8aa6',
                                      'vendor': 'LENOVO',
                                      'version': 'ThinkPad T420'},
                         'name': 'computer',
                         'parent': None,
                         'product': '4180XXX'},
            'pci_0000_03_00_0': {'bus': 3,
                                 'device_type': 'pci',
                                 'domain': 0,
                                 'driver': {'name': 'iwlwifi'},
                                 'function': 0,
                                 'iommuGroup': 7,
                                 'name': 'pci_0000_03_00_0',
                                 'parent': 'computer',
                                 'path':
                                 '/sys/devices/pci0000:00/0000:03:00.0',
                                 'product': {
                                     'description':
                                     'Centrino Advanced-N 6205 [Taylor Peak]',
                                     'id': '0x0085'},
                                 'slot': 0,
                                 'vendor': {'description': 'Intel Corporation',
                                            'id': '0x8086'}},
            'pci_0000_0d_00_0': {'bus': 13,
                                 'device_type': 'pci',
                                 'domain': 0,
                                 'driver': {'name': 'sdhci-pci'},
                                 'function': 0,
                                 'iommuGroup': 7,
                                 'name': 'pci_0000_0d_00_0',
                                 'parent': 'computer',
                                 'path':
                                 '/sys/devices/pci0000:00/0000:0d:00.0',
                                 'product': {'description':
                                             'PCIe SDXC/MMC Host Controller',
                                             'id': '0xe823'},
                                 'slot': 0,
                                 'vendor': {'description': 'Ricoh Co Ltd',
                                            'id': '0x1180'}},
            'scsi_host0': {'adapter': {'fabric_wwn': '37df6c1efa1b4388',
                                       'type': 'fc_host',
                                       'wwnn': 'efb6563f06434a98',
                                       'wwpn': '742f32073aab45d7'},
                           'device_type': 'scsi_host',
                           'host': 0,
                           'name': 'scsi_host0',
                           'parent': 'computer',
                           'path': '/sys/devices/pci0000:00/0000:40:00.0/0'},
            'scsi_host1': {'adapter': {'fabric_wwn': '542efa5dced34123',
                                       'type': 'fc_host',
                                       'wwnn': 'b7433a40c9b84092',
                                       'wwpn': '25c1f485ae42497f'},
                           'device_type': 'scsi_host',
                           'host': 0,
                           'name': 'scsi_host1',
                           'parent': 'computer',
                           'path': '/sys/devices/pci0000:00/0000:40:00.0/1'},
            'scsi_host2': {'adapter': {'fabric_wwn': '5c373c334c20478d',
                                       'type': 'fc_host',
                                       'wwnn': 'f2030bec4a254e6b',
                                       'wwpn': '07dbca4164d44096'},
                           'device_type': 'scsi_host',
                           'host': 0,
                           'name': 'scsi_host2',
                           'parent': 'computer',
                           'path': '/sys/devices/pci0000:00/0000:40:00.0/2'}}


class MockSoftwareUpdate(object):
    def __init__(self):
        self.pkgs = {
            'udevmountd': {'repository': 'openSUSE-13.1-Update',
                           'version': '0.81.5-14.1',
                           'arch': 'x86_64',
                           'package_name': 'udevmountd'},
            'sysconfig-network': {'repository': 'openSUSE-13.1-Extras',
                                  'version': '0.81.5-14.1',
                                  'arch': 'x86_64',
                                  'package_name': 'sysconfig-network'},
            'libzypp': {'repository': 'openSUSE-13.1-Update',
                        'version': '13.9.0-10.1',
                        'arch': 'noarch',
                        'package_name': 'libzypp'}}
        self._num2update = 3

    def doUpdate(self, cb, params):
        msgs = []
        for pkg in self.pkgs.keys():
            msgs.append("Updating package %s" % pkg)
            cb('\n'.join(msgs))
            time.sleep(1)

        time.sleep(2)
        msgs.append("All packages updated")
        cb('\n'.join(msgs), True)

        # After updating all packages any package should be listed to be
        # updated, so reset self._packages
        self.pkgs = {}


class MockRepositories(object):
    def __init__(self):
        self.repos = {"kimchi_repo_1392167832":
                      {"repo_id": "kimchi_repo_1392167832",
                       "enabled": True,
                       "baseurl": "http://www.fedora.org",
                       "config": {"repo_name": "kimchi_repo_1392167832",
                                  "gpgkey": [],
                                  "gpgcheck": True,
                                  "mirrorlist": ""}}}


class MockVMSnapshot(object):
    def __init__(self, name, params={}):
        self.name = name
        self.current = True

        self.info = {'created': params.get('created',
                                           unicode(int(time.time()))),
                     'name': name,
                     'parent': params.get('parent', u''),
                     'state': params.get('state', u'shutoff')}
