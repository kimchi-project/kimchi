#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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
from wok.plugins.kimchi.model.vms import VMModel
from wok.plugins.kimchi.model.vms import VMsModel
from wok.plugins.kimchi.xmlutils.disk import get_vm_disk_info
from wok.plugins.kimchi.xmlutils.disk import get_vm_disks


"""
    Functions that multiple storage-related models (e.g. VMStoragesModel,
    VolumesModel) will need.
"""


def get_disk_used_by(conn, path):
    used_by = []
    # try to find this volume in existing vm
    vms_list = VMsModel.get_vms(conn)
    for vm in vms_list:
        dom = VMModel.get_vm(vm, conn)
        storages = get_vm_disks(dom)
        for disk in storages.keys():
            d_info = get_vm_disk_info(dom, disk)
            if path == d_info['path']:
                used_by.append(vm)

    return used_by
