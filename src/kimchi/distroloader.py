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
#

import glob
import json
import os


from kimchi import config
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.utils import kimchi_log


ARCHS = {'x86_64': ['x86_64', 'amd64', 'i686', 'x86', 'i386'],
         'amd64': ['x86_64', 'amd64', 'i686', 'x86', 'i386'],
         'ppc64': ['ppc', 'ppc64'],
         'ppc64le': ['ppc64', 'ppc64le']}


class DistroLoader(object):

    def __init__(self, location=None):
        self.location = location or config.get_distros_store()

    def _get_json_info(self, fname):
        msg_args = {'filename': fname}
        if not os.path.isfile(fname):
            msg = "DistroLoader: failed to find distro file: %s" % fname
            kimchi_log.error(msg)
            raise NotFoundError("KCHDL0001E", msg_args)
        try:
            with open(fname) as f:
                data = json.load(f)
            return data
        except ValueError:
            msg = "DistroLoader: failed to parse distro file: %s" % fname
            kimchi_log.error(msg)
            raise OperationFailed("KCHDL0002E", msg_args)

    def get(self):
        arch_list = ARCHS.get(os.uname()[4])
        all_json_files = glob.glob("%s/%s" % (self.location, "*.json"))
        distros = []
        for f in all_json_files:
            distros.extend(self._get_json_info(f))

        # Return all remote ISOs arch not found
        return dict([(distro['name'], distro) for distro in distros if
                     (arch_list is None or distro['os_arch'] in arch_list)])
