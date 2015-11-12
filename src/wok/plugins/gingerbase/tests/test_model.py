# -*- coding: utf-8 -*-
#
# Project Ginger Base
#
# Copyright IBM, Corp. 2013-2015
#
# Code derived from Project Kimchi
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
import shutil
import unittest

import wok.objectstore
from wok.basemodel import Singleton
from wok.exception import InvalidParameter, NotFoundError
from wok.rollbackcontext import RollbackContext
from wok.plugins.gingerbase.model import model

invalid_repository_urls = ['www.fedora.org',       # missing protocol
                           '://www.fedora.org',    # missing protocol
                           'http://www.fedora',    # invalid domain name
                           'file:///home/foobar']  # invalid path

TMP_DIR = '/var/lib/gingerbase/tests/'


def setUpModule():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    # iso_gen.construct_fake_iso(UBUNTU_ISO, True, '14.04', 'ubuntu')

    # Some FeatureTests functions depend on server to validate their result.
    # As CapabilitiesModel is a Singleton class it will get the first result
    # from FeatureTests which may be wrong when using the Model instance
    # directly - the case of this test_model.py
    # So clean Singleton instances to make sure to get the right result when
    # running the following tests.
    Singleton._instances = {}


def tearDownModule():
    shutil.rmtree(TMP_DIR)


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = '/tmp/gingerbase-store-test'

    def tearDown(self):
        # FIXME: Tests using 'test:///default' URI should be moved to
        # test_rest or test_mockmodel to avoid overriding problems
        # LibvirtConnection._connections['test:///default'] = {}

        os.unlink(self.tmp_store)

    def test_repository_create(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        yum_repos = [{'repo_id': 'fedora-fake',
                      'baseurl': 'http://www.fedora.org'},
                     {'repo_id': 'fedora-updates-fake',
                      'config':
                      {'mirrorlist': 'http://www.fedoraproject.org'}}]

        deb_repos = [{'baseurl': 'http://archive.ubuntu.com/ubuntu/',
                      'config': {'dist': 'quantal'}},
                     {'baseurl': 'http://archive.ubuntu.com/ubuntu/',
                      'config': {'dist': 'quantal', 'comps': ['main']}}]

        yum_invalid_repos = []
        deb_invalid_repos = []

        for url in invalid_repository_urls:
            wrong_baseurl = {'repo_id': 'wrong-id', 'baseurl': url}
            wrong_mirrorlist = {'repo_id': 'wrong-id',
                                'baseurl': 'www.example.com',
                                'config': {'mirrorlist': url}}
            wrong_config_item = {
                'repo_id': 'wrong-id',
                'baseurl': 'www.example.com',
                'config': {
                    'gpgkey': 'file:///tmp/KEY-fedora-updates-fake-19'}}

            yum_invalid_repos.append(wrong_baseurl)
            yum_invalid_repos.append(wrong_mirrorlist)
            yum_invalid_repos.append(wrong_config_item)

            wrong_baseurl['config'] = {'dist': 'tasty'}
            wrong_config = {'baseurl': deb_repos[0]['baseurl'],
                            'config': {
                                'unsupported_item': "a_unsupported_item"}}
            deb_invalid_repos.append(wrong_baseurl)
            deb_invalid_repos.append(wrong_config)

        repo_type = inst.capabilities_lookup()['repo_mngt_tool']
        if repo_type == 'yum':
            test_repos = yum_repos
            invalid_repos = yum_invalid_repos
        elif repo_type == 'deb':
            test_repos = deb_repos
            invalid_repos = deb_invalid_repos
        else:
            # repository management tool was not recognized by Ginger Base
            # skip test case
            return

        # create repositories with invalid data
        for repo in invalid_repos:
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
        inst = model.Model(objstore_loc=self.tmp_store)

        yum_repo = {'repo_id': 'fedora-fake',
                    'baseurl': 'http://www.fedora.org'}
        yum_new_repo = {'baseurl': 'http://www.fedoraproject.org'}

        deb_repo = {'baseurl': 'http://archive.ubuntu.com/ubuntu/',
                    'config': {'dist': 'quantal'}}
        deb_new_repo = {'baseurl': 'http://br.archive.canonical.com/ubuntu/',
                        'config': {'dist': 'utopic'}}

        yum_invalid_repos = []
        deb_invalid_repos = []

        for url in invalid_repository_urls:
            wrong_baseurl = {'baseurl': url}
            wrong_mirrorlist = {'baseurl': 'www.example.com',
                                'config': {'mirrorlist': url}}

            yum_invalid_repos.append(wrong_baseurl)
            yum_invalid_repos.append(wrong_mirrorlist)

            wrong_baseurl['config'] = {'dist': 'tasty'}
            deb_invalid_repos.append(wrong_baseurl)

        repo_type = inst.capabilities_lookup()['repo_mngt_tool']
        if repo_type == 'yum':
            repo = yum_repo
            new_repo = yum_new_repo
            invalid_repos = yum_invalid_repos
        elif repo_type == 'deb':
            repo = deb_repo
            new_repo = deb_new_repo
            invalid_repos = deb_invalid_repos
        else:
            # repository management tool was not recognized by Ginger Base
            # skip test case
            return

        system_host_repos = len(inst.repositories_get_list())

        with RollbackContext() as rollback:
            repo_id = inst.repositories_create(repo)
            rollback.prependDefer(inst.repository_delete, repo_id)

            host_repos = inst.repositories_get_list()
            self.assertEquals(system_host_repos + 1, len(host_repos))

            # update repositories with invalid data
            for tmp_repo in invalid_repos:
                self.assertRaises(InvalidParameter, inst.repository_update,
                                  repo_id, tmp_repo)

            new_repo_id = inst.repository_update(repo_id, new_repo)
            repo_info = inst.repository_lookup(new_repo_id)

            self.assertEquals(new_repo_id, repo_info['repo_id'])
            self.assertEquals(new_repo['baseurl'], repo_info['baseurl'])
            self.assertEquals(True, repo_info['enabled'])
            inst.repository_update(new_repo_id, repo)

    def test_repository_disable_enable(self):
        inst = model.Model(objstore_loc=self.tmp_store)

        yum_repo = {'repo_id': 'fedora-fake',
                    'baseurl': 'http://www.fedora.org'}
        deb_repo = {'baseurl': 'http://archive.ubuntu.com/ubuntu/',
                    'config': {'dist': 'quantal'}}

        repo_type = inst.capabilities_lookup()['repo_mngt_tool']
        if repo_type == 'yum':
            repo = yum_repo
        elif repo_type == 'deb':
            repo = deb_repo
        else:
            # repository management tool was not recognized by Ginger Base
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

    class TestModel(wok.basemodel.BaseModel):
        def __init__(self):
            foo = BaseModelTests.FoosModel()
            super(BaseModelTests.TestModel, self).__init__([foo])

    def test_root_model(self):
        t = BaseModelTests.TestModel()
        t.foos_create({'item1': 10})
        self.assertEquals(t.foos_get_list(), ['item1'])
