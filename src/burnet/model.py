#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.

import re

class NotFoundError(Exception):
    pass

class OperationFailed(Exception):
    pass

class MissingParameter(Exception):
    pass

class InvalidParameter(Exception):
    pass

class InvalidOperation(Exception):
    pass

def template_name_from_uri(uri):
    m = re.match('/templates/(.*?)/?$', uri)
    if not m:
        raise InvalidParameter(uri)
    return m.group(1)
