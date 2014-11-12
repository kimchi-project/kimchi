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

import time

import libvirt
import lxml.etree as ET
from lxml.builder import E

from kimchi.exception import InvalidOperation, NotFoundError, OperationFailed
from kimchi.model.tasks import TaskModel
from kimchi.model.vms import DOM_STATE_MAP, VMModel
from kimchi.utils import add_task


class VMSnapshotsModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)

    def create(self, vm_name, params={}):
        """Create a snapshot with the current domain state.

        The VM must be stopped before creating a snapshot on it; otherwise, an
        exception will be raised.

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
