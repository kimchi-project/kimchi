# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM, Corp. 2015
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

import json
import os
import requests
import unittest

from functools import partial

from kimchi.config import paths, READONLY_POOL_TYPE
from kimchi.model.model import Model
from kimchi.mockmodel import MockModel
from kimchi.rollbackcontext import RollbackContext
from utils import fake_auth_header, get_free_port, patch_auth, request
from utils import rollback_wrapper, run_server, wait_task


model = None
test_server = None
host = None
port = None
ssl_port = None
cherrypy_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port, cherrypy_port

    patch_auth()
    model = Model(None, '/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


def _do_volume_test(self, model, host, ssl_port, pool_name):
    def _task_lookup(taskid):
        return json.loads(self.request('/tasks/%s' % taskid).read())

    uri = '/storagepools/%s/storagevolumes' % pool_name.encode('utf-8')
    resp = self.request(uri)
    self.assertEquals(200, resp.status)

    resp = self.request('/storagepools/%s' % pool_name.encode('utf-8'))
    pool_info = json.loads(resp.read())
    with RollbackContext() as rollback:
        # Create storage volume with 'capacity'
        vol = 'test-volume'
        vol_uri = uri + '/' + vol
        req = json.dumps({'name': vol, 'format': 'raw',
                          'capacity': 1073741824})  # 1 GiB
        resp = self.request(uri, req, 'POST')
        if pool_info['type'] in READONLY_POOL_TYPE:
            self.assertEquals(400, resp.status)
        else:
            rollback.prependDefer(rollback_wrapper, model.storagevolume_delete,
                                  pool_name, vol)
            self.assertEquals(202, resp.status)
            task_id = json.loads(resp.read())['id']
            wait_task(_task_lookup, task_id)
            status = json.loads(self.request('/tasks/%s' % task_id).read())
            self.assertEquals('finished', status['status'])
            vol_info = json.loads(self.request(vol_uri).read())
            vol_info['name'] = vol
            vol_info['format'] = 'raw'
            vol_info['capacity'] = 1073741824

            # Resize the storage volume: increase its capacity to 2 GiB
            req = json.dumps({'size': 2147483648})  # 2 GiB
            resp = self.request(vol_uri + '/resize', req, 'POST')
            self.assertEquals(200, resp.status)
            storagevolume = json.loads(self.request(vol_uri).read())
            self.assertEquals(2147483648, storagevolume['capacity'])

            # Resize the storage volume: decrease its capacity to 512 MiB
            # FIXME: Due a libvirt bug it is not possible to decrease the
            # volume capacity
            # For reference:
            # - https://bugzilla.redhat.com/show_bug.cgi?id=1021802
            req = json.dumps({'size': 536870912})  # 512 MiB
            resp = self.request(vol_uri + '/resize', req, 'POST')
            # It is only possible when using MockModel
            if isinstance(model, MockModel):
                self.assertEquals(200, resp.status)
                storagevolume = json.loads(self.request(vol_uri).read())
                self.assertEquals(536870912, storagevolume['capacity'])
            else:
                self.assertEquals(500, resp.status)

            # Wipe the storage volume
            resp = self.request(vol_uri + '/wipe', '{}', 'POST')
            self.assertEquals(200, resp.status)
            storagevolume = json.loads(self.request(vol_uri).read())
            self.assertEquals(0, storagevolume['allocation'])

            # Clone the storage volume
            vol_info = json.loads(self.request(vol_uri).read())
            resp = self.request(vol_uri + '/clone', '{}', 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            cloned_vol_name = task['target_uri'].split('/')[-1]
            rollback.prependDefer(model.storagevolume_delete, pool_name,
                                  cloned_vol_name)
            wait_task(_task_lookup, task['id'])
            task = json.loads(self.request('/tasks/%s' % task['id']).read())
            self.assertEquals('finished', task['status'])
            resp = self.request(uri + '/' + cloned_vol_name.encode('utf-8'))

            self.assertEquals(200, resp.status)
            cloned_vol = json.loads(resp.read())

            self.assertNotEquals(vol_info['name'], cloned_vol['name'])
            self.assertNotEquals(vol_info['path'], cloned_vol['path'])
            for key in ['name', 'path', 'allocation']:
                del vol_info[key]
                del cloned_vol[key]

            self.assertEquals(vol_info, cloned_vol)

            # Delete the storage volume
            resp = self.request(vol_uri, '{}', 'DELETE')
            self.assertEquals(204, resp.status)
            resp = self.request(vol_uri)
            self.assertEquals(404, resp.status)

        # Storage volume upload
        # It is done through a sequence of POST and several PUT requests
        filename = 'COPYING.LGPL'
        filepath = os.path.join(paths.get_prefix(), filename)
        filesize = os.stat(filepath).st_size

        # Create storage volume for upload
        req = json.dumps({'name': filename, 'format': 'raw',
                          'capacity': filesize, 'upload': True})
        resp = self.request(uri, req, 'POST')
        if pool_info['type'] in READONLY_POOL_TYPE:
            self.assertEquals(400, resp.status)
        else:
            rollback.prependDefer(rollback_wrapper, model.storagevolume_delete,
                                  pool_name, filename)
            self.assertEquals(202, resp.status)
            task_id = json.loads(resp.read())['id']
            wait_task(_task_lookup, task_id)
            status = json.loads(self.request('/tasks/%s' % task_id).read())
            self.assertEquals('ready for upload', status['message'])

            # Upload volume content
            url = 'https://%s:%s' % (host, ssl_port) + uri + '/' + filename

            # Create a file with 5M to upload
            # Max body size is set to 4M so the upload will fail with 413
            newfile = '/tmp/5m-file'
            with open(newfile, 'wb') as fd:
                fd.seek(5*1024*1024-1)
                fd.write("\0")
            rollback.prependDefer(os.remove, newfile)

            with open(newfile, 'rb') as fd:
                with open(newfile + '.tmp', 'wb') as tmp_fd:
                    data = fd.read()
                    tmp_fd.write(data)

                with open(newfile + '.tmp', 'rb') as tmp_fd:
                    r = requests.put(url, data={'chunk_size': len(data)},
                                     files={'chunk': tmp_fd},
                                     verify=False,
                                     headers=fake_auth_header())
                    self.assertEquals(r.status_code, 413)

            # Do upload
            index = 0
            chunk_size = 2 * 1024
            content = ''

            with open(filepath, 'rb') as fd:
                while True:
                    with open(filepath + '.tmp', 'wb') as tmp_fd:
                        fd.seek(index*chunk_size)
                        data = fd.read(chunk_size)
                        tmp_fd.write(data)

                    with open(filepath + '.tmp', 'rb') as tmp_fd:
                        r = requests.put(url, data={'chunk_size': len(data)},
                                         files={'chunk': tmp_fd},
                                         verify=False,
                                         headers=fake_auth_header())
                        self.assertEquals(r.status_code, 200)
                        content += data
                        index = index + 1

                    if len(data) < chunk_size:
                        break

            rollback.prependDefer(os.remove, filepath + '.tmp')
            resp = self.request(uri + '/' + filename)
            self.assertEquals(200, resp.status)
            uploaded_path = json.loads(resp.read())['path']
            with open(uploaded_path) as fd:
                uploaded_content = fd.read()

            self.assertEquals(content, uploaded_content)

        # Create storage volume with 'url'
        url = 'https://github.com/kimchi-project/kimchi/raw/master/COPYING'
        req = json.dumps({'url': url})
        resp = self.request(uri, req, 'POST')

        if pool_info['type'] in READONLY_POOL_TYPE:
            self.assertEquals(400, resp.status)
        else:
            rollback.prependDefer(model.storagevolume_delete, pool_name,
                                  'COPYING')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            wait_task(_task_lookup, task['id'])
            resp = self.request(uri + '/COPYING')
            self.assertEquals(200, resp.status)


class StorageVolumeTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)

    def test_get_storagevolume(self):
        uri = '/storagepools/default/storagevolumes'
        resp = self.request(uri)
        self.assertEquals(200, resp.status)

        keys = [u'name', u'type', u'capacity', u'allocation', u'path',
                u'used_by', u'format']
        for vol in json.loads(resp.read()):
            resp = self.request(uri + '/' + vol['name'])
            self.assertEquals(200, resp.status)

            all_keys = keys[:]
            vol_info = json.loads(resp.read())
            if vol_info['format'] == 'iso':
                all_keys.extend([u'os_distro', u'os_version', u'bootable'])

            self.assertEquals(sorted(all_keys), sorted(vol_info.keys()))

    def test_storagevolume_action(self):
        _do_volume_test(self, model, host, ssl_port, 'default')
