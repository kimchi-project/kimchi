# -*- coding: utf-8 -*-
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

import grp
import os
import platform
import psutil
import pwd
import re
import shutil
import tempfile
import threading
import time
import unittest
import uuid


import iso_gen
import kimchi.objectstore
import utils
from kimchi import netinfo
from kimchi.config import paths
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.iscsi import TargetClient
from kimchi.model import model
from kimchi.rollbackcontext import RollbackContext
from kimchi.utils import add_task


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/kimchi-store-test'
        self.iso_path = '/tmp/kimchi-model-iso/'
        if not os.path.exists(self.iso_path):
            os.makedirs(self.iso_path)
        self.kimchi_iso = self.iso_path + 'ubuntu12.04.iso'
        iso_gen.construct_fake_iso(self.kimchi_iso, True, '12.04', 'ubuntu')

    def tearDown(self):
        os.unlink(self.tmp_store)
        shutil.rmtree(self.iso_path)

    def test_vm_info(self):
        inst = model.Model('test:///default', self.tmp_store)
        vms = inst.vms_get_list()
        self.assertEquals(1, len(vms))
        self.assertEquals('test', vms[0])

        keys = set(('name', 'state', 'stats', 'uuid', 'memory', 'cpus',
                    'screenshot', 'icon', 'graphics', 'users', 'groups',
                    'access', 'persistent'))

        stats_keys = set(('cpu_utilization',
                          'net_throughput', 'net_throughput_peak',
                          'io_throughput', 'io_throughput_peak'))
        info = inst.vm_lookup('test')
        self.assertEquals(keys, set(info.keys()))
        self.assertEquals('running', info['state'])
        self.assertEquals('test', info['name'])
        self.assertEquals(2048, info['memory'])
        self.assertEquals(2, info['cpus'])
        self.assertEquals(None, info['icon'])
        self.assertEquals(stats_keys, set(info['stats'].keys()))
        self.assertRaises(NotFoundError, inst.vm_lookup, 'nosuchvm')
        self.assertEquals([], info['users'])
        self.assertEquals([], info['groups'])
        self.assertTrue(info['persistent'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_lifecycle(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [], 'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm' in vms)

            inst.vm_start('kimchi-vm')
            rollback.prependDefer(inst.vm_poweroff, 'kimchi-vm')

            info = inst.vm_lookup('kimchi-vm')
            self.assertEquals('running', info['state'])

        vms = inst.vms_get_list()
        self.assertFalse('kimchi-vm' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_image_based_template(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            vol = 'base-vol.img'
            params = {'name': vol,
                      'capacity': 1024,
                      'allocation': 1,
                      'format': 'qcow2'}
            task_id = inst.storagevolumes_create('default', params)['id']
            self._wait_task(inst, task_id)
            self.assertEquals('finished', inst.task_lookup(task_id)['status'])
            vol_path = inst.storagevolume_lookup('default', vol)['path']
            rollback.prependDefer(inst.storagevolume_delete, 'default', vol)

            params = {'name': 'test', 'disks': [{'base': vol_path}]}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm' in vms)

            inst.vm_start('kimchi-vm')
            rollback.prependDefer(inst.vm_poweroff, 'kimchi-vm')

            info = inst.vm_lookup('kimchi-vm')
            self.assertEquals('running', info['state'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_graphics(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        params = {'name': 'test', 'disks': [], 'cdrom': self.kimchi_iso}
        inst.templates_create(params)
        with RollbackContext() as rollback:
            params = {'name': 'kimchi-vnc', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vnc')

            info = inst.vm_lookup('kimchi-vnc')
            self.assertEquals('vnc', info['graphics']['type'])
            self.assertEquals('127.0.0.1', info['graphics']['listen'])

            graphics = {'type': 'spice', 'listen': '127.0.0.1'}
            params = {'name': 'kimchi-spice', 'template': '/templates/test',
                      'graphics': graphics}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-spice')

            info = inst.vm_lookup('kimchi-spice')
            self.assertEquals('spice', info['graphics']['type'])
            self.assertEquals('127.0.0.1', info['graphics']['listen'])

        inst.template_delete('test')

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_ifaces(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [], 'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            params = {'name': 'kimchi-ifaces', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-ifaces')

            # Create a network
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)
            rollback.prependDefer(inst.network_delete, net_name)
            inst.network_activate(net_name)
            rollback.prependDefer(inst.network_deactivate, net_name)

            ifaces = inst.vmifaces_get_list('kimchi-ifaces')
            self.assertEquals(1, len(ifaces))

            iface = inst.vmiface_lookup('kimchi-ifaces', ifaces[0])
            self.assertEquals(17, len(iface['mac']))
            self.assertEquals("default", iface['network'])
            self.assertIn("model", iface)

            # attach network interface to vm
            iface_args = {"type": "network",
                          "network": "test-network",
                          "model": "virtio"}
            mac = inst.vmifaces_create('kimchi-ifaces', iface_args)
            self.assertEquals(17, len(mac))
            # detach network interface from vm
            rollback.prependDefer(inst.vmiface_delete, 'kimchi-ifaces', mac)

            iface = inst.vmiface_lookup('kimchi-ifaces', mac)
            self.assertEquals("network", iface["type"])
            self.assertEquals("test-network", iface['network'])
            self.assertEquals("virtio", iface["model"])

            # update vm interface
            iface_args = {"network": "default",
                          "model": "e1000"}
            inst.vmiface_update('kimchi-ifaces', mac, iface_args)
            iface = inst.vmiface_lookup('kimchi-ifaces', mac)
            self.assertEquals("default", iface['network'])
            self.assertEquals("e1000", iface["model"])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_disk(self):
        disk_path = '/tmp/existent2.iso'
        open(disk_path, 'w').close()

        def _attach_disk(expect_bus='virtio'):
            disk_args = {"type": "disk",
                         "pool": pool,
                         "vol": vol}
            disk = inst.vmstorages_create(vm_name, disk_args)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count + 1, len(storage_list))

            # Check the bus type to be 'virtio'
            disk_info = inst.vmstorage_lookup(vm_name, disk)
            self.assertEquals(u'disk', disk_info['type'])
            self.assertEquals(vol_path, disk_info['path'])
            self.assertEquals(expect_bus, disk_info['bus'])
            return disk

        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            path = '/tmp/kimchi-images'
            pool = 'test-pool'
            vol = 'test-volume.img'
            vol_path = "%s/%s" % (path, vol)
            if not os.path.exists(path):
                os.mkdir(path)

            args = {'name': pool,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, pool)

            # Activate the pool before adding any volume
            inst.storagepool_activate(pool)
            rollback.prependDefer(inst.storagepool_deactivate, pool)

            params = {'name': vol,
                      'capacity': 1024,
                      'allocation': 512,
                      'format': 'qcow2'}
            inst.storagevolumes_create(pool, params)
            rollback.prependDefer(inst.storagevolume_delete, pool, vol)

            vm_name = 'kimchi-cdrom'
            params = {'name': 'test', 'disks': [], 'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            params = {'name': vm_name, 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, vm_name)

            prev_count = len(inst.vmstorages_get_list(vm_name))
            self.assertEquals(1, prev_count)

            # Cold plug and unplug a disk
            disk = _attach_disk()
            inst.vmstorage_delete(vm_name, disk)

            # Hot plug a disk
            inst.vm_start(vm_name)
            disk = _attach_disk()

            # VM disk still there after powered off
            inst.vm_poweroff(vm_name)
            disk_info = inst.vmstorage_lookup(vm_name, disk)
            self.assertEquals(u'disk', disk_info['type'])
            inst.vmstorage_delete(vm_name, disk)

            # Specifying pool and path at same time will fail
            disk_args = {"type": "disk",
                         "pool": pool,
                         "vol": vol,
                         "path": disk_path}
            self.assertRaises(
                InvalidParameter, inst.vmstorages_create, vm_name, disk_args)

            old_distro_iso = self.iso_path + 'rhel4_8.iso'
            iso_gen.construct_fake_iso(old_distro_iso, True, '4.8', 'rhel')

            vm_name = 'kimchi-ide-bus-vm'
            params = {'name': 'old_distro_template', 'disks': [],
                      'cdrom': old_distro_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'old_distro_template')
            params = {'name': vm_name,
                      'template': '/templates/old_distro_template'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, vm_name)

            # Attach will choose IDE bus for old distro
            disk = _attach_disk('ide')
            inst.vmstorage_delete('kimchi-ide-bus-vm', disk)

            # Hot plug IDE bus disk does not work
            inst.vm_start(vm_name)
            self.assertRaises(InvalidOperation, _attach_disk)
            inst.vm_poweroff(vm_name)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_cdrom(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            vm_name = 'kimchi-cdrom'
            params = {'name': 'test', 'disks': [], 'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            params = {'name': vm_name, 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, vm_name)

            prev_count = len(inst.vmstorages_get_list(vm_name))
            self.assertEquals(1, prev_count)

            # dummy .iso files
            iso_path = '/tmp/existent.iso'
            iso_path2 = '/tmp/existent2.iso'
            open(iso_path, 'w').close()
            rollback.prependDefer(os.remove, iso_path)
            open(iso_path2, 'w').close()
            rollback.prependDefer(os.remove, iso_path2)
            wrong_iso_path = '/nonexistent.iso'

            # Create a cdrom
            cdrom_args = {"type": "cdrom",
                          "path": iso_path}
            cdrom_dev = inst.vmstorages_create(vm_name, cdrom_args)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count + 1, len(storage_list))

            # Get cdrom info
            cd_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(u'cdrom', cd_info['type'])
            self.assertEquals(iso_path, cd_info['path'])

            # create a cdrom with existing dev_name
            cdrom_args['dev'] = cdrom_dev
            self.assertRaises(OperationFailed, inst.vmstorages_create,
                              vm_name, cdrom_args)

            # update path of existing cd with
            # non existent iso
            self.assertRaises(InvalidParameter, inst.vmstorage_update,
                              vm_name, cdrom_dev, {'path': wrong_iso_path})

            # Make sure CD ROM still exists after failure
            cd_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(u'cdrom', cd_info['type'])
            self.assertEquals(iso_path, cd_info['path'])

            # update path of existing cd with existent iso of shutoff vm
            inst.vmstorage_update(vm_name, cdrom_dev, {'path': iso_path2})
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(iso_path2, cdrom_info['path'])

            # update path of existing cd with existent iso of running vm
            inst.vm_start(vm_name)
            inst.vmstorage_update(vm_name, cdrom_dev, {'path': iso_path})
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals(iso_path, cdrom_info['path'])

            # eject cdrom
            cdrom_dev = inst.vmstorage_eject(vm_name, cdrom_dev)
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            self.assertEquals('', cdrom_info['path'])
            inst.vm_poweroff(vm_name)

            # removing non existent cdrom
            self.assertRaises(NotFoundError, inst.vmstorage_delete, vm_name,
                              "fakedev")

            # removing valid cdrom
            inst.vmstorage_delete(vm_name, cdrom_dev)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count, len(storage_list))

            # Create a new cdrom using a remote iso
            valid_remote_iso_path = utils.get_remote_iso_path()
            cdrom_args = {"type": "cdrom",
                          "path": valid_remote_iso_path}
            cdrom_dev = inst.vmstorages_create(vm_name, cdrom_args)
            storage_list = inst.vmstorages_get_list(vm_name)
            self.assertEquals(prev_count + 1, len(storage_list))

            # Update remote-backed cdrom with the same ISO
            inst.vmstorage_update(vm_name, cdrom_dev,
                                  {'path': valid_remote_iso_path})
            cdrom_info = inst.vmstorage_lookup(vm_name, cdrom_dev)
            cur_cdrom_path = re.sub(":80/", '/', cdrom_info['path'])
            self.assertEquals(valid_remote_iso_path, cur_cdrom_path)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_storage_provisioning(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [{'size': 1}],
                      'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'test-vm-1', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')

            vm_info = inst.vm_lookup(params['name'])
            disk_path = '%s/%s-0.img' % (
                inst.storagepool_lookup('default')['path'], vm_info['uuid'])
            self.assertTrue(os.access(disk_path, os.F_OK))
        self.assertFalse(os.access(disk_path, os.F_OK))

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_storagepool(self):
        inst = model.Model('qemu:///system', self.tmp_store)

        poolDefs = [
            {'type': 'dir',
             'name': u'kīмсhīUnitTestDirPool',
             'path': '/tmp/kimchi-images'},
            {'type': 'iscsi',
             'name': u'kīмсhīUnitTestISCSIPool',
             'source': {'host': '127.0.0.1',
                        'target': 'iqn.2013-12.localhost.kimchiUnitTest'}}]

        for poolDef in poolDefs:
            with RollbackContext() as rollback:
                path = poolDef.get('path')
                name = poolDef['name']

                if poolDef['type'] == 'iscsi':
                    if not TargetClient(**poolDef['source']).validate():
                        continue

                pools = inst.storagepools_get_list()
                num = len(pools) + 1

                inst.storagepools_create(poolDef)
                rollback.prependDefer(inst.storagepool_delete, name)

                pools = inst.storagepools_get_list()
                self.assertEquals(num, len(pools))

                poolinfo = inst.storagepool_lookup(name)
                if path is not None:
                    self.assertEquals(path, poolinfo['path'])
                self.assertEquals('inactive', poolinfo['state'])
                if poolinfo['type'] == 'dir':
                    self.assertEquals(True, poolinfo['autostart'])
                else:
                    self.assertEquals(False, poolinfo['autostart'])

                inst.storagepool_activate(name)
                rollback.prependDefer(inst.storagepool_deactivate, name)

                poolinfo = inst.storagepool_lookup(name)
                self.assertEquals('active', poolinfo['state'])

                autostart = poolinfo['autostart']
                ori_params = {'autostart':
                              True} if autostart else {'autostart': False}
                for i in [True, False]:
                    params = {'autostart': i}
                    inst.storagepool_update(name, params)
                    rollback.prependDefer(inst.storagepool_update, name,
                                          ori_params)
                    poolinfo = inst.storagepool_lookup(name)
                    self.assertEquals(i, poolinfo['autostart'])
                inst.storagepool_update(name, ori_params)

        pools = inst.storagepools_get_list()
        self.assertIn('default', pools)
        poolinfo = inst.storagepool_lookup('default')
        self.assertEquals('active', poolinfo['state'])
        self.assertIn('ISO', pools)
        poolinfo = inst.storagepool_lookup('ISO')
        self.assertEquals('active', poolinfo['state'])
        self.assertEquals((num - 1), len(pools))

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_storagevolume(self):
        inst = model.Model('qemu:///system', self.tmp_store)

        with RollbackContext() as rollback:
            path = '/tmp/kimchi-images'
            pool = 'test-pool'
            vol = 'test-volume.img'
            if not os.path.exists(path):
                os.mkdir(path)

            args = {'name': pool,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, pool)

            self.assertRaises(InvalidOperation, inst.storagevolumes_get_list,
                              pool)
            poolinfo = inst.storagepool_lookup(pool)
            self.assertEquals(0, poolinfo['nr_volumes'])
            # Activate the pool before adding any volume
            inst.storagepool_activate(pool)
            rollback.prependDefer(inst.storagepool_deactivate, pool)

            vols = inst.storagevolumes_get_list(pool)
            num = len(vols) + 2
            params = {'capacity': 1024,
                      'allocation': 512,
                      'format': 'raw'}
            # 'name' is required for this type of volume
            self.assertRaises(InvalidParameter, inst.storagevolumes_create,
                              pool, params)
            params['name'] = vol
            task_id = inst.storagevolumes_create(pool, params)['id']
            self._wait_task(inst, task_id)
            self.assertEquals('finished', inst.task_lookup(task_id)['status'])
            rollback.prependDefer(inst.storagevolume_delete, pool, vol)

            fd, path = tempfile.mkstemp(dir=path)
            name = os.path.basename(path)
            rollback.prependDefer(inst.storagevolume_delete, pool, name)
            vols = inst.storagevolumes_get_list(pool)
            self.assertIn(name, vols)
            self.assertEquals(num, len(vols))

            inst.storagevolume_wipe(pool, vol)
            volinfo = inst.storagevolume_lookup(pool, vol)
            self.assertEquals(0, volinfo['allocation'])
            self.assertEquals(0, volinfo['ref_cnt'])

            volinfo = inst.storagevolume_lookup(pool, vol)
            # Define the size = capacity + 16M
            capacity = volinfo['capacity'] >> 20
            size = capacity + 16
            inst.storagevolume_resize(pool, vol, size)

            volinfo = inst.storagevolume_lookup(pool, vol)
            self.assertEquals((1024 + 16) << 20, volinfo['capacity'])
            poolinfo = inst.storagepool_lookup(pool)
            self.assertEquals(len(vols), poolinfo['nr_volumes'])

            # download remote volume
            # 1) try an invalid URL
            params = {'url': 'http://www.invalid.url'}
            taskid = inst.storagevolumes_create(pool, params)['id']
            self._wait_task(inst, taskid)
            self.assertEquals('failed', inst.task_lookup(taskid)['status'])
            # 2) download Kimchi's "COPYING" from Github and compare its
            #    content to the corresponding local file's
            url = 'https://github.com/kimchi-project/kimchi/raw/master/COPYING'
            params = {'url': url}
            task_response = inst.storagevolumes_create(pool, params)
            taskid = task_response['id']
            vol_name = task_response['target_uri'].split('/')[-1]
            self.assertEquals('COPYING', vol_name)
            self._wait_task(inst, taskid)
            self.assertEquals('finished', inst.task_lookup(taskid)['status'])
            rollback.prependDefer(inst.storagevolume_delete, pool,
                                  params['name'])
            vol_path = os.path.join(args['path'], vol_name)
            self.assertTrue(os.path.isfile(vol_path))
            with open(vol_path) as vol_file:
                vol_content = vol_file.read()
            with open(os.path.join(paths.get_prefix(), 'COPYING')) as cp_file:
                cp_content = cp_file.read()
            self.assertEquals(vol_content, cp_content)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_storage_customise(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            path = '/tmp/kimchi-images'
            pool = 'test-pool'
            if not os.path.exists(path):
                os.mkdir(path)

            params = {'name': 'test', 'disks': [{'size': 1}],
                      'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'storagepool': '/storagepools/test-pool'}
            self.assertRaises(InvalidParameter, inst.template_update,
                              'test', params)

            args = {'name': pool,
                    'path': path,
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, pool)

            inst.template_update('test', params)

            params = {'name': 'test-vm-1', 'template': '/templates/test'}
            self.assertRaises(InvalidParameter, inst.vms_create, params)

            inst.storagepool_activate(pool)
            rollback.prependDefer(inst.storagepool_deactivate, pool)

            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'test-vm-1')
            vm_info = inst.vm_lookup(params['name'])
            disk_path = '/tmp/kimchi-images/%s-0.img' % vm_info['uuid']
            self.assertTrue(os.access(disk_path, os.F_OK))
            vol = '%s-0.img' % vm_info['uuid']
            volinfo = inst.storagevolume_lookup(pool, vol)
            self.assertEquals(1, volinfo['ref_cnt'])

            # reset template to default storage pool
            # so we can remove the storage pool created 'test-pool'
            params = {'storagepool': '/storagepools/default'}
            inst.template_update('test', params)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_create(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        # Test non-exist path raises InvalidParameter
        params = {'name': 'test',
                  'cdrom': '/non-exsitent.iso'}
        self.assertRaises(InvalidParameter, inst.templates_create, params)

        # Test non-iso path raises InvalidParameter
        params['cdrom'] = os.path.abspath(__file__)
        self.assertRaises(InvalidParameter, inst.templates_create, params)

        with RollbackContext() as rollback:
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)
            rollback.prependDefer(inst.network_delete, net_name)

            params = {'name': 'test', 'memory': 1024, 'cpus': 1,
                      'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')
            info = inst.template_lookup('test')
            for key in params.keys():
                self.assertEquals(params[key], info[key])
            self.assertEquals("default", info["networks"][0])

            # create template with non-existent network
            params['name'] = 'new-test'
            params['networks'] = ["no-exist"]
            self.assertRaises(InvalidParameter, inst.templates_create, params)

            params['networks'] = ['default', 'test-network']
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, params['name'])
            info = inst.template_lookup(params['name'])
            for key in params.keys():
                self.assertEquals(params[key], info[key])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_integrity(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)

            path = '/tmp/kimchi-iso/'
            if not os.path.exists(path):
                os.makedirs(path)
            iso = path + 'ubuntu12.04.iso'
            iso_gen.construct_fake_iso(iso, True, '12.04', 'ubuntu')

            args = {'name': 'test-pool',
                    'path': '/tmp/kimchi-images',
                    'type': 'dir'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_delete, 'test-pool')

            params = {'name': 'test', 'memory': 1024, 'cpus': 1,
                      'networks': ['test-network'], 'cdrom': iso,
                      'storagepool': '/storagepools/test-pool'}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            # Try to delete network
            # It should fail as it is associated to a template
            self.assertRaises(InvalidOperation, inst.network_delete, net_name)
            # Update template to release network and then delete it
            params = {'networks': []}
            inst.template_update('test', params)
            inst.network_delete(net_name)

            shutil.rmtree(path)
            info = inst.template_lookup('test')
            self.assertEquals(info['invalid']['cdrom'], [iso])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_clone(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            orig_params = {'name': 'test-template', 'memory': 1024,
                           'cpus': 1, 'cdrom': self.kimchi_iso}
            inst.templates_create(orig_params)
            rollback.prependDefer(inst.template_delete, 'test-template')
            orig_temp = inst.template_lookup(orig_params['name'])

            ident = inst.template_clone('test-template')
            rollback.prependDefer(inst.template_delete, ident)
            clone_temp = inst.template_lookup(ident)

            clone_temp['name'] = orig_temp['name']
            for key in clone_temp.keys():
                self.assertEquals(clone_temp[key], orig_temp[key])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_template_update(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            net_name = 'test-network'
            net_args = {'name': net_name,
                        'connection': 'nat',
                        'subnet': '127.0.100.0/24'}
            inst.networks_create(net_args)
            rollback.prependDefer(inst.network_delete, net_name)

            orig_params = {'name': 'test', 'memory': 1024, 'cpus': 1,
                           'cdrom': self.kimchi_iso}
            inst.templates_create(orig_params)

            params = {'name': 'new-test'}
            self.assertEquals('new-test', inst.template_update('test', params))
            self.assertRaises(NotFoundError, inst.template_delete, 'test')

            params = {'name': 'new-test', 'memory': 512, 'cpus': 2}
            inst.template_update('new-test', params)
            rollback.prependDefer(inst.template_delete, 'new-test')

            info = inst.template_lookup('new-test')
            for key in params.keys():
                self.assertEquals(params[key], info[key])
            self.assertEquals("default", info["networks"][0])

            params = {'name': 'new-test', 'memory': 1024, 'cpus': 1,
                      'networks': ['default', 'test-network']}
            inst.template_update('new-test', params)
            info = inst.template_lookup('new-test')
            for key in params.keys():
                self.assertEquals(params[key], info[key])

            # test update with non-existent network
            params = {'networks': ["no-exist"]}
            self.assertRaises(InvalidParameter, inst.template_update,
                              'new-test', params)

    def test_vm_edit(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)

        orig_params = {'name': 'test', 'memory': '1024', 'cpus': '1',
                       'cdrom': self.kimchi_iso}
        inst.templates_create(orig_params)

        with RollbackContext() as rollback:
            params_1 = {'name': 'kimchi-vm1', 'template': '/templates/test'}
            params_2 = {'name': 'kimchi-vm2', 'template': '/templates/test'}
            inst.vms_create(params_1)
            rollback.prependDefer(self._rollback_wrapper, inst.vm_delete,
                                  'kimchi-vm1')
            inst.vms_create(params_2)
            rollback.prependDefer(self._rollback_wrapper, inst.vm_delete,
                                  'kimchi-vm2')

            vms = inst.vms_get_list()
            self.assertTrue('kimchi-vm1' in vms)

            # update vm graphics when vm is not running
            inst.vm_update(u'kimchi-vm1',
                           {"graphics": {"passwd": "123456"}})

            inst.vm_start('kimchi-vm1')
            rollback.prependDefer(self._rollback_wrapper, inst.vm_poweroff,
                                  'kimchi-vm1')

            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals('123456', vm_info['graphics']["passwd"])
            self.assertEquals(None, vm_info['graphics']["passwdValidTo"])

            # update vm graphics when vm is running
            inst.vm_update(u'kimchi-vm1',
                           {"graphics": {"passwd": "abcdef",
                                         "passwdValidTo": 20}})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals('abcdef', vm_info['graphics']["passwd"])
            self.assertGreaterEqual(20, vm_info['graphics']['passwdValidTo'])

            info = inst.vm_lookup('kimchi-vm1')
            self.assertEquals('running', info['state'])

            params = {'name': 'new-vm'}
            self.assertRaises(InvalidParameter, inst.vm_update,
                              'kimchi-vm1', params)

            # change VM users and groups, when wm is running.
            inst.vm_update(u'kimchi-vm1',
                           {'users': ['root'], 'groups': ['root']})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals(['root'], vm_info['users'])
            self.assertEquals(['root'], vm_info['groups'])
            # change VM users and groups by removing all elements,
            # when wm is running.
            inst.vm_update(u'kimchi-vm1', {'users': [], 'groups': []})
            vm_info = inst.vm_lookup(u'kimchi-vm1')
            self.assertEquals([], vm_info['users'])
            self.assertEquals([], vm_info['groups'])

            inst.vm_poweroff('kimchi-vm1')
            self.assertRaises(OperationFailed, inst.vm_update,
                              'kimchi-vm1', {'name': 'kimchi-vm2'})

            params = {'name': u'пeω-∨м', 'cpus': 4, 'memory': 2048}
            inst.vm_update('kimchi-vm1', params)
            rollback.prependDefer(self._rollback_wrapper, inst.vm_delete,
                                  u'пeω-∨м')
            self.assertEquals(info['uuid'], inst.vm_lookup(u'пeω-∨м')['uuid'])
            info = inst.vm_lookup(u'пeω-∨м')
            for key in params.keys():
                self.assertEquals(params[key], info[key])

            # change only VM users - groups are not changed (default is empty)
            users = inst.users_get_list()[:3]
            inst.vm_update(u'пeω-∨м', {'users': users})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals([], inst.vm_lookup(u'пeω-∨м')['groups'])

            # change only VM groups - users are not changed (default is empty)
            groups = inst.groups_get_list()[:2]
            inst.vm_update(u'пeω-∨м', {'groups': groups})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users and groups by adding a new element to each one
            users.append(pwd.getpwuid(os.getuid()).pw_name)
            groups.append(grp.getgrgid(os.getgid()).gr_name)
            inst.vm_update(u'пeω-∨м', {'users': users, 'groups': groups})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users (wrong value) and groups
            # when an error occurs, everything fails and nothing is changed
            self.assertRaises(InvalidParameter, inst.vm_update, u'пeω-∨м',
                              {'users': ['userdoesnotexist'], 'groups': []})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users and groups (wrong value)
            # when an error occurs, everything fails and nothing is changed
            self.assertRaises(InvalidParameter, inst.vm_update, u'пeω-∨м',
                              {'users': [], 'groups': ['groupdoesnotexist']})
            self.assertEquals(users, inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals(groups, inst.vm_lookup(u'пeω-∨м')['groups'])

            # change VM users and groups by removing all elements
            inst.vm_update(u'пeω-∨м', {'users': [], 'groups': []})
            self.assertEquals([], inst.vm_lookup(u'пeω-∨м')['users'])
            self.assertEquals([], inst.vm_lookup(u'пeω-∨м')['groups'])

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_network(self):
        inst = model.Model('qemu:///system', self.tmp_store)

        with RollbackContext() as rollback:

            # Regression test:
            # Kimchi fails creating new network #318
            name = 'test-network-no-subnet'

            networks = inst.networks_get_list()
            num = len(networks) + 1
            args = {'name': name,
                    'connection': 'nat',
                    'subnet': ''}
            inst.networks_create(args)
            rollback.prependDefer(inst.network_delete, name)

            networks = inst.networks_get_list()
            self.assertEquals(num, len(networks))
            networkinfo = inst.network_lookup(name)
            self.assertNotEqual(args['subnet'], networkinfo['subnet'])
            self.assertEqual(args['connection'], networkinfo['connection'])
            self.assertEquals('inactive', networkinfo['state'])
            self.assertEquals([], networkinfo['vms'])
            self.assertTrue(networkinfo['autostart'])
            self.assertTrue(networkinfo['persistent'])

            inst.network_activate(name)
            rollback.prependDefer(inst.network_deactivate, name)

            networkinfo = inst.network_lookup(name)
            self.assertEquals('active', networkinfo['state'])

            # test network creation with subnet passed
            name = 'test-network-subnet'

            networks = inst.networks_get_list()
            num = len(networks) + 1
            args = {'name': name,
                    'connection': 'nat',
                    'subnet': '127.0.100.0/24'}
            inst.networks_create(args)
            rollback.prependDefer(inst.network_delete, name)

            networks = inst.networks_get_list()
            self.assertEquals(num, len(networks))
            networkinfo = inst.network_lookup(name)
            self.assertEqual(args['subnet'], networkinfo['subnet'])
            self.assertEqual(args['connection'], networkinfo['connection'])
            self.assertEquals('inactive', networkinfo['state'])
            self.assertEquals([], networkinfo['vms'])
            self.assertTrue(networkinfo['autostart'])

            inst.network_activate(name)
            rollback.prependDefer(inst.network_deactivate, name)

            networkinfo = inst.network_lookup(name)
            self.assertEquals('active', networkinfo['state'])

        networks = inst.networks_get_list()
        self.assertEquals((num - 2), len(networks))

    def test_multithreaded_connection(self):
        def worker():
            for i in xrange(100):
                ret = inst.vms_get_list()
                self.assertEquals('test', ret[0])

        inst = model.Model('test:///default', self.tmp_store)
        threads = []
        for i in xrange(100):
            t = threading.Thread(target=worker)
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def test_object_store(self):
        store = kimchi.objectstore.ObjectStore(self.tmp_store)

        with store as session:
            # Test create
            session.store('fǒǒ', 'těst1', {'α': 1})
            session.store('fǒǒ', 'těst2', {'β': 2})

            # Test list
            items = session.get_list('fǒǒ')
            self.assertTrue(u'těst1' in items)
            self.assertTrue(u'těst2' in items)

            # Test get
            item = session.get('fǒǒ', 'těst1')
            self.assertEquals(1, item[u'α'])

            # Test delete
            session.delete('fǒǒ', 'těst2')
            self.assertEquals(1, len(session.get_list('fǒǒ')))

            # Test get non-existent item

            self.assertRaises(NotFoundError, session.get,
                              'α', 'β')

            # Test delete non-existent item
            self.assertRaises(NotFoundError, session.delete,
                              'fǒǒ', 'těst2')

            # Test refresh existing item
            session.store('fǒǒ', 'těst1', {'α': 2})
            item = session.get('fǒǒ', 'těst1')
            self.assertEquals(2, item[u'α'])

    def test_object_store_threaded(self):
        def worker(ident):
            with store as session:
                session.store('foo', ident, {})

        store = kimchi.objectstore.ObjectStore(self.tmp_store)

        threads = []
        for i in xrange(50):
            t = threading.Thread(target=worker, args=(i,))
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        with store as session:
            self.assertEquals(50, len(session.get_list('foo')))
            self.assertEquals(10, len(store._connections.keys()))

    def test_get_interfaces(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        expected_ifaces = netinfo.all_favored_interfaces()
        ifaces = inst.interfaces_get_list()
        self.assertEquals(len(expected_ifaces), len(ifaces))
        for name in expected_ifaces:
            iface = inst.interface_lookup(name)
            self.assertEquals(iface['name'], name)
            self.assertIn('type', iface)
            self.assertIn('status', iface)
            self.assertIn('ipaddr', iface)
            self.assertIn('netmask', iface)

    def test_async_tasks(self):
        class task_except(Exception):
            pass

        def quick_op(cb, message):
            cb(message, True)

        def long_op(cb, params):
            time.sleep(params.get('delay', 3))
            cb(params.get('message', ''), params.get('result', False))

        def abnormal_op(cb, params):
            try:
                raise task_except
            except:
                cb("Exception raised", False)

        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        taskid = add_task('', quick_op, inst.objstore, 'Hello')
        self._wait_task(inst, taskid)
        self.assertEquals(1, taskid)
        self.assertEquals('finished', inst.task_lookup(taskid)['status'])
        self.assertEquals('Hello', inst.task_lookup(taskid)['message'])

        taskid = add_task('', long_op, inst.objstore,
                          {'delay': 3, 'result': False,
                           'message': 'It was not meant to be'})
        self.assertEquals(2, taskid)
        self.assertEquals('running', inst.task_lookup(taskid)['status'])
        self.assertEquals('OK', inst.task_lookup(taskid)['message'])
        self._wait_task(inst, taskid)
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])
        self.assertEquals('It was not meant to be',
                          inst.task_lookup(taskid)['message'])
        taskid = add_task('', abnormal_op, inst.objstore, {})
        self._wait_task(inst, taskid)
        self.assertEquals('Exception raised',
                          inst.task_lookup(taskid)['message'])
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])

    # This wrapper function is needed due to the new backend messaging in
    # vm model. vm_poweroff and vm_delete raise exception if vm is not found.
    # These functions are called after vm has been deleted if test finishes
    # correctly, then NofFoundError exception is raised and rollback breaks
    def _rollback_wrapper(self, func, vmname):
        try:
            func(vmname)
        except NotFoundError:
            # VM has been deleted already
            return

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_delete_running_vm(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': u'test', 'disks': [], 'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': u'kīмсhī-∨м', 'template': u'/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(self._rollback_wrapper, inst.vm_delete,
                                  u'kīмсhī-∨м')

            inst.vm_start(u'kīмсhī-∨м')
            rollback.prependDefer(self._rollback_wrapper, inst.vm_poweroff,
                                  u'kīмсhī-∨м')

            inst.vm_delete(u'kīмсhī-∨м')

            vms = inst.vms_get_list()
            self.assertFalse(u'kīмсhī-∨м' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_vm_list_sorted(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [], 'cdrom': self.kimchi_iso}
            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm', 'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertEquals(vms, sorted(vms, key=unicode.lower))

    def test_use_test_host(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            params = {'name': 'test', 'disks': [], 'cdrom': self.kimchi_iso,
                      'storagepool': '/storagepools/default-pool',
                      'domain': 'test',
                      'arch': 'i686'}

            inst.templates_create(params)
            rollback.prependDefer(inst.template_delete, 'test')

            params = {'name': 'kimchi-vm',
                      'template': '/templates/test'}
            inst.vms_create(params)
            rollback.prependDefer(inst.vm_delete, 'kimchi-vm')

            vms = inst.vms_get_list()

            self.assertTrue('kimchi-vm' in vms)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_debug_reports(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        if not inst.capabilities_lookup()['system_report_tool']:
            raise unittest.SkipTest("Without debug report tool")

        try:
            timeout = int(os.environ['TEST_REPORT_TIMEOUT'])
        except (ValueError, KeyError):
            timeout = 120

        namePrefix = 'unitTestReport'
        # sosreport always deletes unsual letters like '-' and '_' in the
        # generated report file name.
        uuidstr = str(uuid.uuid4()).translate(None, "-_")
        reportName = namePrefix + uuidstr
        try:
            inst.debugreport_delete(namePrefix + '*')
        except NotFoundError:
            pass
        with RollbackContext() as rollback:
            report_list = inst.debugreports_get_list()
            self.assertFalse(reportName in report_list)
            try:
                tmp_name = reportName + "_1"
                task = inst.debugreports_create({'name': reportName})
                rollback.prependDefer(inst.debugreport_delete, tmp_name)
                taskid = task['id']
                self._wait_task(inst, taskid, timeout)
                self.assertEquals('finished',
                                  inst.task_lookup(taskid)['status'],
                                  "It is not necessary an error.  "
                                  "You may need to increase the "
                                  "timeout number by "
                                  "TEST_REPORT_TIMEOUT=200 "
                                  "./run_tests.sh test_model")
                report_list = inst.debugreports_get_list()
                self.assertTrue(reportName in report_list)
                name = inst.debugreport_update(reportName, {'name': tmp_name})
                self.assertEquals(name, tmp_name)
                report_list = inst.debugreports_get_list()
                self.assertTrue(tmp_name in report_list)
            except OperationFailed, e:
                if 'debugreport tool not found' not in e.message:
                    raise e

    def _wait_task(self, model, taskid, timeout=5):
            for i in range(0, timeout):
                if model.task_lookup(taskid)['status'] == 'running':
                    time.sleep(1)

    def test_get_distros(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        distros = inst.distros_get_list()
        for d in distros:
            distro = inst.distro_lookup(d)
            self.assertIn('name', distro)
            self.assertIn('os_distro', distro)
            self.assertIn('os_version', distro)
            self.assertIn('os_arch', distro)
            self.assertIn('path', distro)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_get_hostinfo(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)
        info = inst.host_lookup()
        distro, version, codename = platform.linux_distribution()
        self.assertIn('cpu', info)
        self.assertEquals(distro, info['os_distro'])
        self.assertEquals(version, info['os_version'])
        self.assertEquals(unicode(codename, "utf-8"), info['os_codename'])
        self.assertEquals(psutil.TOTAL_PHYMEM, info['memory'])

    def test_get_hoststats(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)
        time.sleep(1.5)
        stats = inst.hoststats_lookup()
        stats_keys = ['cpu_utilization', 'memory', 'disk_read_rate',
                      'disk_write_rate', 'net_recv_rate', 'net_sent_rate']
        self.assertEquals(sorted(stats_keys), sorted(stats.keys()))
        cpu_utilization = stats['cpu_utilization']
        # cpu_utilization is set int 0, after first stats sample
        # the cpu_utilization is float in range [0.0, 100.0]
        self.assertIsInstance(cpu_utilization, float)
        self.assertGreaterEqual(cpu_utilization, 0.0)
        self.assertTrue(cpu_utilization <= 100.0)

        memory_stats = stats['memory']
        self.assertIn('total', memory_stats)
        self.assertIn('free', memory_stats)
        self.assertIn('cached', memory_stats)
        self.assertIn('buffers', memory_stats)
        self.assertIn('avail', memory_stats)

        history = inst.hoststatshistory_lookup()
        self.assertEquals(sorted(stats_keys), sorted(history.keys()))
        for key, value in history.iteritems():
            self.assertEquals(type(value), list)

    @unittest.skipUnless(utils.running_as_root(), 'Must be run as root')
    def test_deep_scan(self):
        inst = model.Model('qemu:///system',
                           objstore_loc=self.tmp_store)
        with RollbackContext() as rollback:
            path = '/tmp/kimchi-images/tmpdir'
            if not os.path.exists(path):
                os.makedirs(path)
            iso_gen.construct_fake_iso('/tmp/kimchi-images/tmpdir/'
                                       'ubuntu12.04.iso', True,
                                       '12.04', 'ubuntu')
            iso_gen.construct_fake_iso('/tmp/kimchi-images/sles10.iso',
                                       True, '10', 'sles')

            args = {'name': 'kimchi-scanning-pool',
                    'path': '/tmp/kimchi-images',
                    'type': 'kimchi-iso'}
            inst.storagepools_create(args)
            rollback.prependDefer(inst.storagepool_deactivate, args['name'])

            time.sleep(1)
            volumes = inst.storagevolumes_get_list(args['name'])
            self.assertEquals(len(volumes), 2)

    def test_repository_create(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        yum_repos = [{'repo_id': 'fedora-fake',
                      'baseurl': 'http://www.fedora.org'},
                     {'repo_id': 'fedora-updates-fake',
                      'config':
                      {'mirrorlist': 'http://www.fedoraproject.org',
                       'gpgkey': 'file:///tmp/KEY-fedora-updates-fake-19'}}]

        deb_repos = [{'baseurl': 'http://br.archive.ubuntu.com/kimchi/fake',
                      'config': {'dist': 'quantal'}},
                     {'baseurl': 'http://br.archive.kimchi.com/ubuntu/fake',
                      'config': {'dist': 'quantal', 'comps': ['main']}}]

        repo_type = inst.capabilities_lookup()['repo_mngt_tool']
        if repo_type == 'yum':
            test_repos = yum_repos
        elif repo_type == 'deb':
            test_repos = deb_repos
        else:
            # repository management tool was not recognized by Kimchi
            # skip test case
            return

        invalid_urls = ['www.fedora.org',                 # missing protocol
                        '://www.fedora.org',              # missing protocol
                        'http://www.fedora',              # invalid domain name
                        'file:///home/userdoesnotexist']  # invalid path

        # create repositories with invalid baseurl
        for url in invalid_urls:
            repo = {'repo_id': 'repo_fake',
                    'baseurl': url,
                    'config': {'dist': 'quantal'}}
            self.assertRaises(InvalidParameter, inst.repositories_create, repo)

        # create repositories with invalid mirrorlist
        for url in invalid_urls:
            repo = {'repo_id': 'repo_fake',
                    'config': {'mirrorlist': url, 'dist': 'quantal'}}
            self.assertRaises(InvalidParameter, inst.repositories_create, repo)

        for repo in test_repos:
            system_host_repos = len(inst.repositories_get_list())
            repo_id = inst.repositories_create(repo)
            host_repos = inst.repositories_get_list()
            self.assertEquals(system_host_repos + 1, len(host_repos))

            repo_info = inst.repository_lookup(repo_id)
            self.assertEquals(repo_id, repo_info['repo_id'])
            self.assertEquals(True, repo_info.get('enabled'))
            self.assertEquals(repo.get('baseurl', ''),
                              repo_info.get('baseurl'))

            original_config = repo.get('config', {})
            config_info = repo_info.get('config', {})

            if repo_type == 'yum':
                self.assertEquals(original_config.get('mirrorlist', ''),
                                  config_info.get('mirrorlist', ''))
                self.assertEquals(True, config_info['gpgcheck'])
            else:
                self.assertEquals(original_config['dist'], config_info['dist'])
                self.assertEquals(original_config.get('comps', []),
                                  config_info.get('comps', []))

            inst.repository_delete(repo_id)
            self.assertRaises(NotFoundError, inst.repository_lookup, repo_id)

        self.assertRaises(NotFoundError, inst.repository_lookup, 'google')

    def test_repository_update(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        yum_repo = {'repo_id': 'fedora-fake',
                    'baseurl': 'http://www.fedora.org'}
        yum_new_repo = {'baseurl': 'http://www.fedoraproject.org'}

        deb_repo = {'baseurl': 'http://br.archive.ubuntu.com/kimchi/fake',
                    'config': {'dist': 'quantal'}}
        deb_new_repo = {'baseurl': 'http://archive.canonical.com/kimchi'}

        repo_type = inst.capabilities_lookup()['repo_mngt_tool']
        if repo_type == 'yum':
            repo = yum_repo
            new_repo = yum_new_repo
        elif repo_type == 'deb':
            repo = deb_repo
            new_repo = deb_new_repo
        else:
            # repository management tool was not recognized by Kimchi
            # skip test case
            return

        system_host_repos = len(inst.repositories_get_list())

        repo_id = inst.repositories_create(repo)
        host_repos = inst.repositories_get_list()
        self.assertEquals(system_host_repos + 1, len(host_repos))

        invalid_urls = ['www.fedora.org',                 # missing protocol
                        '://www.fedora.org',              # missing protocol
                        'http://www.fedora',              # invalid domain name
                        'file:///home/userdoesnotexist']  # invalid path

        # update repositories with invalid baseurl
        for url in invalid_urls:
            wrong_repo = {'baseurl': url}
            self.assertRaises(InvalidParameter, inst.repository_update,
                              repo_id, wrong_repo)

        # update repositories with invalid mirrorlist
        for url in invalid_urls:
            wrong_repo = {'config': {'mirrorlist': url}}
            self.assertRaises(InvalidParameter, inst.repository_update,
                              repo_id, wrong_repo)

        new_repo_id = inst.repository_update(repo_id, new_repo)
        repo_info = inst.repository_lookup(new_repo_id)

        self.assertEquals(new_repo_id, repo_info['repo_id'])
        self.assertEquals(new_repo['baseurl'], repo_info['baseurl'])
        self.assertEquals(True, repo_info['enabled'])

        # remove files creates
        inst.repository_delete(new_repo_id)

    def test_repository_disable_enable(self):
        inst = model.Model('test:///default',
                           objstore_loc=self.tmp_store)

        yum_repo = {'repo_id': 'fedora-fake',
                    'baseurl': 'http://www.fedora.org'}
        deb_repo = {'baseurl': 'http://br.archive.ubuntu.com/kimchi/fake',
                    'config': {'dist': 'quantal'}}

        repo_type = inst.capabilities_lookup()['repo_mngt_tool']
        if repo_type == 'yum':
            repo = yum_repo
        elif repo_type == 'deb':
            repo = deb_repo
        else:
            # repository management tool was not recognized by Kimchi
            # skip test case
            return

        system_host_repos = len(inst.repositories_get_list())

        repo_id = inst.repositories_create(repo)

        host_repos = inst.repositories_get_list()
        self.assertEquals(system_host_repos + 1, len(host_repos))

        repo_info = inst.repository_lookup(repo_id)
        self.assertEquals(True, repo_info['enabled'])

        inst.repository_disable(repo_id)
        repo_info = inst.repository_lookup(repo_id)
        self.assertEquals(False, repo_info['enabled'])

        inst.repository_enable(repo_id)
        repo_info = inst.repository_lookup(repo_id)
        self.assertEquals(True, repo_info['enabled'])

        # remove files creates
        inst.repository_delete(repo_id)


class BaseModelTests(unittest.TestCase):
    class FoosModel(object):
        def __init__(self):
            self.data = {}

        def create(self, params):
            self.data.update(params)

        def get_list(self):
            return list(self.data)

    class TestModel(kimchi.basemodel.BaseModel):
        def __init__(self):
            foo = BaseModelTests.FoosModel()
            super(BaseModelTests.TestModel, self).__init__([foo])

    def test_root_model(self):
        t = BaseModelTests.TestModel()
        t.foos_create({'item1': 10})
        self.assertEquals(t.foos_get_list(), ['item1'])
