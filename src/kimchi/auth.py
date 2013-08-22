#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  ShaoHe Feng <shaohef@linux.vnet.ibm.com>
#  Shu Ming <shuming@linux.vnet.ibm.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import PAM
import cherrypy
from exception import *

def authenticate(username, password, service="passwd"):
    '''Returns True if authenticate is OK via PAM.'''
    def _pam_conv(auth, query_list, userData=None):
        resp = []
        for i in range(len(query_list)):
            query, qtype = query_list[i]
            if qtype == PAM.PAM_PROMPT_ECHO_ON:
                resp.append((username, 0))
            elif qtype == PAM.PAM_PROMPT_ECHO_OFF:
                resp.append((password, 0))
            elif qtype == PAM.PAM_PROMPT_ERROR_MSG:
                cherrypy.log.error_log.error("PAM authenticate prompt error "
                                              "message: %s" % query)
                resp.append(('', 0));
            elif qtype == PAM.PAM_PROMPT_TEXT_INFO:
                resp.append(('', 0));
            else:
                return None
        return resp

    auth = PAM.pam()
    auth.start(service)
    auth.set_item(PAM.PAM_USER, username)
    auth.set_item(PAM.PAM_CONV, _pam_conv)

    try:
        auth.authenticate()
    except PAM.error, (resp, code):
        raise InvalidOperation(resp, code)

    return True
