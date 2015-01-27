#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
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

import time

import libvirt
import lxml.etree as ET
from lxml import objectify
from lxml.builder import E

from kimchi.exception import InvalidOperation, NotFoundError, OperationFailed
from kimchi.model.tasks import TaskModel
from kimchi.model.vms import DOM_STATE_MAP, VMModel
from kimchi.model.vmstorages import VMStorageModel, VMStoragesModel
from kimchi.utils import add_task
from kimchi.xmlutils.utils import xpath_get_text


class VMSnapshotsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)
        self.vmstorages = VMStoragesModel(**kargs)
        self.vmstorage = VMStorageModel(**kargs)

    def create(self, vm_name, params={}):
        """Create a snapshot with the current domain state.

        The VM must be stopped and contain only disks with format 'qcow2';
        otherwise an exception will be raised.

        Parameters:
        vm_name -- the name of the VM where the snapshot will be created.
        params -- a dict with the following values:
            "name": The snapshot name (optional). If omitted, a default value
            based on the current time will be used.

        Return:
        A Task running the operation.
        """
        vir_dom = VMModel.get_vm(vm_name, self.conn)
        if DOM_STATE_MAP[vir_dom.info()[0]] != u'shutoff':
            raise InvalidOperation('KCHSNAP0001E', {'vm': vm_name})

        # if the VM has a non-CDROM disk with type 'raw', abort.
        for storage_name in self.vmstorages.get_list(vm_name):
            storage = self.vmstorage.lookup(vm_name, storage_name)
            type = storage['type']
            format = storage['format']

            if type != u'cdrom' and format != u'qcow2':
                raise InvalidOperation('KCHSNAP0010E', {'vm': vm_name,
                                                        'format': format})

        name = params.get('name', unicode(int(time.time())))

        task_params = {'vm_name': vm_name, 'name': name}
        taskid = add_task(u'/vms/%s/snapshots/%s' % (vm_name, name),
                          self._create_task, self.objstore, task_params)
        return self.task.lookup(taskid)

    def _create_task(self, cb, params):
        """Asynchronous function which actually creates the snapshot.

        Parameters:
        cb -- a callback function to signal the Task's progress.
        params -- a dict with the following values:
            "vm_name": the name of the VM where the snapshot will be created.
            "name": the snapshot name.
        """
        vm_name = params['vm_name']
        name = params['name']

        cb('building snapshot XML')
        root_elem = E.domainsnapshot()
        root_elem.append(E.name(name))
        xml = ET.tostring(root_elem, encoding='utf-8')

        try:
            cb('fetching snapshot domain')
            vir_dom = VMModel.get_vm(vm_name, self.conn)
            cb('creating snapshot')
            vir_dom.snapshotCreateXML(xml, 0)
        except (NotFoundError, OperationFailed, libvirt.libvirtError), e:
            raise OperationFailed('KCHSNAP0002E',
                                  {'name': name, 'vm': vm_name,
                                   'err': e.message})

        cb('OK', True)

    def get_list(self, vm_name):
        vir_dom = VMModel.get_vm(vm_name, self.conn)

        try:
            vir_snaps = vir_dom.listAllSnapshots(0)
            return sorted([s.getName().decode('utf-8') for s in vir_snaps],
                          key=unicode.lower)
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHSNAP0005E',
                                  {'vm': vm_name, 'err': e.message})


class VMSnapshotModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def lookup(self, vm_name, name):
        vir_snap = self.get_vmsnapshot(vm_name, name)

        try:
            snap_xml_str = vir_snap.getXMLDesc(0).decode('utf-8')
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHSNAP0004E', {'name': name,
                                                   'vm': vm_name,
                                                   'err': e.message})

        snap_xml = objectify.fromstring(snap_xml_str)

        try:
            parent = unicode(snap_xml.parent.name)
        except AttributeError:
            parent = u''

        return {'created': unicode(snap_xml.creationTime),
                'name': unicode(snap_xml.name),
                'parent': parent,
                'state': unicode(snap_xml.state)}

    def delete(self, vm_name, name):
        try:
            vir_snap = self.get_vmsnapshot(vm_name, name)
            vir_snap.delete(0)
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHSNAP0006E', {'name': name,
                                                   'vm': vm_name,
                                                   'err': e.message})

    def revert(self, vm_name, name):
        try:
            vir_dom = VMModel.get_vm(vm_name, self.conn)
            vir_snap = self.get_vmsnapshot(vm_name, name)
            vir_dom.revertToSnapshot(vir_snap, 0)

            # get vm name recorded in the snapshot and return new uri params
            vm_new_name = xpath_get_text(vir_snap.getXMLDesc(0),
                                         'domain/name')[0]
            return [vm_new_name, name]
        except libvirt.libvirtError, e:
            raise OperationFailed('KCHSNAP0009E', {'name': name,
                                                   'vm': vm_name,
                                                   'err': e.message})

    def get_vmsnapshot(self, vm_name, name):
        vir_dom = VMModel.get_vm(vm_name, self.conn)

        try:
            return vir_dom.snapshotLookupByName(name, 0)
        except libvirt.libvirtError, e:
            code = e.get_error_code()
            if code == libvirt.VIR_ERR_NO_DOMAIN_SNAPSHOT:
                raise NotFoundError('KCHSNAP0003E', {'name': name,
                                                     'vm': vm_name})
            else:
                raise OperationFailed('KCHSNAP0004E', {'name': name,
                                                       'vm': vm_name,
                                                       'err': e.message})


class CurrentVMSnapshotModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.vmsnapshot = VMSnapshotModel(**kargs)

    def lookup(self, vm_name):
        vir_dom = VMModel.get_vm(vm_name, self.conn)

        try:
            vir_snap = vir_dom.snapshotCurrent(0)
            snap_name = vir_snap.getName().decode('utf-8')
        except libvirt.libvirtError, e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN_SNAPSHOT:
                return {}

            raise OperationFailed('KCHSNAP0008E',
                                  {'vm': vm_name, 'err': e.message})

        return self.vmsnapshot.lookup(vm_name, snap_name)
