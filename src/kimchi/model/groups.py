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

import grp

from kimchi.config import config


class GroupsModel(object):
    def __init__(self, **args):
        auth_type = config.get("authentication", "method")
        for klass in GroupsModel.__subclasses__():
            if auth_type == klass.auth_type:
                self.grp = klass(**args)

    def get_list(self, **args):
        if hasattr(self.grp, '_get_list'):
            return self.grp._get_list(**args)
        else:
            return list()

    def validate(self, gid):
        return self.grp._validate(gid)


class PAMGroupsModel(GroupsModel):
    auth_type = 'pam'

    def __init__(self, **kargs):
        pass

    def _get_list(self):
        return sorted([group.gr_name
                      for group in grp.getgrall()])

    def _validate(self, gid):
        try:
            grp.getgrnam(gid)
        except KeyError:
            return False
        return True


class LDAPGroupsModel(GroupsModel):
    auth_type = 'ldap'

    def __init__(self, **kargs):
        pass

    def _validate(self, gid):
        return False
