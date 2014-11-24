#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
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


from kimchi.control.base import Resource


class CPUInfo(Resource):
    def __init__(self, model):
        super(CPUInfo, self).__init__(model)
        self.admin_methods = ['GET']
        self.role_key = 'host'
        self.uri_fmt = "/host/cpuinfo"

    @property
    def data(self):
        return {'threading_enabled': self.info['guest_threads_enabled'],
                'sockets': self.info['sockets'],
                'cores': self.info['cores_available'],
                'threads_per_core': self.info['threads_per_core']
                }
