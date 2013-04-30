#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.
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

def get_object_store():
    return os.path.join(get_prefix(), 'data', 'objectstore')

def get_template_path(resource):
    return '%s/templates/%s.tmpl' % (get_prefix(), resource)

def get_screenshot_path():
    return "%s/data/screenshots" % get_prefix()


if __name__ == '__main__':
    print get_prefix()
