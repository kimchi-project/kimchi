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

import os
import tempfile
import lxml.etree as ET
from lxml.builder import E

import libvirt

from kimchi.exception import InvalidParameter, OperationFailed, TimeoutExpired
from kimchi.iscsi import TargetClient
from kimchi.rollbackcontext import RollbackContext
from kimchi.utils import kimchi_log, parse_cmd_output, run_command


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
        pool = E.pool(type='dir')
        pool.append(E.name(self.poolArgs['name']))
        pool.append(E.target(E.path(self.poolArgs['path'])))
        return ET.tostring(pool, encoding='unicode', pretty_print=True)


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
        # Due to an NFS bug (See Red Hat BZ 1023059), NFSv4 exports may take
        # 10-15 seconds to mount the first time.
        cmd_timeout = 15

        with RollbackContext() as rollback:
            rollback.prependDefer(os.rmdir, mnt_point)
            try:
                run_command(mount_cmd, cmd_timeout)
                rollback.prependDefer(run_command, umount_cmd, cmd_timeout)
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
        pool = E.pool(type='netfs')
        pool.append(E.name(self.poolArgs['name']))

        source = E.source()
        source.append(E.host(name=self.poolArgs['source']['host']))
        source.append(E.dir(path=self.poolArgs['source']['path']))

        pool.append(source)
        pool.append(E.target(E.path(self.path)))
        return ET.tostring(pool, encoding='unicode', pretty_print=True)


class LogicalPoolDef(StoragePoolDef):
    poolType = 'logical'

    def __init__(self, poolArgs):
        super(LogicalPoolDef, self).__init__(poolArgs)
        self.path = '/dev/' + self.poolArgs['name']

    @property
    def xml(self):
        # Required parameters
        # name:
        # type:
        # source[devices]:
        pool = E.pool(type='logical')
        pool.append(E.name(self.poolArgs['name']))

        source = E.source()
        for device_path in self.poolArgs['source']['devices']:
            source.append(E.device(path=device_path))

        pool.append(source)
        pool.append(E.target(E.path(self.path)))
        return ET.tostring(pool, encoding='unicode', pretty_print=True)


class ScsiPoolDef(StoragePoolDef):
    poolType = 'scsi'

    def prepare(self, conn=None):
        tmp_name = self.poolArgs['source']['name']
        self.poolArgs['source']['name'] = tmp_name.replace('scsi_', '')
        # fc_host adapters type are only available in libvirt >= 1.0.5
        if not self.poolArgs['fc_host_support']:
            self.poolArgs['source']['adapter']['type'] = 'scsi_host'
            msg = "Libvirt version <= 1.0.5. Setting SCSI host name as '%s'; "\
                  "setting SCSI adapter type as 'scsi_host'; "\
                  "ignoring wwnn and wwpn." % tmp_name
            kimchi_log.info(msg)
        # Path for Fibre Channel scsi hosts
        self.poolArgs['path'] = '/dev/disk/by-path'
        if not self.poolArgs['source']['adapter']['type']:
            self.poolArgs['source']['adapter']['type'] = 'scsi_host'

    @property
    def xml(self):
        # Required parameters
        # name:
        # source[adapter][type]:
        # source[name]:
        # source[adapter][wwnn]:
        # source[adapter][wwpn]:
        # path:
        pool = E.pool(type='scsi')
        pool.append(E.name(self.poolArgs['name']))

        adapter = E.adapter(type=self.poolArgs['source']['adapter']['type'])
        adapter.set('name', self.poolArgs['source']['name'])
        adapter.set('wwnn', self.poolArgs['source']['adapter']['wwnn'])
        adapter.set('wwpn', self.poolArgs['source']['adapter']['wwpn'])

        pool.append(E.source(adapter))
        pool.append(E.target(E.path(self.poolArgs['path'])))
        return ET.tostring(pool, encoding='unicode', pretty_print=True)


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
            secret = E.secret(ephemeral='no', private='yes')

            description = E.description('Secret for iSCSI storage pool %s' %
                                        self.poolArgs['name'])
            secret.append(description)
            secret.append(E.auth(type='chap', username=auth['username']))

            usage = E.usage(type='iscsi')
            usage.append(E.target(self.poolArgs['name']))
            secret.append(usage)
            virSecret = conn.secretDefineXML(ET.tostring(secret))

        virSecret.setValue(auth['password'])

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
        pool = E.pool(type='iscsi')
        pool.append(E.name(self.poolArgs['name']))

        host = E.host(name=self.poolArgs['source']['host'])
        port = self.poolArgs['source'].get('port')
        if port is not None:
            host.set('port', str(port))

        source = E.source(host)
        source.append(E.device(path=self.poolArgs['source']['target']))

        source_auth = self.poolArgs['source'].get('auth')
        if source_auth is not None:
            auth = E.auth(type='chap')
            auth.set('username', source_auth['username'])

            secret = E.secret(type='iscsi')
            secret.set('usage', self.poolArgs['name'])
            auth.append(secret)

            source.append(auth)

        pool.append(source)
        pool.append(E.target(E.path('/dev/disk/by-id')))
        return ET.tostring(pool, encoding='unicode', pretty_print=True)
