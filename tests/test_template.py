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
import unittest

from functools import partial

from kimchi.config import READONLY_POOL_TYPE
from kimchi.mockmodel import MockModel
from utils import get_free_port, patch_auth, request, run_server


model = None
test_server = None
host = None
port = None
ssl_port = None
cherrypy_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port, cherrypy_port

    patch_auth()
    model = MockModel('/tmp/obj-store-test')
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)
        model.reset()

    def test_tmpl_lifecycle(self):
        resp = self.request('/templates')
        self.assertEquals(200, resp.status)
        self.assertEquals(0, len(json.loads(resp.read())))

        # Create a template without cdrom and disk specified fails with 400
        t = {'name': 'test', 'os_distro': 'ImagineOS',
             'os_version': '1.0', 'memory': 1024, 'cpus': 1,
             'storagepool': '/storagepools/alt'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(400, resp.status)

        # Create a template
        t = {'name': 'test', 'cdrom': '/tmp/mock.iso'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the template
        keys = ['name', 'icon', 'invalid', 'os_distro', 'os_version', 'cpus',
                'memory', 'cdrom', 'disks', 'storagepool', 'networks',
                'folder', 'graphics', 'cpu_info']
        tmpl = json.loads(self.request('/templates/test').read())
        self.assertEquals(sorted(tmpl.keys()), sorted(keys))

        # Verify if default disk format was configured
        self.assertEquals(tmpl['disks'][0]['format'], 'qcow2')

        # Clone a template
        resp = self.request('/templates/test/clone', '{}', 'POST')
        self.assertEquals(303, resp.status)

        # Verify the cloned template
        tmpl_cloned = json.loads(self.request('/templates/test-clone1').read())
        del tmpl['name']
        del tmpl_cloned['name']
        self.assertEquals(tmpl, tmpl_cloned)

        # Delete the cloned template
        resp = self.request('/templates/test-clone1', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Create a template with same name fails with 400
        req = json.dumps({'name': 'test', 'cdrom': '/tmp/mock.iso'})
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(400, resp.status)

        # Create an image based template
        open('/tmp/mock.img', 'w').close()
        t = {'name': 'test_img_template', 'disks': [{'base': '/tmp/mock.img'}]}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)
        os.remove('/tmp/mock.img')

        # Test disk format
        t = {'name': 'test-format', 'cdrom': '/tmp/mock.iso',
             'disks': [{'index': 0, 'size': 10, 'format': 'vmdk'}]}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)
        tmpl = json.loads(self.request('/templates/test-format').read())
        self.assertEquals(tmpl['disks'][0]['format'], 'vmdk')

    def test_customized_tmpl(self):
        # Create a template
        t = {'name': 'test', 'cdrom': '/tmp/mock.iso'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)
        tmpl = json.loads(self.request('/templates/test').read())

        # Update name
        new_name = u'kīмсhīTmpl'
        new_tmpl_uri = '/templates/%s' % new_name.encode('utf-8')
        req = json.dumps({'name': new_name})
        resp = self.request('/templates/test', req, 'PUT')
        self.assertEquals(303, resp.status)
        resp = self.request(new_tmpl_uri)
        update_tmpl = json.loads(resp.read())
        self.assertEquals(new_name, update_tmpl['name'])
        del tmpl['name']
        del update_tmpl['name']
        self.assertEquals(tmpl, update_tmpl)

        # Update icon
        req = json.dumps({'icon': 'images/icon-fedora.png'})
        resp = self.request(new_tmpl_uri, req, 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals('images/icon-fedora.png', update_tmpl['icon'])

        # Update os_distro and os_version
        req = json.dumps({'os_distro': 'fedora', 'os_version': '21'})
        resp = self.request(new_tmpl_uri, req, 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals('fedora', update_tmpl['os_distro'])
        self.assertEquals('21', update_tmpl['os_version'])

        # Update cpus
        req = json.dumps({'cpus': 2})
        resp = self.request(new_tmpl_uri, req, 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals(2, update_tmpl['cpus'])

        # Update memory
        req = json.dumps({'memory': 2048})
        resp = self.request(new_tmpl_uri, req, 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals(2048, update_tmpl['memory'])

        # Update cpu_info
        resp = self.request(new_tmpl_uri)
        cpu_info = json.loads(resp.read())['cpu_info']
        self.assertEquals(cpu_info, {})
        self.assertEquals(cpu_info.get('topology'), None)

        cpu_info_data = {'cpu_info': {'topology': {'sockets': 1,
                                                   'cores': 2,
                                                   'threads': 1}}}
        resp = self.request(new_tmpl_uri, json.dumps(cpu_info_data), 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals(update_tmpl['cpu_info'], cpu_info_data['cpu_info'])

        # Update cdrom
        cdrom_data = {'cdrom': '/tmp/mock2.iso'}
        resp = self.request(new_tmpl_uri, json.dumps(cdrom_data), 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals(update_tmpl['cdrom'], cdrom_data['cdrom'])

        # Update disks
        disk_data = {'disks': [{'index': 0, 'size': 10},
                               {'index': 1, 'size': 20}]}
        resp = self.request(new_tmpl_uri, json.dumps(disk_data), 'PUT')
        self.assertEquals(200, resp.status)
        resp = self.request(new_tmpl_uri)
        self.assertEquals(200, resp.status)
        updated_tmpl = json.loads(resp.read())
        self.assertEquals(updated_tmpl['disks'], disk_data['disks'])

        # For all supported types, edit the template and check if
        # the change was made.
        disk_types = ['bochs', 'cloop', 'cow', 'dmg', 'qcow', 'qcow2',
                      'qed', 'raw', 'vmdk', 'vpc']
        for disk_type in disk_types:
            disk_data = {'disks': [{'index': 0, 'format': disk_type,
                                    'size': 10}]}
            resp = self.request(new_tmpl_uri, json.dumps(disk_data), 'PUT')
            self.assertEquals(200, resp.status)

            resp = self.request(new_tmpl_uri)
            self.assertEquals(200, resp.status)
            updated_tmpl = json.loads(resp.read())
            self.assertEquals(updated_tmpl['disks'], disk_data['disks'])

        # Update folder
        folder_data = {'folder': ['mock', 'isos']}
        resp = self.request(new_tmpl_uri, json.dumps(folder_data), 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals(update_tmpl['folder'], folder_data['folder'])

        # Update graphics
        req = json.dumps({'graphics': {'type': 'spice'}})
        resp = self.request(new_tmpl_uri, req, 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals('spice', update_tmpl['graphics']['type'])

        req = json.dumps({'graphics': {'type': 'vnc', 'listen': 'fe00::0'}})
        resp = self.request(new_tmpl_uri, req, 'PUT')
        self.assertEquals(200, resp.status)
        update_tmpl = json.loads(resp.read())
        self.assertEquals('vnc', update_tmpl['graphics']['type'])
        self.assertEquals('fe00::0', update_tmpl['graphics']['listen'])

    def test_customized_network(self):
        # Create a template
        t = {'name': 'test', 'cdrom': '/tmp/mock.iso'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Create networks to be used for testing
        networks = [{'name': u'kīмсhī-пet', 'connection': 'isolated'},
                    {'name': u'nat-network', 'connection': 'nat'},
                    {'name': u'subnet-network', 'connection': 'nat',
                     'subnet': '127.0.100.0/24'}]

        # Verify the current system has at least one interface to create a
        # bridged network
        interfaces = json.loads(self.request('/interfaces?type=nic').read())
        if len(interfaces) > 0:
            iface = interfaces[0]['name']
            networks.append({'name': u'bridge-network', 'connection': 'bridge',
                             'interface': iface})
            networks.append({'name': u'bridge-network', 'connection': 'bridge',
                             'interface': iface, 'vlan_id': 987})

        tmpl_nets = []
        for net in networks:
            self.request('/networks', json.dumps(net), 'POST')
            tmpl_nets.append(net['name'])
            req = json.dumps({'networks': tmpl_nets})
            resp = self.request('/templates/test', req, 'PUT')
            self.assertEquals(200, resp.status)

    def test_customized_storagepool(self):
        # Create a template
        t = {'name': 'test', 'cdrom': '/tmp/mock.iso'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # MockModel always returns 2 partitions (vdx, vdz)
        partitions = json.loads(self.request('/host/partitions').read())
        devs = [dev['path'] for dev in partitions]

        # MockModel always returns 3 FC devices
        fc_devs = json.loads(self.request('/host/devices?_cap=fc_host').read())
        fc_devs = [dev['name'] for dev in fc_devs]

        poolDefs = [
            {'type': 'dir', 'name': u'kīмсhīUnitTestDirPool',
             'path': '/tmp/kimchi-images'},
            {'type': 'netfs', 'name': u'kīмсhīUnitTestNSFPool',
             'source': {'host': 'localhost',
                        'path': '/var/lib/kimchi/nfs-pool'}},
            {'type': 'scsi', 'name': u'kīмсhīUnitTestSCSIFCPool',
             'source': {'adapter_name': fc_devs[0]}},
            {'type': 'iscsi', 'name': u'kīмсhīUnitTestISCSIPool',
             'source': {'host': '127.0.0.1',
                        'target': 'iqn.2015-01.localhost.kimchiUnitTest'}},
            {'type': 'logical', 'name': u'kīмсhīUnitTestLogicalPool',
             'source': {'devices': [devs[0]]}}]

        for pool in poolDefs:
            self.request('/storagepools', json.dumps(pool), 'POST')
            pool_uri = '/storagepools/%s' % pool['name'].encode('utf-8')
            self.request(pool_uri + '/activate', '{}', 'POST')

            req = None
            if pool['type'] in READONLY_POOL_TYPE:
                resp = self.request(pool_uri + '/storagevolumes')
                vols = json.loads(resp.read())
                if len(vols) > 0:
                    vol = vols[0]['name']
                    req = json.dumps({'storagepool': pool_uri,
                                      'disks': [{'volume': vol}]})
            else:
                req = json.dumps({'storagepool': pool_uri})

            if req is not None:
                resp = self.request('/templates/test', req, 'PUT')
                self.assertEquals(200, resp.status)

    def test_tmpl_integrity(self):
        # Create a network and a pool for testing template integrity
        net = {'name': u'nat-network', 'connection': 'nat'}
        self.request('/networks', json.dumps(net), 'POST')

        pool = {'type': 'dir', 'name': 'dir-pool', 'path': '/tmp/dir-pool'}
        self.request('/storagepools', json.dumps(pool), 'POST')
        pool_uri = '/storagepools/%s' % pool['name'].encode('utf-8')
        self.request(pool_uri + '/activate', '{}', 'POST')

        # Create a template using the custom network and pool
        t = {'name': 'test', 'cdrom': '/tmp/mock.iso',
             'networks': ['nat-network'],
             'storagepool': '/storagepools/dir-pool'}
        req = json.dumps(t)
        resp = self.request('/templates', req, 'POST')
        self.assertEquals(201, resp.status)

        # Try to delete network
        # It should fail as it is associated to a template
        resp = self.request('/networks/nat-network', '{}', 'DELETE')
        self.assertIn("KCHNET0017E", json.loads(resp.read())["reason"])

        # Update template to release network and then delete it
        params = {'networks': []}
        req = json.dumps(params)
        self.request('/templates/test', req, 'PUT')
        resp = self.request('/networks/nat-network', '{}', 'DELETE')
        self.assertEquals(204, resp.status)

        # Try to delete the storagepool
        # It should fail as it is associated to a template
        resp = self.request('/storagepools/dir-pool', '{}', 'DELETE')
        self.assertEquals(400, resp.status)

        # Verify the template
        res = json.loads(self.request('/templates/test').read())
        self.assertEquals(res['invalid']['cdrom'], ['/tmp/mock.iso'])
