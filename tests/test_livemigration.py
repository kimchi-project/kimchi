#
# Project Kimchi
#
# Copyright IBM, Corp. 2015
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

import json
import libvirt
import mock
import os
import socket
import unittest
from functools import partial

from tests.utils import get_free_port, patch_auth, request, rollback_wrapper
from tests.utils import run_server, running_as_root, wait_task

from wok.basemodel import Singleton
from wok.exception import OperationFailed
from wok.rollbackcontext import RollbackContext
from wok.utils import run_command

from wok.plugins.kimchi.model import model
from wok.plugins.kimchi.model.libvirtconnection import LibvirtConnection
from wok.plugins.kimchi.model.vms import VMModel

import iso_gen


ISO_DIR = '/var/lib/libvirt/images/'
UBUNTU_ISO = ISO_DIR + 'ubuntu_kimchi_migration_test_14.04.iso'
KIMCHI_LIVE_MIGRATION_TEST = None


def setUpModule():
    if not os.path.exists(ISO_DIR):
        os.makedirs(ISO_DIR)
    iso_gen.construct_fake_iso(UBUNTU_ISO, True, '14.04', 'ubuntu')
    # Some FeatureTests functions depend on server to validate their result.
    # As CapabilitiesModel is a Singleton class it will get the first result
    # from FeatureTests which may be wrong when using the Model instance
    # directly - the case of this test_model.py
    # So clean Singleton instances to make sure to get the right result when
    # running the following tests.
    Singleton._instances = {}


def tearDownModule():
    os.remove(UBUNTU_ISO)


def remoteserver_environment_defined():
    global KIMCHI_LIVE_MIGRATION_TEST
    KIMCHI_LIVE_MIGRATION_TEST = os.environ.get('KIMCHI_LIVE_MIGRATION_TEST')
    return KIMCHI_LIVE_MIGRATION_TEST is not None


def running_root_and_remoteserver_defined():
    return running_as_root() and remoteserver_environment_defined()


def check_if_vm_migration_test_possible():
    inst = model.Model(objstore_loc='/tmp/kimchi-store-test')
    try:
        inst.vm_migration_pre_check(
            KIMCHI_LIVE_MIGRATION_TEST,
            'root',
            None
        )
    except:
        return False
    return True


@unittest.skipUnless(running_root_and_remoteserver_defined(),
                     'Must be run as root and with a remote server '
                     'defined in the KIMCHI_LIVE_MIGRATION_TEST variable')
class LiveMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/kimchi-store-test'
        self.inst = model.Model(
            'qemu:///system',
            objstore_loc=self.tmp_store
        )
        params = {'name': u'template_test_vm_migrate',
                  'disks': [],
                  'cdrom': UBUNTU_ISO,
                  'memory': 2048,
                  'max_memory': 4096 << 10}
        self.inst.templates_create(params)
        params = {'name': u'template_test_vm_migrate_nonshared',
                  'disks': [{'name': 'test_vm_migrate.img', 'size': 1}],
                  'cdrom': UBUNTU_ISO,
                  'memory': 2048,
                  'max_memory': 4096*1024}
        self.inst.templates_create(params)

    def tearDown(self):
        self.inst.template_delete('template_test_vm_migrate')
        self.inst.template_delete('template_test_vm_migrate_nonshared')

        os.unlink(self.tmp_store)

    def create_vm_test(self, non_shared_storage=False):
        params = {
            'name': u'test_vm_migrate',
            'template': u'/plugins/kimchi/templates/template_test_vm_migrate'
        }
        if non_shared_storage:
            params = {
                'name': u'test_vm_migrate',
                'template': u'/plugins/kimchi/templates/'
                'template_test_vm_migrate_nonshared'
            }
        task = self.inst.vms_create(params)
        self.inst.task_wait(task['id'])

    def test_vm_migrate_fails_if_remote_is_localhost(self):
        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              '127.0.0.1')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              'localhost')

            hostname = socket.gethostname()

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              hostname)

    def test_vm_migrate_fails_if_remotehost_unreachable(self):
        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              'test.vm.migrate.host.unreachable')

    def test_vm_migrate_fails_if_not_passwordless_login(self):
        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              'this_is_a_fake_remote_host')

    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.'
                '_get_remote_libvirt_conn')
    def test_vm_migrate_fails_different_remote_hypervisor(
            self, mock_get_remote_conn):

        class MockRemoteConnObj(object):
            def getType(self):
                return 'another_hypervisor'

            def close(self):
                pass

        mock_get_remote_conn.return_value = MockRemoteConnObj()

        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              KIMCHI_LIVE_MIGRATION_TEST)

    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.'
                '_get_remote_libvirt_conn')
    def test_vm_migrate_fails_different_remote_arch(
            self, mock_get_remote_conn):

        class MockRemoteConnObj(object):
            def getType(self):
                return 'QEMU'

            def getInfo(self):
                return ['another_arch', 'QEMU']

            def close(self):
                pass

        mock_get_remote_conn.return_value = MockRemoteConnObj()

        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              KIMCHI_LIVE_MIGRATION_TEST)

    def get_remote_conn(self):
        remote_uri = 'qemu+ssh://%s@%s/system' % \
            ('root', KIMCHI_LIVE_MIGRATION_TEST)
        remote_conn = libvirt.open(remote_uri)
        return remote_conn

    def get_remote_vm_list(self):
        remote_uri = 'qemu+ssh://%s@%s/system' % \
            ('root', KIMCHI_LIVE_MIGRATION_TEST)
        remote_conn = libvirt.open(remote_uri)
        return [vm.name() for vm in remote_conn.listAllDomains()]

    @unittest.skipUnless(check_if_vm_migration_test_possible(),
                         'not possible to test a live migration')
    def test_vm_livemigrate_persistent(self):

        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            # removing cdrom because it is not shared storage and will make
            # the migration fail
            dev_list = self.inst.vmstorages_get_list('test_vm_migrate')
            self.inst.vmstorage_delete('test_vm_migrate',  dev_list[0])

            try:
                self.inst.vm_start('test_vm_migrate')
            except Exception, e:
                self.fail('Failed to start the vm, reason: %s' % e.message)
            try:
                task = self.inst.vm_migrate('test_vm_migrate',
                                            KIMCHI_LIVE_MIGRATION_TEST)
                self.inst.task_wait(task['id'])
                self.assertIn('test_vm_migrate', self.get_remote_vm_list())

                remote_conn = self.get_remote_conn()
                rollback.prependDefer(remote_conn.close)

                remote_vm = remote_conn.lookupByName('test_vm_migrate')
                self.assertTrue(remote_vm.isPersistent())

                remote_vm.destroy()
                remote_vm.undefine()
            except Exception, e:
                self.fail('Migration test failed: %s' % e.message)

    @unittest.skipUnless(check_if_vm_migration_test_possible(),
                         'not possible to test a live migration')
    def test_vm_livemigrate_transient(self):
        self.create_vm_test()

        with RollbackContext() as rollback:
            try:
                # removing cdrom because it is not shared storage and will make
                # the migration fail
                dev_list = self.inst.vmstorages_get_list('test_vm_migrate')
                self.inst.vmstorage_delete('test_vm_migrate',  dev_list[0])

                self.inst.vm_start('test_vm_migrate')

                # to make the VM transient, undefine it while it's running
                vm = VMModel.get_vm(
                    'test_vm_migrate',
                    LibvirtConnection('qemu:///system')
                )
                vm.undefine()

                task = self.inst.vm_migrate('test_vm_migrate',
                                            KIMCHI_LIVE_MIGRATION_TEST)
                self.inst.task_wait(task['id'])
                self.assertIn('test_vm_migrate', self.get_remote_vm_list())

                remote_conn = self.get_remote_conn()
                rollback.prependDefer(remote_conn.close)

                remote_vm = remote_conn.lookupByName('test_vm_migrate')
                self.assertFalse(remote_vm.isPersistent())

                remote_vm.destroy()
            except Exception, e:
                # Clean up here instead of rollback because if the
                # VM was turned transient and shut down it might
                # not exist already - rollback in this case  will cause
                # a QEMU error
                vm = VMModel.get_vm(
                    'test_vm_migrate',
                    LibvirtConnection('qemu:///system')
                )
                if vm.isPersistent():
                    vm.undefine()
                vm.shutdown()
                self.fail('Migration test failed: %s' % e.message)

    @unittest.skipUnless(check_if_vm_migration_test_possible(),
                         'not possible to test shutdown migration')
    def test_vm_coldmigrate(self):
        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            # removing cdrom because it is not shared storage and will make
            # the migration fail
            dev_list = self.inst.vmstorages_get_list('test_vm_migrate')
            self.inst.vmstorage_delete('test_vm_migrate',  dev_list[0])

            try:
                task = self.inst.vm_migrate('test_vm_migrate',
                                            KIMCHI_LIVE_MIGRATION_TEST)
                self.inst.task_wait(task['id'])
                self.assertIn('test_vm_migrate', self.get_remote_vm_list())

                remote_conn = self.get_remote_conn()
                rollback.prependDefer(remote_conn.close)

                remote_vm = remote_conn.lookupByName('test_vm_migrate')
                self.assertTrue(remote_vm.isPersistent())

                state = remote_vm.info()[0]
                self.assertEqual(state, libvirt.VIR_DOMAIN_SHUTOFF)

                remote_vm.undefine()
            except Exception, e:
                self.fail('Migration test failed: %s' % e.message)

    def _erase_remote_file(self, path):
        username_host = "root@%s" % KIMCHI_LIVE_MIGRATION_TEST
        cmd = ['ssh', '-oStrictHostKeyChecking=no', username_host,
               'rm', '-f', path]
        _, _, returncode = run_command(cmd, silent=True)
        if returncode != 0:
            print 'cannot erase remote file ', path

    @unittest.skipUnless(check_if_vm_migration_test_possible(),
                         'not possible to test a live migration')
    def test_vm_livemigrate_persistent_nonshared(self):

        with RollbackContext() as rollback:
            self.create_vm_test(non_shared_storage=True)
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            # getting disk path info to clean it up later
            storage_list = self.inst.vmstorages_get_list('test_vm_migrate')
            disk_info = self.inst.vmstorage_lookup(
                'test_vm_migrate',
                storage_list[0]
            )
            disk_path = disk_info.get('path')

            try:
                self.inst.vm_start('test_vm_migrate')
            except Exception, e:
                self.fail('Failed to start the vm, reason: %s' % e.message)
            try:
                task = self.inst.vm_migrate('test_vm_migrate',
                                            KIMCHI_LIVE_MIGRATION_TEST)
                self.inst.task_wait(task['id'], 3600)
                self.assertIn('test_vm_migrate', self.get_remote_vm_list())

                remote_conn = self.get_remote_conn()
                rollback.prependDefer(remote_conn.close)

                remote_vm = remote_conn.lookupByName('test_vm_migrate')
                self.assertTrue(remote_vm.isPersistent())

                remote_vm.destroy()
                remote_vm.undefine()

                self._erase_remote_file(disk_path)
                self._erase_remote_file(UBUNTU_ISO)
            except Exception, e:
                self.fail('Migration test failed: %s' % e.message)

    def _task_lookup(self, taskid):
        return json.loads(
            self.request('/plugins/kimchi/tasks/%s' % taskid).read()
        )

    @unittest.skipUnless(check_if_vm_migration_test_possible(),
                         'not possible to test a live migration')
    def test_vm_livemigrate_persistent_API(self):
        patch_auth()

        inst = model.Model(libvirt_uri='qemu:///system',
                           objstore_loc=self.tmp_store)

        host = '127.0.0.1'
        port = get_free_port('http')
        ssl_port = get_free_port('https')
        cherrypy_port = get_free_port('cherrypy_port')

        with RollbackContext() as rollback:
            test_server = run_server(host, port, ssl_port, test_mode=True,
                                     cherrypy_port=cherrypy_port, model=inst)
            rollback.prependDefer(test_server.stop)

            self.request = partial(request, host, ssl_port)

            self.create_vm_test()
            rollback.prependDefer(rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            # removing cdrom because it is not shared storage and will make
            # the migration fail
            dev_list = self.inst.vmstorages_get_list('test_vm_migrate')
            self.inst.vmstorage_delete('test_vm_migrate',  dev_list[0])

            try:
                self.inst.vm_start('test_vm_migrate')
            except Exception, e:
                self.fail('Failed to start the vm, reason: %s' % e.message)

            migrate_url = "/plugins/kimchi/vms/%s/migrate" % 'test_vm_migrate'

            req = json.dumps({'remote_host': KIMCHI_LIVE_MIGRATION_TEST,
                             'user': 'root'})
            resp = self.request(migrate_url, req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            wait_task(self._task_lookup, task['id'])
            task = json.loads(
                self.request(
                    '/plugins/kimchi/tasks/%s' % task['id'],
                    '{}'
                ).read()
            )
            self.assertEquals('finished', task['status'])

            try:
                remote_conn = self.get_remote_conn()
                rollback.prependDefer(remote_conn.close)
                remote_vm = remote_conn.lookupByName('test_vm_migrate')
                self.assertTrue(remote_vm.isPersistent())
                remote_vm.destroy()
                remote_vm.undefine()
            except Exception, e:
                self.fail('Migration test failed: %s' % e.message)

    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.'
                '_set_password_less_login')
    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.'
                '_check_if_migrating_same_arch_hypervisor')
    @mock.patch('wok.plugins.kimchi.model.vms.VMModel.'
                '_check_ppc64_subcores_per_core')
    def test_set_passwordless_login(self, mock_ppc64_subpercore,
                                    mock_same_arch,
                                    mock_password_less_login):
        self.inst.vm_migration_pre_check(
            'this_is_a_fake_remote_host',
            'test_vm_migrate_fake_user',
            'fake_password'
        )
        mock_password_less_login.assert_called_once_with(
            'this_is_a_fake_remote_host',
            'test_vm_migrate_fake_user',
            'fake_password'
        )
