#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

import copy
import os
import tempfile

import libvirt

from kimchi.exception import InvalidParameter, OperationFailed, TimeoutExpired
from kimchi.iscsi import TargetClient
from kimchi.rollbackcontext import RollbackContext
from kimchi.utils import parse_cmd_output, run_command


class StoragePoolDef(object):
    @classmethod
    def create(cls, poolArgs):
        for klass in cls.__subclasses__():
            if poolArgs['type'] == klass.poolType:
                return klass(poolArgs)
        raise OperationFailed("KCHPOOL0014E", {'type': poolArgs['type']})

    def __init__(self, poolArgs):
        self.poolArgs = poolArgs

    def prepare(self, conn):
        ''' Validate pool arguments and perform preparations. Operation which
        would cause side effect should be put here. Subclasses can optionally
        override this method, or it always succeeds by default. '''
        pass

    @property
    def xml(self):
        ''' Subclasses have to override this method to actually generate the
        storage pool XML definition. Should cause no side effect and be
        idempotent'''
        # TODO: When add new pool type, should also add the related test in
        # tests/test_storagepool.py
        raise OperationFailed("KCHPOOL0015E", {'pool': self})


class DirPoolDef(StoragePoolDef):
    poolType = 'dir'

    @property
    def xml(self):
        # Required parameters
        # name:
        # type:
        # path:
        xml = u"""
        <pool type='dir'>
          <name>{name}</name>
          <target>
            <path>{path}</path>
          </target>
        </pool>
        """.format(**self.poolArgs)
        return xml


class NetfsPoolDef(StoragePoolDef):
    poolType = 'netfs'

    def __init__(self, poolArgs):
        super(NetfsPoolDef, self).__init__(poolArgs)
        self.path = '/var/lib/kimchi/nfs_mount/' + self.poolArgs['name']

    def prepare(self, conn):
        mnt_point = tempfile.mkdtemp(dir='/tmp')
        export_path = "%s:%s" % (
            self.poolArgs['source']['host'], self.poolArgs['source']['path'])
        mount_cmd = ["mount", "-o", 'soft,timeo=100,retrans=3,retry=0',
                     export_path, mnt_point]
        umount_cmd = ["umount", "-f", export_path]
        mounted = False

        with RollbackContext() as rollback:
            rollback.prependDefer(os.rmdir, mnt_point)
            try:
                run_command(mount_cmd, 30)
                rollback.prependDefer(run_command, umount_cmd)
            except TimeoutExpired:
                raise InvalidParameter("KCHPOOL0012E", {'path': export_path})

            with open("/proc/mounts", "rb") as f:
                rawMounts = f.read()
            output_items = ['dev_path', 'mnt_point', 'type']
            mounts = parse_cmd_output(rawMounts, output_items)
            for item in mounts:
                if 'dev_path' in item and item['dev_path'] == export_path:
                    mounted = True

            if not mounted:
                raise InvalidParameter("KCHPOOL0013E", {'path': export_path})

    @property
    def xml(self):
        # Required parameters
        # name:
        # type:
        # source[host]:
        # source[path]:
        poolArgs = copy.deepcopy(self.poolArgs)
        poolArgs['path'] = self.path
        xml = u"""
        <pool type='netfs'>
          <name>{name}</name>
          <source>
            <host name='{source[host]}'/>
            <dir path='{source[path]}'/>
          </source>
          <target>
            <path>{path}</path>
          </target>
        </pool>
        """.format(**poolArgs)
        return xml


class LogicalPoolDef(StoragePoolDef):
    poolType = 'logical'

    def __init__(self, poolArgs):
        super(LogicalPoolDef, self).__init__(poolArgs)
        self.path = '/var/lib/kimchi/logical_mount/' + self.poolArgs['name']

    @property
    def xml(self):
        # Required parameters
        # name:
        # type:
        # source[devices]:
        poolArgs = copy.deepcopy(self.poolArgs)
        devices = []
        for device_path in poolArgs['source']['devices']:
            devices.append('<device path="%s" />' % device_path)

        poolArgs['source']['devices'] = ''.join(devices)
        poolArgs['path'] = self.path

        xml = u"""
        <pool type='logical'>
        <name>{name}</name>
            <source>
            {source[devices]}
            </source>
        <target>
            <path>{path}</path>
        </target>
        </pool>
        """.format(**poolArgs)
        return xml


class IscsiPoolDef(StoragePoolDef):
    poolType = 'iscsi'

    def prepare(self, conn):
        source = self.poolArgs['source']
        if not TargetClient(**source).validate():
            msg_args = {'host': source['host'], 'target': source['target']}
            raise OperationFailed("KCHISCSI0002E", msg_args)
        self._prepare_auth(conn)

    def _prepare_auth(self, conn):
        try:
            auth = self.poolArgs['source']['auth']
        except KeyError:
            return

        try:
            virSecret = conn.secretLookupByUsage(
                libvirt.VIR_SECRET_USAGE_TYPE_ISCSI, self.poolArgs['name'])
        except libvirt.libvirtError:
            xml = '''
            <secret ephemeral='no' private='yes'>
              <description>Secret for iSCSI storage pool {name}</description>
              <auth type='chap' username='{username}'/>
              <usage type='iscsi'>
                <target>{name}</target>
              </usage>
            </secret>'''.format(name=self.poolArgs['name'],
                                username=auth['username'])
            virSecret = conn.secretDefineXML(xml)

        virSecret.setValue(auth['password'])

    def _format_port(self, poolArgs):
        try:
            port = poolArgs['source']['port']
        except KeyError:
            return ""
        return "port='%s'" % port

    def _format_auth(self, poolArgs):
        try:
            auth = poolArgs['source']['auth']
        except KeyError:
            return ""

        return '''
        <auth type='chap' username='{username}'>
          <secret type='iscsi' usage='{name}'/>
        </auth>'''.format(name=poolArgs['name'], username=auth['username'])

    @property
    def xml(self):
        # Required parameters
        # name:
        # type:
        # source[host]:
        # source[target]:
        #
        # Optional parameters
        # source[port]:
        poolArgs = copy.deepcopy(self.poolArgs)
        poolArgs['source'].update({'port': self._format_port(poolArgs),
                                   'auth': self._format_auth(poolArgs)})
        poolArgs['path'] = '/dev/disk/by-id'

        xml = u"""
        <pool type='iscsi'>
          <name>{name}</name>
          <source>
            <host name='{source[host]}' {source[port]}/>
            <device path='{source[target]}'/>
            {source[auth]}
          </source>
          <target>
            <path>{path}</path>
          </target>
        </pool>
        """.format(**poolArgs)
        return xml
