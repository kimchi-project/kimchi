#
# Project Ginger Base
#
# Copyright IBM, Corp. 2015
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

import lxml.etree as ET
import os
import random
import time

from wok.objectstore import ObjectStore
from wok.utils import add_task, wok_log

from wok.plugins.gingerbase import config
from wok.plugins.gingerbase.model import cpuinfo
from wok.plugins.gingerbase.model.debugreports import DebugReportsModel
from wok.plugins.gingerbase.model.model import Model

fake_user = {'root': 'letmein!'}
mockmodel_defaults = {'domain': 'test', 'arch': 'i686'}


class MockModel(Model):

    def __init__(self, objstore_loc=None):
        # Override osinfo.defaults to ajust the values according to
        # test:///default driver

        self._mock_swupdate = MockSoftwareUpdate()
        self._mock_repositories = MockRepositories()

        cpuinfo.get_topo_capabilities = \
            MockModel.get_topo_capabilities

        super(MockModel, self).__init__(objstore_loc)
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

        DebugReportsModel._gen_debugreport_file = self._gen_debugreport_file

    def reset(self):
        self._mock_swupdate = MockSoftwareUpdate()
        self._mock_repositories = MockRepositories()

        if hasattr(self, 'objstore'):
            self.objstore = ObjectStore(self.objstore_loc)

    @staticmethod
    def get_topo_capabilities(conn):
        # The libvirt test driver doesn't return topology.
        xml = "<topology sockets='1' cores='2' threads='2'/>"
        return ET.fromstring(xml)

    def _gen_debugreport_file(self, name):
        return add_task('/plugins/gingerbase/debugreports/%s' % name,
                        self._create_log, self.objstore, name)

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

    def _mock_host_shutdown(self, *name):
        wok_log.info("The host system will be shutted down")

    def _mock_host_reboot(self, *name):
        wok_log.info("The host system will be rebooted")

    def _mock_packagesupdate_get_list(self):
        return self._mock_swupdate.pkgs.keys()

    def _mock_packageupdate_lookup(self, pkg_name):
        return self._mock_swupdate.pkgs[pkg_name]

    def _mock_host_swupdate(self, args=None):
        task_id = add_task('/plugins/gingerbase/host/swupdate',
                           self._mock_swupdate.doUpdate,
                           self.objstore)
        return self.task_lookup(task_id)

    def _mock_repositories_get_list(self):
        return self._mock_repositories.repos.keys()

    def _mock_repositories_create(self, params):
        # Create a repo_id if not given by user. The repo_id will follow
        # the format gingerbase_repo_<integer>, where integer is the number of
        # seconds since the Epoch (January 1st, 1970), in UTC.
        repo_id = params.get('repo_id', None)
        if repo_id is None:
            repo_id = "gingerbase_repo_%s" % str(int(time.time() * 1000))
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
        self.repos = {"gingerbase_repo_1392167832":
                      {"repo_id": "gingerbase_repo_1392167832",
                       "enabled": True,
                       "baseurl": "http://www.fedora.org",
                       "config": {"repo_name": "gingerbase_repo_1392167832",
                                  "gpgkey": [],
                                  "gpgcheck": True,
                                  "mirrorlist": ""}}}
