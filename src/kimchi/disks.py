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


def get_partitions_paths():
    try:
        """ Returns all available partitions path of the host """
        blkid = subprocess.Popen(
            ["blkid", "-o", "device"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dev_paths = blkid.communicate()[0].rstrip("\n").split("\n")
    except:
        raise OperationFailed("Unable to retrieve partitions' full path.")
    return dev_paths


def get_partition_path(name, dev_paths):
    """ Returns device path given a partition name """
    dev_path = None
    regexp = re.compile(r"^.*"+name+"$")
    for path in dev_paths:
        if regexp.search(path) is not None:
            dev_path = path
            break
    if dev_path:
        return dev_path


def get_partitions_names():
    try:
        """ Returns all the names of available partitions  """
        lsblk = subprocess.Popen(
            ["lsblk", "-Pbo", "NAME,TYPE"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = lsblk.communicate()[0]
        lines_output = output.rstrip("\n").split("\n")
        # Will be used later to double check the partition
        dev_paths = get_partitions_paths()
        names = []
        keys = ["NAME", "TYPE"]
        # output is on format key="value", where key = NAME, TYPE
        for line in lines_output:
            d = {}
            for key in keys:
                expression = r"%s=\".*?\"" % key
                match = re.search(expression, line)
                field = match.group()
                k, v = field.split('=', 1)
                d[k.lower()] = v[1:-1]
            if d['type'] not in ['part', 'lvm']:
                continue
            # split()[0] to avoid the second part of the name,
            # after the whiteline
            name = d['name'].split()[0]
            # There are special cases where lsblk reports
            # a partition that does not exist in blkid and fdisk (Extended
            # partitions), which can't be used for pool creation. We
            # need to filter these cases as well.
            if not get_partition_path(name, dev_paths):
                continue
            names.append(name)
        return names
    except:
        raise OperationFailed("Unable to retrieve partitions' full path.")


def get_partition_details(name):
    try:
        # Find device path
        dev_path = get_partition_path(name, get_partitions_paths())
        # Couldn't find dev_path.
        if not dev_path:
            return
        # Executing lsblk to get partition/disk info
        lsblk = subprocess.Popen(
            ["lsblk", "-Pbo", "TYPE,FSTYPE,SIZE,MOUNTPOINT", dev_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # single line output
        output = lsblk.communicate()[0].rstrip("\n")
        # output is on format key="value", where key = NAME, TYPE, FSTYPE,
        # SIZE, MOUNTPOINT
        keys = ["TYPE", "FSTYPE", "SIZE", "MOUNTPOINT"]
        d = {}
        for key in keys:
            expression = r"%s=\".*?\"" % key
            match = re.search(expression, output)
            field = match.group()
            k, v = field.split('=', 1)
            d[k.lower()] = v[1:-1]
        if d['mountpoint']:
            # Sometimes the mountpoint comes with [SWAP] or other
            # info which is not an actual mount point. Filtering it
            regexp = re.compile(r"\[.*\]")
            if regexp.search(d['mountpoint']) is not None:
                d['mountpoint'] = ''
        d['path'] = dev_path
        d['name'] = name
        return d
    except:
        raise OperationFailed("Unable to retrieve partitions' data.")
