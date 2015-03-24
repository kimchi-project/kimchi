#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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

import os.path
import re
import subprocess

from parted import Device as PDevice
from parted import Disk as PDisk

from kimchi.exception import OperationFailed
from kimchi.utils import kimchi_log


def _get_dev_node_path(maj_min):
    """ Returns device node path given the device number 'major:min' """

    dm_name = "/sys/dev/block/%s/dm/name" % maj_min
    if os.path.exists(dm_name):
        with open(dm_name) as dm_f:
            content = dm_f.read().rstrip('\n')
        return "/dev/mapper/" + content

    uevent = "/sys/dev/block/%s/uevent" % maj_min
    with open(uevent) as ueventf:
        content = ueventf.read()

    data = dict(re.findall(r'(\S+)=(".*?"|\S+)', content.replace("\n", " ")))

    return "/dev/%s" % data["DEVNAME"]


def _get_lsblk_devs(keys, devs=[]):
    lsblk = subprocess.Popen(
        ["lsblk", "-Pbo"] + [','.join(keys)] + devs,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = lsblk.communicate()
    if lsblk.returncode != 0:
        raise OperationFailed("KCHDISKS0001E", {'err': err})

    return _parse_lsblk_output(out, keys)


def _get_dev_major_min(name):
    maj_min = None

    keys = ["NAME", "MAJ:MIN"]
    dev_list = _get_lsblk_devs(keys)

    for dev in dev_list:
        if dev['name'].split()[0] == name:
            maj_min = dev['maj:min']
            break
    else:
        raise OperationFailed("KCHDISKS0002E", {'device': name})

    return maj_min


def _is_dev_leaf(devNodePath):
    try:
        # By default, lsblk prints a device information followed by children
        # device information
        childrenCount = len(
            _get_lsblk_devs(["NAME"], [devNodePath])) - 1
    except OperationFailed as e:
        # lsblk is known to fail on multipath devices
        # Assume these devices contain children
        kimchi_log.error(
            "Error getting device info for %s: %s", devNodePath, e)
        return False

    return childrenCount == 0


def _is_dev_extended_partition(devType, devNodePath):
    if devType != 'part':
        return False
    diskPath = devNodePath.rstrip('0123456789')
    device = PDevice(diskPath)
    try:
        extended_part = PDisk(device).getExtendedPartition()
    except NotImplementedError as e:
        kimchi_log.warning(
            "Error getting extended partition info for dev %s type %s: %s",
            devNodePath, devType, e.message)
        # Treate disk with unsupported partiton table as if it does not
        # contain extended partitions.
        return False
    if extended_part and extended_part.path == devNodePath:
        return True
    return False


def _parse_lsblk_output(output, keys):
    # output is on format key="value",
    # where key can be NAME, TYPE, FSTYPE, SIZE, MOUNTPOINT, etc
    lines = output.rstrip("\n").split("\n")
    r = []
    for line in lines:
        d = {}
        for key in keys:
            expression = r"%s=\".*?\"" % key
            match = re.search(expression, line)
            field = match.group()
            k, v = field.split('=', 1)
            d[k.lower()] = v[1:-1]
        r.append(d)
    return r


def _get_vgname(devNodePath):
    """ Return volume group name of a physical volume. If the device node path
    is not a physical volume, return empty string. """
    pvs = subprocess.Popen(
        ["pvs", "--unbuffered", "--nameprefixes", "--noheadings",
         "-o", "vg_name", devNodePath],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = pvs.communicate()
    if pvs.returncode != 0:
        return ""

    return re.findall(r"LVM2_VG_NAME='([^\']*)'", out)[0]


def _is_available(name, devtype, fstype, mountpoint, majmin):
    devNodePath = _get_dev_node_path(majmin)
    # Only list unmounted and unformated and leaf and (partition or disk)
    # leaf means a partition, a disk has no partition, or a disk not held
    # by any multipath device. Physical volume belongs to no volume group
    # is also listed. Extended partitions should not be listed.
    if (devtype in ['part', 'disk', 'mpath'] and
            fstype in ['', 'LVM2_member'] and
            mountpoint == "" and
            _get_vgname(devNodePath) == "" and
            _is_dev_leaf(devNodePath) and
            not _is_dev_extended_partition(devtype, devNodePath)):
        return True
    return False


def get_partitions_names(check=False):
    names = set()
    keys = ["NAME", "TYPE", "FSTYPE", "MOUNTPOINT", "MAJ:MIN"]
    # output is on format key="value",
    # where key can be NAME, TYPE, FSTYPE, MOUNTPOINT
    for dev in _get_lsblk_devs(keys):
        # split()[0] to avoid the second part of the name, after the
        # whiteline
        name = dev['name'].split()[0]
        if check and not _is_available(name, dev['type'], dev['fstype'],
                                       dev['mountpoint'], dev['maj:min']):
            continue
        names.add(name)

    return list(names)


def get_partition_details(name):
    majmin = _get_dev_major_min(name)
    dev_path = _get_dev_node_path(majmin)

    keys = ["TYPE", "FSTYPE", "SIZE", "MOUNTPOINT"]
    try:
        dev = _get_lsblk_devs(keys, [dev_path])[0]
    except OperationFailed as e:
        kimchi_log.error(
            "Error getting partition info for %s: %s", name, e)
        return {}

    dev['available'] = _is_available(name, dev['type'], dev['fstype'],
                                     dev['mountpoint'], majmin)
    if dev['mountpoint']:
        # Sometimes the mountpoint comes with [SWAP] or other
        # info which is not an actual mount point. Filtering it
        regexp = re.compile(r"\[.*\]")
        if regexp.search(dev['mountpoint']) is not None:
            dev['mountpoint'] = ''
    dev['path'] = dev_path
    dev['name'] = name
    return dev
