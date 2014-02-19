#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
#
# Authors:
#  Paulo Vital <pvital@linux.vnet.ibm.com>
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
import platform

from kimchi.basemodel import Singleton
from kimchi.exception import InvalidOperation, InvalidParameter
from kimchi.exception import OperationFailed, NotFoundError, MissingParameter

YUM_DISTROS = ['fedora', 'red hat enterprise linux',
               'red hat enterprise linux server', 'opensuse ',
               'suse linux enterprise server ']
APT_DISTROS = ['debian', 'ubuntu']


class Repositories(object):
    __metaclass__ = Singleton

    """
    Class to represent and operate with repositories information.
    """
    def __init__(self):
        # This stores all repositories for Kimchi perspective. It's a
        # dictionary of dictionaries, in the format {<repo_id>: {repo}},
        # where:
        # repo = {'repo_id': <string>, 'repo_name': <string>,
        #        'baseurl': ([<string>], None), 'url_args': ([<string>, None),
        #        'enabled': True/False, 'gpgcheck': True/False,
        #        'gpgkey': ([<string>], None),
        #        'is_mirror': True/False}

        self._repo_storage = {}

        self._distro = platform.linux_distribution()[0].lower()
        if (self._distro in YUM_DISTROS):
            self._pkg_mnger = YumRepo()
        elif (self._distro in APT_DISTROS):
            self._pkg_mnger = AptRepo()
        else:
            raise InvalidOperation("KCHREPOS0014E")

        if self._pkg_mnger:
            # update the self._repo_storage with system's repositories
            self._scanSystemRepositories()

    def _scanSystemRepositories(self):
        """
        Update repositories._repo_storage with system's (host) repositories.
        """
        # Call system pkg_mnger to get the repositories as list of dict.
        for repo in self._pkg_mnger.getRepositoriesList():
            self.addRepository(repo)

    def addRepository(self, params={}):
        """
        Add and enable a new repository into repositories._repo_storage.
        """
        # Create and enable the repository
        repo_id = params.get('repo_id')
        repo = {'repo_id': repo_id,
                'repo_name': params.get('repo_name', repo_id),
                'baseurl': params.get('baseurl'),
                'url_args': params.get('url_args', None),
                'enabled': True,
                'gpgkey': params.get('gpgkey', None),
                'is_mirror': params.get('is_mirror', False)}

        if repo['gpgkey'] is not None:
            repo['gpgcheck'] = True
        else:
            repo['gpgcheck'] = False

        self._repo_storage[repo_id] = repo

        # Check in self._pkg_mnger if the repository already exists there
        if not repo_id in [irepo['repo_id'] for irepo in
                           self._pkg_mnger.getRepositoriesList()]:
            self._pkg_mnger.addRepo(repo)

    def getRepositories(self):
        """
        Return a dictionary with all Kimchi's repositories. Each element uses
        the format {<repo_id>: {repo}}, where repo is a dictionary in the
        repositories.Repositories() format.
        """
        return self._repo_storage

    def getRepository(self, repo_id):
        """
        Return a dictionary with all info from a given repository ID.
        """
        if not repo_id in self._repo_storage.keys():
            raise NotFoundError("KCHREPOS0010E", {'repo_id': repo_id})

        repo = self._repo_storage[repo_id]
        if (isinstance(repo['baseurl'], list)) and (len(repo['baseurl']) > 0):
            repo['baseurl'] = repo['baseurl'][0]

        return repo

    def getRepositoryFromPkgMnger(self, repo_id):
        """
        Return a dictionary with all info from a given repository ID.
        All info come from self._pkg_mnger.getRepo().
        """
        return self._pkg_mnger.getRepo(repo_id)

    def enabledRepositories(self):
        """
        Return a list with enabled repositories IDs.
        """
        enabled_repos = []
        for repo_id in self._repo_storage.keys():
            if self._repo_storage[repo_id]['enabled']:
                enabled_repos.append(repo_id)
        return enabled_repos

    def enableRepository(self, repo_id):
        """
        Enable a repository.
        """
        # Check if repo_id is already enabled
        if repo_id in self.enabledRepositories():
            raise NotFoundError("KCHREPOS0011E", {'repo_id': repo_id})

        try:
            repo = self.getRepository(repo_id)
            repo['enabled'] = True
            self.updateRepository(repo_id, repo)
            self._pkg_mnger.enableRepo(repo_id)
            return True
        except:
            raise OperationFailed("KCHREPOS0007E", {'repo_id': repo_id})

    def disableRepository(self, repo_id):
        """
        Disable a given repository.
        """
        # Check if repo_id is already disabled
        if not repo_id in self.enabledRepositories():
            raise NotFoundError("KCHREPOS0012E", {'repo_id': repo_id})

        try:
            repo = self.getRepository(repo_id)
            repo['enabled'] = False
            self.updateRepository(repo_id, repo)
            self._pkg_mnger.disableRepo(repo_id)
            return True
        except:
            raise OperationFailed("KCHREPOS0008E", {'repo_id': repo_id})

    def updateRepository(self, repo_id, new_repo={}):
        """
        Update the information of a given repository.
        The input is the repo_id of the repository to be updated and a dict
        with the information to be updated.
        """
        if (len(new_repo) == 0):
            raise InvalidParameter("KCHREPOS0013E")

        repo = self._repo_storage[repo_id]
        repo.update(new_repo)

        del self._repo_storage[repo_id]
        self._repo_storage[repo_id] = repo
        self._pkg_mnger.updateRepo(repo_id, self._repo_storage[repo_id])

    def removeRepository(self, repo_id):
        """
        Remove a given repository
        """
        if not repo_id in self._repo_storage.keys():
            raise NotFoundError("KCHREPOS0010E", {'repo_id': repo_id})

        del self._repo_storage[repo_id]
        self._pkg_mnger.removeRepo(repo_id)
        return True


class YumRepo(object):
    """
    Class to represent and operate with YUM repositories.
    It's loaded only on those systems listed at YUM_DISTROS and loads necessary
    modules in runtime.
    """
    def __init__(self):
        self._yb = getattr(__import__('yum'), 'YumBase')()
        self._repos = self._yb.repos
        self._conf = self._yb.conf
        self._enabled_repos = self._repos.listEnabled()

    def getRepositoriesList(self):
        """
        Return a list of dictionaries in the repositories.Repositories() format
        """
        repo_list = []
        for repo in self.enabledRepos():
            irepo = {}
            irepo['repo_id'] = repo.id
            irepo['repo_name'] = repo.name
            irepo['url_args'] = None,
            irepo['enabled'] = repo.enabled
            irepo['gpgcheck'] = repo.gpgcheck
            irepo['gpgkey'] = repo.gpgkey
            if len(repo.baseurl) > 0:
                irepo['baseurl'] = repo.baseurl
                irepo['is_mirror'] = False
            else:
                irepo['baseurl'] = [repo.mirrorlist]
                irepo['is_mirror'] = True
            repo_list.append(irepo)
        return repo_list

    def addRepo(self, repo={}):
        """
        Add a given repository in repositories.Repositories() format to YumBase
        """
        if len(repo) == 0:
            raise InvalidParameter("KCHREPOS0013E")

        # At least one base url, or one mirror, must be given.
        # baseurls must be a list of strings specifying the urls
        # mirrorlist must be a list of strings specifying a list of mirrors
        # Here we creates the lists, or set as None
        if repo['is_mirror']:
            mirrors = repo['baseurl']
            baseurl = None
        else:
            baseurl = [repo['baseurl']]
            mirrors = None

        self._yb.add_enable_repo(repo['repo_id'], baseurl, mirrors,
                                 name=repo['repo_name'],
                                 gpgcheck=repo['gpgcheck'],
                                 gpgkey=[repo['gpgkey']])

        # write a repo file in the system with repo{} information.
        self._write2disk(repo)

    def getRepo(self, repo_id):
        """
        Return a dictionary in the repositories.Repositories() of the given
        repository ID format with the information of a YumRepository object.
        """
        try:
            repo = self._repos.getRepo(repo_id)
            irepo = {}
            irepo['repo_id'] = repo.id
            irepo['repo_name'] = repo.name
            irepo['url_args'] = None,
            irepo['enabled'] = repo.enabled
            irepo['gpgcheck'] = repo.gpgcheck
            irepo['gpgkey'] = repo.gpgkey
            if len(repo.baseurl) > 0:
                irepo['baseurl'] = repo.baseurl
                irepo['is_mirror'] = False
            else:
                irepo['baseurl'] = [repo.mirrorlist]
                irepo['is_mirror'] = True
            return irepo
        except:
            raise OperationFailed("KCHREPOS0010E", {'repo_id': repo_id})

    def enabledRepos(self):
        """
        Return a list with enabled YUM repositories IDs
        """
        return self._enabled_repos

    def isRepoEnable(self, repo_id):
        """
        Return if a given repository ID is enabled or not
        """
        for repo in self.enabledRepos():
            if repo_id == repo.id:
                return True
        return False

    def enableRepo(self, repo_id):
        """
        Enable a given repository
        """
        try:
            self._repos.getRepo(repo_id).enable()
            self._repos.doSetup()
            return True
        except:
            raise OperationFailed("KCHREPOS0007E", {'repo_id': repo_id})

    def disableRepo(self, repo_id):
        """
        Disable a given repository
        """
        try:
            self._repos.getRepo(repo_id).disable()
            self._repos.doSetup()
            return True
        except:
            raise OperationFailed("KCHREPOS0008E", {'repo_id': repo_id})

    def updateRepo(self, repo_id, repo={}):
        """
        Update a given repository in repositories.Repositories() format
        """
        if len(repo) == 0:
            raise MissingParameter("KCHREPOS0013E")

        self._repos.delete(repo_id)
        self.addRepo(repo)

    def removeRepo(self, repo_id):
        """
        Remove a given repository
        """
        try:
            self._repos.delete(repo_id)
            self._removefromdisk(repo_id)
        except:
            raise OperationFailed("KCHREPOS0018E", {'repo_id': repo_id})

    def _write2disk(self, repo={}):
        """
        Write repository info into disk.
        """
        # Get a list with all reposdir configured in system's YUM.
        conf_dir = self._conf.reposdir
        if not conf_dir:
            raise NotFoundError("KCHREPOS0015E")

        if len(repo) == 0:
            raise InvalidParameter("KCHREPOS0016E")

        # Generate the content to be wrote.
        repo_content = '[%s]\n' % repo['repo_id']
        repo_content = repo_content + 'name=%s\n' % repo['repo_name']

        if isinstance(repo['baseurl'], list):
            link = repo['baseurl'][0]
        else:
            link = repo['baseurl']

        if repo['is_mirror']:
            repo_content = repo_content + 'mirrorlist=%s\n' % link
        else:
            repo_content = repo_content + 'baseurl=%s\n' % link

        if repo['enabled']:
            repo_content = repo_content + 'enabled=1\n'
        else:
            repo_content = repo_content + 'enabled=0\n'

        if repo['gpgcheck']:
            repo_content = repo_content + 'gpgcheck=1\n'
        else:
            repo_content = repo_content + 'gpgcheck=0\n'

        if repo['gpgkey']:
            if isinstance(repo['gpgkey'], list):
                link = repo['gpgkey'][0]
            else:
                link = repo['gpgkey']
            repo_content = repo_content + 'gpgckey=%s\n' % link

        # Scan for the confdirs and write the file in the first available
        # directory in the system. YUM will scan each confdir for repo files
        # and load it contents, so we can write in the first available dir.
        for dir in conf_dir:
            if os.path.isdir(dir):
                repo_file = dir + '/%s.repo' % repo['repo_id']
                if os.path.isfile(repo_file):
                    os.remove(repo_file)

                try:
                    with open(repo_file, 'w') as fd:
                        fd.write(repo_content)
                        fd.close()
                except:
                    raise OperationFailed("KCHREPOS0017E",
                                          {'repo_file': repo_file})
                break
        return True

    def _removefromdisk(self, repo_id):
        """
        Delete the repo file from disk of a given repository
        """
        conf_dir = self._conf.reposdir
        if not conf_dir:
            raise NotFoundError("KCHREPOS0015E")

        for dir in conf_dir:
            if os.path.isdir(dir):
                repo_file = dir + '/%s.repo' % repo_id
                if os.path.isfile(repo_file):
                    os.remove(repo_file)

        return True


class AptRepo(object):
    """
    Class to represent and operate with YUM repositories.
    It's loaded only on those systems listed at YUM_DISTROS and loads necessary
    modules in runtime.
    """
    def __init__(self):
        getattr(__import__('apt_pkg'), 'init_config')()
        getattr(__import__('apt_pkg'), 'init_system')()
        self._config = getattr(__import__('apt_pkg'), 'config')
        self._etc_slist = '/%s%s' % (self._config.get('Dir::Etc'),
                          self._config.get('Dir::Etc::sourcelist'))
        self._etc_sparts = '/%s%s' % (self._config.get('Dir::Etc'),
                           self._config.get('Dir::Etc::sourceparts'))

        module = __import__('aptsources.sourceslist', globals(), locals(),
                            ['SourcesList'], -1)
        self._repos = getattr(module, 'SourcesList')()

    def getRepositoriesList(self):
        """
        Return a list of dictionaries in the repositories.Repositories() format
        """
        repo_list = []
        for repo in self.enabledRepos():
            irepo = {}
            if repo.file == self._etc_slist:
                id = "%s%s" % (repo.uri.split("//")[1], repo.dist)
            else:
                id = repo.file.split('/')[-1].split('.')[0]
            irepo['repo_id'] = id
            irepo['baseurl'] = repo.uri
            list = [repo.dist]
            for comp in repo.comps:
                list.append(comp)
            irepo['url_args'] = list
            irepo['enabled'] = True
            irepo['is_mirror'] = False
            irepo['gpgcheck'] = False
            irepo['gpgkey'] = None
            repo_list.append(irepo)
        return repo_list

    def addRepo(self, repo={}):
        """
        Add a given repository in repositories.Repositories() format to APT
        """
        if len(repo) == 0:
            raise InvalidParameter("KCHREPOS0013E")

        if repo['url_args'] is not None:
            dist = repo['url_args'][0]
            args = repo['url_args'][1:]
        else:
            dist = None
            args = []

        _file = '%s/%s.list' % (self._etc_sparts, repo['repo_id'])

        self._repos.add('deb', repo['baseurl'], dist, args, file=_file)
        self._repos.save()

    def getRepo(self, repo_id):
        """
        Return a dictionary in the repositories.Repositories() format of the
        given repository ID with the information of a SourceEntry object.
        """
        for repo in self.enabledRepos():
            if repo.file == self._etc_slist:
                id = "%s%s" % (repo.uri.split("//")[1], repo.dist)
            else:
                id = repo.file.split('/')[-1].split('.')[0]

            if id != repo_id:
                continue

            irepo = {}
            irepo['repo_id'] = id
            irepo['baseurl'] = repo.uri
            list = [repo.dist]
            for comp in repo.comps:
                list.append(comp)
            irepo['url_args'] = list
            irepo['enabled'] = True
            irepo['is_mirror'] = False
            irepo['gpgcheck'] = False
            irepo['gpgkey'] = None
            return irepo
        raise OperationFailed("KCHREPOS0010E", {'repo_id': repo_id})

    def enabledRepos(self):
        """
        Return a list with enabled APT repositories
        """
        enabled_repos = []
        self._repos.refresh()
        for repo in self._repos:
            if (len(repo.str()) > 3) and (not repo.disabled):
                if repo.type == 'deb':
                    enabled_repos.append(repo)
        return enabled_repos

    def enableRepo(self, repo_id):
        """
        Enable a given repository
        """
        try:
            lrepo = self._genSourceLine(repo_id)
            self._repos.refresh()
            for repo in self._repos:
                if repo.disabled and (lrepo == repo.line):
                    repo.set_enabled('True')
                    self._repos.save()
            return True
        except:
            raise OperationFailed("KCHREPOS0007E", {'repo_id': repo_id})

    def disableRepo(self, repo_id):
        """
        Disable a given repository
        """
        try:
            lrepo = self._genSourceLine(repo_id)
            self._repos.refresh()
            for repo in self._repos:
                if (not repo.disabled) and (lrepo == repo.line):
                    repo.set_enabled('False')
                    self._repos.save()
            return True
        except:
            raise OperationFailed("KCHREPOS0008E", {'repo_id': repo_id})

    def updateRepo(self, repo_id, repo={}):
        """
        Update a given repository in repositories.Repositories() format
        """
        if len(repo) == 0:
            raise MissingParameter("KCHREPOS0013E")

        self.removeRepo(repo_id)
        self.addRepo(repo)

    def removeRepo(self, repo_id):
        """
        Remove a given repository
        """
        try:
            lrepo = self._genSourceLine(repo_id)
            self._repos.refresh()
            for repo in self._repos:
                if lrepo == repo.line:
                    self._repos.remove(repo)
                    self._repos.save()
                    self._removefromdisk(repo_id)
        except:
            raise OperationFailed("KCHREPOS0018E", {'repo_id': repo_id})

    def _genSourceLine(self, repo_id):
        """
        Generate a source.list line from repo_id information.
        """
        line = ''
        repo = self.getRepo(repo_id)
        if repo['enabled']:
            line = 'deb '
        else:
            line = '#deb '
        line = line + repo['baseurl'] + ' '
        line = line + ' '.join(repo['url_args'])
        line = line + '\n'
        return line

    def _removefromdisk(self, repo_id):
        """
        Delete the repo file from disk of a given repository
        """
        if os.path.isdir(self._etc_sparts):
            _file = '%s/%s.list' % (self._etc_sparts, repo_id)
            if os.path.isfile(_file):
                os.remove(_file)
        return True
