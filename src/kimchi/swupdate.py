#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
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

import subprocess
import time

from kimchi.basemodel import Singleton
from kimchi.config import kimchiLock
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.utils import kimchi_log, run_command
from kimchi.yumparser import get_yum_packages_list_update


class SoftwareUpdate(object):
    __metaclass__ = Singleton

    """
    Class to represent and operate with OS software update.
    """
    def __init__(self):
        # This stores all packages to be updated for Kimchi perspective. It's a
        # dictionary of dictionaries, in the format {'package_name': package},
        # where:
        # package = {'package_name': <string>, 'version': <string>,
        #           'arch': <string>, 'repository': <string>
        #           }
        self._packages = {}

        # This stores the number of packages to update
        self._num2update = 0

        # Get the distro of host machine and creates an object related to
        # correct package management system
        try:
            __import__('yum')
            kimchi_log.info("Loading YumUpdate features.")
            self._pkg_mnger = YumUpdate()
        except ImportError:
            try:
                __import__('apt')
                kimchi_log.info("Loading AptUpdate features.")
                self._pkg_mnger = AptUpdate()
            except ImportError:
                zypper_help = ["zypper", "--help"]
                (stdout, stderr, returncode) = run_command(zypper_help)
                if returncode == 0:
                    kimchi_log.info("Loading ZypperUpdate features.")
                    self._pkg_mnger = ZypperUpdate()
                else:
                    raise Exception("There is no compatible package manager "
                                    "for this system.")

    def _scanUpdates(self):
        """
        Update self._packages with packages to be updated.
        """
        self._packages = {}
        self._num2update = 0

        # Call system pkg_mnger to get the packages as list of dictionaries.
        for pkg in self._pkg_mnger.getPackagesList():

            # Check if already exist a package in self._packages
            pkg_id = pkg.get('package_name')
            if pkg_id in self._packages.keys():
                # package already listed to update. do nothing
                continue

            # Update the self._packages and self._num2update
            self._packages[pkg_id] = pkg
            self._num2update = self._num2update + 1

    def getUpdates(self):
        """
        Return the self._packages.
        """
        self._scanUpdates()
        return self._packages

    def getUpdate(self, name):
        """
        Return a dictionary with all info from a given package name.
        """
        if name not in self._packages.keys():
            raise NotFoundError('KCHPKGUPD0002E', {'name': name})

        return self._packages[name]

    def getNumOfUpdates(self):
        """
        Return the number of packages to be updated.
        """
        self._scanUpdates()
        return self._num2update

    def doUpdate(self, cb, params):
        """
        Execute the update
        """
        # reset messages
        cb('')

        cmd = self._pkg_mnger.update_cmd
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        msgs = []
        while proc.poll() is None:
            msgs.append(proc.stdout.readline())
            cb(''.join(msgs))
            time.sleep(0.5)

        # read the final output lines
        msgs.extend(proc.stdout.readlines())

        retcode = proc.poll()
        if retcode == 0:
            return cb(''.join(msgs), True)

        msgs.extend(proc.stderr.readlines())
        return cb(''.join(msgs), False)


class YumUpdate(object):
    """
    Class to represent and operate with YUM software update system.
    It's loaded only on those systems listed at YUM_DISTROS and loads necessary
    modules in runtime.
    """
    def __init__(self):
        self._pkgs = {}
        self.update_cmd = ["yum", "-y", "update"]

    def _refreshUpdateList(self):
        """
        Update the list of packages to be updated in the system.
        """
        try:
            kimchiLock.acquire()
            self._pkgs = get_yum_packages_list_update()
        except Exception, e:
            raise OperationFailed('KCHPKGUPD0003E', {'err': str(e)})
        finally:
            kimchiLock.release()

    def getPackagesList(self):
        """
        Return a list of package's dictionaries. Each dictionary contains the
        information about a package, in the format:
        package = {'package_name': <string>, 'version': <string>,
                   'arch': <string>, 'repository': <string>}
        """
        self._refreshUpdateList()
        pkg_list = []
        for pkg in self._pkgs:
            package = {'package_name': pkg.name, 'version': pkg.version,
                       'arch': pkg.arch, 'repository': pkg.ui_from_repo}
            pkg_list.append(package)
        return pkg_list


class AptUpdate(object):
    """
    Class to represent and operate with APT software update system.
    It's loaded only on those systems listed at APT_DISTROS and loads necessary
    modules in runtime.
    """
    def __init__(self):
        self._pkgs = {}
        self.pkg_lock = getattr(__import__('apt_pkg'), 'SystemLock')
        self.update_cmd = ['apt-get', 'upgrade', '-y']

    def _refreshUpdateList(self):
        """
        Update the list of packages to be updated in the system.
        """
        apt_cache = getattr(__import__('apt'), 'Cache')()
        try:
            with self.pkg_lock():
                apt_cache.update()
                apt_cache.upgrade()
                self._pkgs = apt_cache.get_changes()
        except Exception, e:
            kimchiLock.release()
            raise OperationFailed('KCHPKGUPD0003E', {'err': e.message})

    def getPackagesList(self):
        """
        Return a list of package's dictionaries. Each dictionary contains the
        information about a package, in the format
        package = {'package_name': <string>, 'version': <string>,
                   'arch': <string>, 'repository': <string>}
        """
        kimchiLock.acquire()
        self._refreshUpdateList()
        kimchiLock.release()
        pkg_list = []
        for pkg in self._pkgs:
            package = {'package_name': pkg.shortname,
                       'version': pkg.candidate.version,
                       'arch': pkg._pkg.architecture,
                       'repository': pkg.candidate.origins[0].label}
            pkg_list.append(package)

        return pkg_list


class ZypperUpdate(object):
    """
    Class to represent and operate with Zypper software update system.
    It's loaded only on those systems listed at ZYPPER_DISTROS and loads
    necessary modules in runtime.
    """
    def __init__(self):
        self._pkgs = {}
        self.update_cmd = ["zypper", "--non-interactive", "update",
                           "--auto-agree-with-licenses"]

    def _refreshUpdateList(self):
        """
        Update the list of packages to be updated in the system.
        """
        self._pkgs = []
        cmd = ["zypper", "list-updates"]
        (stdout, stderr, returncode) = run_command(cmd)

        if len(stderr) > 0:
            raise OperationFailed('KCHPKGUPD0003E', {'err': stderr})

        for line in stdout.split('\n'):
            if line.find('v |') >= 0:
                info = line.split(' | ')
                package = {'package_name': info[2], 'version': info[4],
                           'arch': info[5], 'repository': info[1]}
                self._pkgs.append(package)

    def getPackagesList(self):
        """
        Return a list of package's dictionaries. Each dictionary contains the
        information about a package, in the format
        package = {'package_name': <string>, 'version': <string>,
                   'arch': <string>, 'repository': <string>}
        """
        kimchiLock.acquire()
        self._refreshUpdateList()
        kimchiLock.release()
        return self._pkgs
