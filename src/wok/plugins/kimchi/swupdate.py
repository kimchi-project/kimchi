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

import fcntl
import os
import signal
import subprocess
import time
from configobj import ConfigObj, ConfigObjError
from psutil import pid_exists

from wok.basemodel import Singleton
from wok.exception import NotFoundError, OperationFailed
from wok.utils import run_command, wok_log

from wok.plugins.kimchi.config import kimchiLock
from wok.plugins.kimchi.yumparser import get_yum_packages_list_update


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
            wok_log.info("Loading YumUpdate features.")
            self._pkg_mnger = YumUpdate()
        except ImportError:
            try:
                __import__('apt')
                wok_log.info("Loading AptUpdate features.")
                self._pkg_mnger = AptUpdate()
            except ImportError:
                zypper_help = ["zypper", "--help"]
                (stdout, stderr, returncode) = run_command(zypper_help)
                if returncode == 0:
                    wok_log.info("Loading ZypperUpdate features.")
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

    def preUpdate(self):
        """
        Make adjustments before executing the command in
        a child process.
        """
        os.setsid()
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    def tailUpdateLogs(self, cb, params):
        """
        When the package manager is already running (started outside kimchi or
        if wokd is restarted) we can only know what's happening by reading the
        logfiles. This method acts like a 'tail -f' on the default package
        manager logfile. If the logfile is not found, a simple '*' is
        displayed to track progress. This will be until the process finishes.
        """
        if not self._pkg_mnger.isRunning():
            return

        fd = None
        try:
            fd = os.open(self._pkg_mnger.logfile, os.O_RDONLY)

        # cannot open logfile, print something to let users know that the
        # system is being upgrading until the package manager finishes its
        # job
        except (TypeError, OSError):
            msgs = []
            while self._pkg_mnger.isRunning():
                msgs.append('*')
                cb(''.join(msgs))
                time.sleep(1)
            msgs.append('\n')
            cb(''.join(msgs), True)
            return

        # go to the end of logfile and starts reading, if nothing is read or
        # a pattern is not found in the message just wait and retry until
        # the package manager finishes
        os.lseek(fd, 0, os.SEEK_END)
        msgs = []
        progress = []
        while True:
            read = os.read(fd, 1024)
            if not read:
                if not self._pkg_mnger.isRunning():
                    break

                if not msgs:
                    progress.append('*')
                    cb(''.join(progress))

                time.sleep(1)
                continue

            msgs.append(read)
            cb(''.join(msgs))

        os.close(fd)
        return cb(''.join(msgs), True)

    def doUpdate(self, cb, params):
        """
        Execute the update
        """
        # reset messages
        cb('')

        cmd = self._pkg_mnger.update_cmd
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=self.preUpdate)
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
        self.logfile = self._get_output_log()

    def _get_output_log(self):
        """
        Return the logfile path
        """
        yumcfg = None
        try:
            yumcfg = ConfigObj('/etc/yum.conf')

        except ConfigObjError:
            return None

        if 'main' in yumcfg and 'logfile' in yumcfg['main']:
            return yumcfg['main']['logfile']

        return None

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
        if self.isRunning():
            raise OperationFailed('KCHPKGUPD0005E')

        self._refreshUpdateList()
        pkg_list = []
        for pkg in self._pkgs:
            package = {'package_name': pkg.name, 'version': pkg.version,
                       'arch': pkg.arch, 'repository': pkg.ui_from_repo}
            pkg_list.append(package)
        return pkg_list

    def isRunning(self):
        """
        Return True whether the YUM package manager is already running or
        False otherwise.
        """
        try:
            with open('/var/run/yum.pid', 'r') as pidfile:
                pid = int(pidfile.read().rstrip('\n'))

        # cannot find pidfile, assumes yum is not running
        except (IOError, ValueError):
            return False

        # the pidfile exists and it lives in process table
        if pid_exists(pid):
            return True

        return False


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
        self.logfile = '/var/log/apt/term.log'

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
        if self.isRunning():
            raise OperationFailed('KCHPKGUPD0005E')

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

    def isRunning(self):
        """
        Return True whether the APT package manager is already running or
        False otherwise.
        """
        try:
            with open('/var/lib/dpkg/lock', 'w') as lockfile:
                fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # cannot open dpkg lock file to write in exclusive mode means the
        # apt is currently running
        except IOError:
            return True

        return False


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
        self.logfile = '/var/log/zypp/history'

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
        if self.isRunning():
            raise OperationFailed('KCHPKGUPD0005E')

        kimchiLock.acquire()
        self._refreshUpdateList()
        kimchiLock.release()
        return self._pkgs

    def isRunning(self):
        """
        Return True whether the Zypper package manager is already running or
        False otherwise.
        """
        try:
            with open('/var/run/zypp.pid', 'r') as pidfile:
                pid = int(pidfile.read().rstrip('\n'))

        # cannot find pidfile, assumes yum is not running
        except (IOError, ValueError):
            return False

        # the pidfile exists and it lives in process table
        if pid_exists(pid):
            return True

        return False
