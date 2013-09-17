#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  ShaoHe Feng <shaohef@linux.vnet.ibm.com>
#  Shu Ming <shuming@linux.vnet.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
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
import re
import base64
import template
from exception import *


SESSION_USER = 'userid'


def debug(msg):
    pass
    # cherrypy.log.error(msg)


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
        raise OperationFailed(resp, code)

    return True

def from_browser():
    # Enable Basic Authentication for REST tools.
    # Ajax request sent from jQuery in browser will have "X-Requested-With"
    # header. We will check it to determine whether enable BA.
    requestHeader = cherrypy.request.headers.get("X-Requested-With", None)
    return (requestHeader == "XMLHttpRequest")

def check_auth_session():
    """
    A user is considered authenticated if we have an established session open
    for the user.
    """
    try:
        s = cherrypy.session[SESSION_USER]
        user = cherrypy.request.login = cherrypy.session[SESSION_USER]
        debug("Authenticated with session: %s, for user: %s" % (s, user))
    except KeyError:
        debug("Session not found")
        return False
    debug("Session found for user %s" % user)
    return True


def check_auth_httpba():
    """
    REST API users may authenticate with HTTP Basic Auth.  This is not allowed
    for the UI because web browsers would cache the credentials and make it
    impossible for the user to log out without closing their browser completely.
    """
    if from_browser() or not template.can_accept('application/json'):
        return False

    authheader = cherrypy.request.headers.get('AUTHORIZATION')
    if not authheader:
        debug("No authentication headers found")
        return False

    debug("Authheader: %s" % authheader)
    # TODO: what happens if you get an auth header that doesn't use basic auth?
    b64data = re.sub("Basic ", "", authheader)
    decodeddata = base64.b64decode(b64data.encode("ASCII"))
    # TODO: test how this handles ':' characters in username/passphrase.
    userid, password = decodeddata.decode().split(":", 1)

    return login(userid, password)


def login(userid, password):
    if not authenticate(userid, password):
        debug("User cannot be verified with the supplied password")
        return False
    debug("User verified, establishing session")
    cherrypy.session.regenerate()
    cherrypy.session[SESSION_USER] = cherrypy.request.login = userid
    return True


def logout():
    userid = cherrypy.session.get(SESSION_USER, None)
    cherrypy.session[SESSION_USER] = cherrypy.request.login = None
    cherrypy.lib.sessions.expire()


def kimchiauth(*args, **kwargs):
    debug("Entering kimchiauth...")
    if check_auth_session():
        return

    if check_auth_httpba():
        return

    if not from_browser():
        cherrypy.response.headers['WWW-Authenticate'] = 'Basic realm=kimchi'

    raise cherrypy.HTTPError("401 Unauthorized")
