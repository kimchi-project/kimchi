# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2017
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
import tempfile
import unittest
import urllib
from functools import partial

import cherrypy
import mock
import requests
from requests.exceptions import ConnectionError
from wok.config import paths
from wok.plugins.kimchi.config import READONLY_POOL_TYPE
from wok.rollbackcontext import RollbackContext

from tests.utils import fake_auth_header
from tests.utils import HOST
from tests.utils import patch_auth
from tests.utils import PORT
from tests.utils import request
from tests.utils import rollback_wrapper
from tests.utils import run_server
from tests.utils import wait_task

model = None
objectstore_loc = tempfile.mktemp()
test_server = None


@mock.patch('wok.plugins.kimchi.config.get_object_store')
def setUpModule(func):
    func.return_value = objectstore_loc
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=False)
    model = cherrypy.tree.apps['/plugins/kimchi'].root.model


def tearDownModule():
    test_server.stop()
    os.unlink(objectstore_loc)


def _do_volume_test(self, model, pool_name):
    def _task_lookup(taskid):
        return json.loads(
            self.request(
                f'/plugins/kimchi/tasks/{taskid}').read().decode('utf-8')
        )

    uri = urllib.parse.quote(
        f'/plugins/kimchi/storagepools/{pool_name}/storagevolumes')
    resp = self.request(uri)
    self.assertEqual(200, resp.status)

    resp = self.request(urllib.parse.quote(
        f'/plugins/kimchi/storagepools/{pool_name}'))
    pool_info = json.loads(resp.read().decode('utf-8'))
    with RollbackContext() as rollback:
        # Create storage volume with 'capacity'
        vol = 'test-volume'
        vol_uri = uri + '/' + vol
        req = json.dumps(
            {'name': vol, 'format': 'raw', 'capacity': 1073741824}
        )  # 1 GiB
        resp = self.request(uri, req, 'POST')
        if pool_info['type'] in READONLY_POOL_TYPE:
            self.assertEqual(400, resp.status)
        else:
            rollback.prependDefer(
                rollback_wrapper, model.storagevolume_delete, pool_name, vol
            )
            self.assertEqual(202, resp.status)
            task_id = json.loads(resp.read().decode('utf-8'))['id']
            wait_task(_task_lookup, task_id)
            status = json.loads(
                self.request(
                    f'/plugins/kimchi/tasks/{task_id}').read().decode('utf-8')
            )
            self.assertEqual('finished', status['status'])
            vol_info = json.loads(self.request(vol_uri).read().decode('utf-8'))
            vol_info['name'] = vol
            vol_info['format'] = 'raw'
            vol_info['capacity'] = 1073741824

            # Resize the storage volume: increase its capacity to 2 GiB
            req = json.dumps({'size': 2147483648})  # 2 GiB
            resp = self.request(vol_uri + '/resize', req, 'POST')
            self.assertEqual(200, resp.status)
            storagevolume = json.loads(
                self.request(vol_uri).read().decode('utf-8'))
            self.assertEqual(2147483648, storagevolume['capacity'])

            # Resize the storage volume: decrease its capacity to 512 MiB
            # This test case may fail if libvirt does not include the fix for
            # https://bugzilla.redhat.com/show_bug.cgi?id=1021802
            req = json.dumps({'size': 536870912})  # 512 MiB
            resp = self.request(vol_uri + '/resize', req, 'POST')
            self.assertEqual(200, resp.status)
            storagevolume = json.loads(
                self.request(vol_uri).read().decode('utf-8'))
            self.assertEqual(536870912, storagevolume['capacity'])

            # Wipe the storage volume
            resp = self.request(vol_uri + '/wipe', '{}', 'POST')
            self.assertEqual(200, resp.status)
            storagevolume = json.loads(
                self.request(vol_uri).read().decode('utf-8'))
            self.assertEqual(0, storagevolume['allocation'])

            # Clone the storage volume
            vol_info = json.loads(self.request(vol_uri).read().decode('utf-8'))
            resp = self.request(vol_uri + '/clone', '{}', 'POST')
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read())
            cloned_vol_name = task['target_uri'].split('/')[-2]
            rollback.prependDefer(
                model.storagevolume_delete, pool_name, cloned_vol_name
            )
            wait_task(_task_lookup, task['id'])
            task = json.loads(
                self.request('/plugins/kimchi/tasks/%s' % task['id'])
                .read()
                .decode('utf-8')
            )
            self.assertEqual('finished', task['status'])
            resp = self.request(uri + '/' + cloned_vol_name)

            self.assertEqual(200, resp.status)
            cloned_vol = json.loads(resp.read().decode('utf-8'))

            self.assertNotEquals(vol_info['name'], cloned_vol['name'])
            self.assertNotEquals(vol_info['path'], cloned_vol['path'])
            for key in ['name', 'path', 'allocation']:
                del vol_info[key]
                del cloned_vol[key]

            self.assertEqual(vol_info, cloned_vol)

            # Delete the storage volume
            resp = self.request(vol_uri, '{}', 'DELETE')
            self.assertEqual(204, resp.status)
            resp = self.request(vol_uri)
            self.assertEqual(404, resp.status)

        # Storage volume upload
        # It is done through a sequence of POST and several PUT requests
        filename = 'COPYING.LGPL'
        filepath = os.path.join(paths.get_prefix(), filename)
        filesize = os.stat(filepath).st_size

        # Create storage volume for upload
        req = json.dumps(
            {'name': filename, 'format': 'raw',
                'capacity': filesize, 'upload': True}
        )
        resp = self.request(uri, req, 'POST')
        if pool_info['type'] in READONLY_POOL_TYPE:
            self.assertEqual(400, resp.status)
        else:
            rollback.prependDefer(
                rollback_wrapper, model.storagevolume_delete, pool_name, filename
            )
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read().decode('utf-8'))
            task_id = task['id']
            wait_task(_task_lookup, task_id)
            status = json.loads(
                self.request('/plugins/kimchi/tasks/%s' % task_id)
                .read()
                .decode('utf-8')
            )
            self.assertEqual('ready for upload', status['message'])

            # Upload volume content
            url = 'http://%s:%s' % (HOST, PORT) + uri + '/' + filename

            # Create a file with 5M to upload
            # Max body size is set to 4M so the upload should fail with 413.
            # Since nginx is not being used for testing anymore, and cherrypy
            # aborts connection instead of returning a 413 like nginx does,
            # test case expects for exception raised by cherrypy.
            newfile = '/tmp/5m-file'
            with open(newfile, 'wb') as fd:
                fd.seek(5 * 1024 * 1024 - 1)
                fd.write(b'\0')
            rollback.prependDefer(os.remove, newfile)

            with open(newfile, 'rb') as fd:
                with open(newfile + '.tmp', 'wb') as tmp_fd:
                    data = fd.read()
                    tmp_fd.write(data)

                with open(newfile + '.tmp', 'rb') as tmp_fd:
                    error_msg = 'Connection aborted'
                    with self.assertRaisesRegexp(ConnectionError, error_msg):
                        requests.put(
                            url,
                            data={'chunk_size': len(data)},
                            files={'chunk': tmp_fd},
                            verify=False,
                            headers=fake_auth_header(),
                        )

            # Do upload
            index = 0
            chunk_size = 2 * 1024
            content = ''

            with open(filepath, 'rb') as fd:
                while True:
                    with open(filepath + '.tmp', 'wb') as tmp_fd:
                        fd.seek(index * chunk_size)
                        data = fd.read(chunk_size)
                        tmp_fd.write(data)

                    with open(filepath + '.tmp', 'rb') as tmp_fd:
                        r = requests.put(
                            url,
                            data={'chunk_size': len(data)},
                            files={'chunk': tmp_fd},
                            verify=False,
                            headers=fake_auth_header(),
                        )
                        self.assertEqual(r.status_code, 200)
                        content += data.decode('utf-8')
                        index = index + 1

                    if len(data) < chunk_size:
                        break

            rollback.prependDefer(os.remove, filepath + '.tmp')
            resp = self.request(uri + '/' + filename)
            self.assertEqual(200, resp.status)
            uploaded_path = json.loads(resp.read().decode('utf-8'))['path']
            with open(uploaded_path) as fd:
                uploaded_content = fd.read()

            self.assertEqual(content, uploaded_content)

        # Create storage volume with 'url'
        url = 'https://github.com/kimchi-project/kimchi/raw/master/COPYING'
        req = json.dumps({'url': url})
        resp = self.request(uri, req, 'POST')

        if pool_info['type'] in READONLY_POOL_TYPE:
            self.assertEqual(400, resp.status)
        else:
            rollback.prependDefer(
                model.storagevolume_delete, pool_name, 'COPYING')
            self.assertEqual(202, resp.status)
            task = json.loads(resp.read().decode('utf-8'))
            wait_task(_task_lookup, task['id'])
            resp = self.request(uri + '/COPYING')
            self.assertEqual(200, resp.status)


class StorageVolumeTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request)

    def test_get_storagevolume(self):
        uri = '/plugins/kimchi/storagepools/default/storagevolumes'
        resp = self.request(uri)
        self.assertEqual(200, resp.status)

        keys = [
            'name',
            'type',
            'capacity',
            'allocation',
            'path',
            'used_by',
            'format',
            'isvalid',
            'has_permission',
        ]
        for vol in json.loads(resp.read().decode('utf-8')):
            resp = self.request(uri + '/' + vol['name'])
            self.assertEqual(200, resp.status)

            all_keys = keys[:]
            vol_info = json.loads(resp.read().decode('utf-8'))
            if vol_info['format'] == 'iso':
                all_keys.extend(['os_distro', 'os_version', 'bootable'])

            self.assertEqual(sorted(all_keys), sorted(vol_info.keys()))

    def test_storagevolume_action(self):
        _do_volume_test(self, model, 'default')
