#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.
#

from distutils.core import setup

setup(name='burnet',
      version='0.1',
      package_dir={'': 'src'},
      py_modules=['burnet', 'burnet.server', 'burnet.root'],
      scripts=['bin/burnetd'])
