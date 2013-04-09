#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.

import copy
from collections import OrderedDict

osinfo = OrderedDict([
    ('unknown', {
        'version': lambda d,v: True,
        'icon': 'images/image-missing.svg',
        'os_distro': 'unknown', 'os_version': 'unknown',
        'cpus': 1, 'cpu_cores': 1, 'cpu_threads': 1,
        'memory': 1024,
        'cdrom': '',
        'disks': [{'index': 0, 'size': 10}],
        'disk_bus': 'ide', 'nic_model': 'ne2k_pci'
  }),
])

defaults = {'network': 'default', 'storagepool': 'default'}

def lookup(distro, version):
    ret = None
    for name, entry in osinfo.items():
        # Test if this entry is a valid match
        if entry['version'](distro, version):
            params = copy.copy(entry)
            del params['version']  # Don't pass around the version function
            ret = (name, params)
    if ret:
        ret[1].update(defaults)
    return ret
