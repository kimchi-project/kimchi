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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301USA

import subprocess


from kimchi.exception import OperationFailed


class TargetClient(object):
    def __init__(self, target, host, port=None, auth=None):
        self.portal = host + ("" if port is None else ":%s" % port)
        self.target = target
        self.auth = auth
        self.targetCmd = ['iscsiadm', '--mode', 'node', '--targetname',
                          self.target, '--portal', self.portal]

    def _update_db(self, Name, Value):
        self._run_cmd(['--op=update', '--name', Name, '--value', Value])

    def _update_auth(self):
        if self.auth is None:
            items = (('node.session.auth.authmethod', 'None'),
                     ('node.session.auth.username', ''),
                     ('node.session.auth.password', ''))
        else:
            items = (('node.session.auth.authmethod', 'CHAP'),
                     ('node.session.auth.username', self.auth['username']),
                     ('node.session.auth.password', self.auth['password']))
        for name, value in items:
            self._update_db(name, value)

    def _run_cmd(self, cmd):
        iscsiadm = subprocess.Popen(
            self.targetCmd + cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = iscsiadm.communicate()
        if iscsiadm.returncode != 0:
            msg_args = {'portal': self.portal, 'err': err}
            raise OperationFailed("KCHISCSI0001E", msg_args)
        return out

    def _discover(self):
        iscsiadm = subprocess.Popen(
            ['iscsiadm', '--mode', 'discovery', '--type', 'sendtargets',
             '--portal', self.portal],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = iscsiadm.communicate()
        if iscsiadm.returncode != 0:
            msg_args = {'portal': self.portal, 'err': err}
            raise OperationFailed("KCHISCSI0001E", msg_args)
        return out

    def _run_op(self, op):
        self._run_cmd(['--' + op])

    def login(self):
        self._discover()
        self._update_auth()
        self._run_op('login')

    def logout(self):
        self._run_op('logout')

    def validate(self):
        try:
            self.login()
        except OperationFailed:
            return False

        self.logout()
        return True
