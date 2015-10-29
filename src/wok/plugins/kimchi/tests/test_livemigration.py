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
import os
import socket
import shutil
import unittest
from functools import partial


from wok.basemodel import Singleton
from wok.exception import OperationFailed
from wok.rollbackcontext import RollbackContext


from wok.plugins.kimchi.model import model
from wok.plugins.kimchi.model.libvirtconnection import LibvirtConnection
from wok.plugins.kimchi.model.vms import VMModel


import iso_gen
import utils
from utils import get_free_port, patch_auth, request
from utils import run_server, wait_task


TMP_DIR = '/var/lib/kimchi/tests/'
UBUNTU_ISO = TMP_DIR + 'ubuntu14.04.iso'
KIMCHI_LIVE_MIGRATION_TEST = None


def setUpModule():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    iso_gen.construct_fake_iso(UBUNTU_ISO, True, '14.04', 'ubuntu')
    # Some FeatureTests functions depend on server to validate their result.
    # As CapabilitiesModel is a Singleton class it will get the first result
    # from FeatureTests which may be wrong when using the Model instance
    # directly - the case of this test_model.py
    # So clean Singleton instances to make sure to get the right result when
    # running the following tests.
    Singleton._instances = {}


def tearDownModule():
    shutil.rmtree(TMP_DIR)


def remoteserver_environment_defined():
    global KIMCHI_LIVE_MIGRATION_TEST
    KIMCHI_LIVE_MIGRATION_TEST = os.environ.get('KIMCHI_LIVE_MIGRATION_TEST')
    return KIMCHI_LIVE_MIGRATION_TEST is not None


def running_root_and_remoteserver_defined():
    return utils.running_as_root() and remoteserver_environment_defined()


def check_if_vm_migration_test_possible():
    inst = model.Model(objstore_loc='/tmp/kimchi-store-test')
    try:
        inst.vm_migration_pre_check(KIMCHI_LIVE_MIGRATION_TEST, 'root')
    except:
        return False
    return True


@unittest.skipUnless(running_root_and_remoteserver_defined(),
                     'Must be run as root and with a remote server '
                     'defined in the KIMCHI_LIVE_MIGRATION_TEST variable')
class LiveMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/kimchi-store-test'
        self.inst = model.Model(objstore_loc=self.tmp_store)
        params = {'name': u'template_test_vm_migrate',
                  'disks': [],
                  'cdrom': UBUNTU_ISO,
                  'memory': 2048,
                  'max_memory': 4096*1024}
        self.inst.templates_create(params)

    def tearDown(self):
        self.inst.template_delete('template_test_vm_migrate')

        os.unlink(self.tmp_store)

    def create_vm_test(self):
        params = {
            'name': u'test_vm_migrate',
            'template': u'/plugins/kimchi/templates/template_test_vm_migrate'
        }
        task = self.inst.vms_create(params)
        self.inst.task_wait(task['id'])

    def test_vm_migrate_fails_if_remote_is_localhost(self):
        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(utils.rollback_wrapper, self.inst.vm_delete,
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
            rollback.prependDefer(utils.rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              'test.vm.migrate.host.unreachable')

    def test_vm_migrate_fails_if_not_passwordless_login(self):
        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(utils.rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            self.assertRaises(OperationFailed,
                              self.inst.vm_migrate,
                              'test_vm_migrate',
                              KIMCHI_LIVE_MIGRATION_TEST,
                              user='test_vm_migrate_fake_user')

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
        inst = model.Model(libvirt_uri='qemu:///system',
                           objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(utils.rollback_wrapper, self.inst.vm_delete,
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
                task = inst.vm_migrate('test_vm_migrate',
                                       KIMCHI_LIVE_MIGRATION_TEST)
                inst.task_wait(task['id'])
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
        inst = model.Model(libvirt_uri='qemu:///system',
                           objstore_loc=self.tmp_store)

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

                task = inst.vm_migrate('test_vm_migrate',
                                       KIMCHI_LIVE_MIGRATION_TEST)
                inst.task_wait(task['id'])
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
        inst = model.Model(libvirt_uri='qemu:///system',
                           objstore_loc=self.tmp_store)

        with RollbackContext() as rollback:
            self.create_vm_test()
            rollback.prependDefer(utils.rollback_wrapper, self.inst.vm_delete,
                                  u'test_vm_migrate')

            # removing cdrom because it is not shared storage and will make
            # the migration fail
            dev_list = self.inst.vmstorages_get_list('test_vm_migrate')
            self.inst.vmstorage_delete('test_vm_migrate',  dev_list[0])

            try:
                task = inst.vm_migrate('test_vm_migrate',
                                       KIMCHI_LIVE_MIGRATION_TEST)
                inst.task_wait(task['id'])
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
            rollback.prependDefer(utils.rollback_wrapper, self.inst.vm_delete,
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
