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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import lxml.etree as ET
import unittest

from kimchi.model.libvirtstoragepool import StoragePoolDef


class StoragepoolXMLTests(unittest.TestCase):
    def test_get_storagepool_xml(self):
        poolDefs = [
            {'def':
                {'type': 'dir',
                 'name': 'unitTestDirPool',
                 'path': '/var/temp/images'},
             'xml':
             """
             <pool type='dir'>
               <name>unitTestDirPool</name>
               <target>
                 <path>/var/temp/images</path>
               </target>
             </pool>
             """},
            {'def':
                {'type': 'netfs',
                 'name': 'unitTestNFSPool',
                 'source': {'host': '127.0.0.1',
                            'path': '/var/export'}},
             'xml':
             """
             <pool type='netfs'>
               <name>unitTestNFSPool</name>
               <source>
                 <host name='127.0.0.1'/>
                 <dir path='/var/export'/>
               </source>
               <target>
                 <path>/var/lib/kimchi/nfs_mount/unitTestNFSPool</path>
               </target>
             </pool>
             """},
            {'def':
                {'type': 'logical',
                 'name': 'unitTestLogicalPool',
                 'source': {'devices': ['/dev/hda', '/dev/hdb']}},
             'xml':
             """
             <pool type='logical'>
             <name>unitTestLogicalPool</name>
                 <source>
                     <device path="/dev/hda" />
                     <device path="/dev/hdb" />
                 </source>
             <target>
                 <path>/dev/unitTestLogicalPool</path>
             </target>
             </pool>
             """},
            {'def':
                {'type': 'iscsi',
                 'name': 'unitTestISCSIPool',
                 'source': {
                     'host': '127.0.0.1',
                     'target': 'iqn.2003-01.org.linux-iscsi.localhost'}},
             'xml':
             """
             <pool type='iscsi'>
               <name>unitTestISCSIPool</name>
               <source>
                 <host name='127.0.0.1' />
                 <device path='iqn.2003-01.org.linux-iscsi.localhost'/>
               </source>
               <target>
                 <path>/dev/disk/by-id</path>
               </target>
             </pool>
             """},
            {'def':
                {'type': 'iscsi',
                 'name': 'unitTestISCSIPoolPort',
                 'source': {
                     'host': '127.0.0.1',
                     'port': 3266,
                     'target': 'iqn.2003-01.org.linux-iscsi.localhost'}},
             'xml':
             """
             <pool type='iscsi'>
               <name>unitTestISCSIPoolPort</name>
               <source>
                 <host name='127.0.0.1' port='3266' />
                 <device path='iqn.2003-01.org.linux-iscsi.localhost'/>
               </source>
               <target>
                 <path>/dev/disk/by-id</path>
               </target>
             </pool>
             """},
            {'def':
                {'type': 'iscsi',
                 'name': 'unitTestISCSIPoolAuth',
                 'source': {
                     'host': '127.0.0.1',
                     'target': 'iqn.2003-01.org.linux-iscsi.localhost',
                     'auth': {'username': 'testUser',
                              'password': 'ActuallyNotUsedInPoolXML'}}},
             'xml':
             """
             <pool type='iscsi'>
               <name>unitTestISCSIPoolAuth</name>
               <source>
                 <host name='127.0.0.1' />
                 <device path='iqn.2003-01.org.linux-iscsi.localhost'/>
                 <auth type='chap' username='testUser'>
                   <secret type='iscsi' usage='unitTestISCSIPoolAuth'/>
                 </auth>
               </source>
               <target>
                 <path>/dev/disk/by-id</path>
               </target>
             </pool>
             """},
            {'def':
                {'type': 'scsi',
                 'name': 'unitTestSCSIFCPool',
                 'path': '/dev/disk/by-path',
                 'source': {
                     'name': 'scsi_host3',
                     'adapter': {
                         'type': 'fc_host',
                         'wwpn': '0123456789abcdef',
                         'wwnn': 'abcdef0123456789'}}},
             'xml':
             """
             <pool type='scsi'>
               <name>unitTestSCSIFCPool</name>
               <source>
                   <adapter type='fc_host' name='scsi_host3'
                     wwnn='abcdef0123456789' wwpn='0123456789abcdef'></adapter>
               </source>
               <target>
                   <path>/dev/disk/by-path</path>
               </target>
             </pool>
             """}]

        for poolDef in poolDefs:
            defObj = StoragePoolDef.create(poolDef['def'])
            xmlStr = defObj.xml

            parser = ET.XMLParser(remove_blank_text=True)
            t1 = ET.fromstring(xmlStr, parser)
            t2 = ET.fromstring(poolDef['xml'], parser)
            self.assertEquals(ET.tostring(t1), ET.tostring(t2))
