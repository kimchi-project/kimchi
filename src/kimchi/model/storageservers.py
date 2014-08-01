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

from kimchi.exception import NotFoundError
from kimchi.model.storagepools import StoragePoolModel, StoragePoolsModel

# Types of remote storage servers supported
STORAGE_SERVERS = ['netfs', 'iscsi']


class StorageServersModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.pool = StoragePoolModel(**kargs)
        self.pools = StoragePoolsModel(**kargs)

    def get_list(self, _target_type=None):
        if not _target_type:
            target_type = STORAGE_SERVERS
        else:
            target_type = [_target_type]

        pools = self.pools.get_list()

        server_list = []
        for pool in pools:
            try:
                pool_info = self.pool.lookup(pool)
                if (pool_info['type'] in target_type and
                        pool_info['source']['addr'] not in server_list):
                    # Avoid to add same server for multiple times
                    # if it hosts more than one storage type
                    server_list.append(pool_info['source']['addr'])
            except NotFoundError:
                pass

        return server_list


class StorageServerModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.pool = StoragePoolModel(**kargs)

    def lookup(self, server):
        conn = self.conn.get()
        pools = conn.listStoragePools()
        pools += conn.listDefinedStoragePools()
        for pool in pools:
            try:
                pool_info = self.pool.lookup(pool)
                if (pool_info['type'] in STORAGE_SERVERS and
                        pool_info['source']['addr'] == server):
                    info = dict(host=server)
                    if (pool_info['type'] == "iscsi" and
                       'port' in pool_info['source']):
                        info["port"] = pool_info['source']['port']
                    return info
            except NotFoundError:
                # Avoid inconsistent pool result because of lease between list
                # lookup
                pass

        raise NotFoundError("KCHSR0001E", {'server': server})
