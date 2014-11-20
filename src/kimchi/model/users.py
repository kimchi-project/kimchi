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

import ldap
import pwd

from kimchi.config import config
from kimchi.exception import NotFoundError


class UsersModel(object):
    def __init__(self, **args):
        auth_type = config.get("authentication", "method")
        for klass in UsersModel.__subclasses__():
            if auth_type == klass.auth_type:
                self.user = klass(**args)

    def get_list(self, **args):
        return self.user._get_list(**args)

    def validate(self, user):
        return self.user._validate(user)


class PAMUsersModel(UsersModel):
    auth_type = 'pam'

    def __init__(self, **kargs):
        pass

    def _get_list(self):
        return [user.pw_name for user in pwd.getpwall()
                if user.pw_shell.rsplit("/")[-1] not in ["nologin", "false"]]

    def _validate(self, user):
        try:
            return user in self._get_list()
        except:
            return False


class LDAPUsersModel(UsersModel):
    auth_type = 'ldap'

    def __init__(self, **kargs):
        pass

    def _get_list(self, _user_id=''):
        return self._get_user(_user_id)

    def _validate(self, user):
        try:
            self._get_user(user)
            return True
        except NotFoundError:
            return False

    def _get_user(self, _user_id):
        ldap_server = config.get("authentication", "ldap_server").strip('"')
        ldap_search_base = config.get(
            "authentication", "ldap_search_base").strip('"')
        ldap_search_filter = config.get(
            "authentication", "ldap_search_filter",
            vars={"username": _user_id.encode("utf-8")}).strip('"')

        connect = ldap.open(ldap_server)
        try:
            result = connect.search_s(
                ldap_search_base, ldap.SCOPE_SUBTREE, ldap_search_filter)
            if len(result) == 0:
                raise NotFoundError("KCHAUTH0004E", {'user_id': _user_id})
            return result[0][1]
        except ldap.NO_SUCH_OBJECT:
            raise NotFoundError("KCHAUTH0004E", {'user_id': _user_id})
