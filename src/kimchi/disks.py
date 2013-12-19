#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Daniel H Barboza <danielhb@linux.vnet.ibm.com>
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

import re
import subprocess

from kimchi.exception import OperationFailed
from kimchi.utils import kimchi_log


def _get_partition_path(name):
    """ Returns device path given a partition name """
    dev_path = None
    maj_min = None

    keys = ["NAME", "MAJ:MIN"]
    dev_list = _get_lsblk_devs(keys)

    for dev in dev_list:
        if dev['name'] == name:
            maj_min = dev['maj:min']
            break

    uevent_cmd = "cat /sys/dev/block/%s/uevent" % maj_min
    uevent = subprocess.Popen(uevent_cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, shell=True)
    out, err = uevent.communicate()
    if uevent.returncode != 0:
        raise OperationFailed("Error getting partition path for %s", name)

    data = dict(re.findall(r'(\S+)=(".*?"|\S+)', out.replace("\n", " ")))

    return "/dev/%s" % data["DEVNAME"]


def _get_lsblk_devs(keys, devs=[]):
    lsblk = subprocess.Popen(
        ["lsblk", "-Pbo"] + [','.join(keys)] + devs,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = lsblk.communicate()
    if lsblk.returncode != 0:
        raise OperationFailed('Error executing lsblk: %s' % err)

    return _parse_lsblk_output(out, keys)


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


def get_partitions_names():
    names = []
    ignore_names = []
    keys = ["NAME", "TYPE", "FSTYPE", "MOUNTPOINT"]
    # output is on format key="value",
    # where key can be NAME, TYPE, FSTYPE, MOUNTPOINT
    for dev in _get_lsblk_devs(keys):
        # split()[0] to avoid the second part of the name, after the
        # whiteline
        name = dev['name'].split()[0]
        # Only list unmounted and unformated partition or disk.
        if not all([dev['type'] in ['part', 'disk'],
                    dev['fstype'] == "",
                    dev['mountpoint'] == ""]):

            # the whole disk must be ignored in it has at least one
            # mounted/formatted partition
            if dev['type'] == 'part':
                ignore_names.append(name[:-1])
            continue

        names.append(name)

    return list(set(names) - set(ignore_names))


def get_partition_details(name):
    dev_path = _get_partition_path(name)

    keys = ["TYPE", "FSTYPE", "SIZE", "MOUNTPOINT"]
    try:
        dev = _get_lsblk_devs(keys, [dev_path])[0]
    except OperationFailed as e:
        kimchi_log.error(
            "Error getting partition info for %s: %s", name, e)
        return {}

    if dev['mountpoint']:
        # Sometimes the mountpoint comes with [SWAP] or other
        # info which is not an actual mount point. Filtering it
        regexp = re.compile(r"\[.*\]")
        if regexp.search(dev['mountpoint']) is not None:
            dev['mountpoint'] = ''
    dev['path'] = dev_path
    dev['name'] = name
    return dev
