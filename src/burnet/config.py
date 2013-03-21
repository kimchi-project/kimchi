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

import os, os.path

# FIXME
PREFIX="/usr/local"

def get_prefix():
    if __file__[0] == '/':
        base = os.path.dirname(__file__)
    else:
        base = os.path.dirname('./%s' % __file__)

    if os.access('%s/../../src/burnet/config.py' % base, os.F_OK):
        return '%s/../..' % base
    else:
        return '%s/share/burnet' % PREFIX

def get_template_path(resource):
    return '%s/templates/%s.tmpl' % (get_prefix(), resource)

if __name__ == '__main__':
    print get_prefix()
