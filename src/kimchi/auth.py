#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
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

import base64
import cherrypy
import grp
import PAM
import re
import time


from kimchi import template
from kimchi.exception import InvalidOperation, OperationFailed
from kimchi.utils import run_command


USER_ID = 'userid'
USER_GROUPS = 'groups'
USER_SUDO = 'sudo'
REFRESH = 'robot-refresh'


def debug(msg):
    pass
    # cherrypy.log.error(msg)


class User(object):

    def __init__(self, userid):
        self.user = {}
        self.user[USER_ID] = userid
        self.user[USER_GROUPS] = None
        self.user[USER_SUDO] = False

    def get_groups(self):
        self.user[USER_GROUPS] = [g.gr_name for g in grp.getgrall()
                                  if self.user[USER_ID] in g.gr_mem]
        return self.user[USER_GROUPS]

    def has_sudo(self):
        out, err, exit = run_command(['sudo', '-l', '-U', self.user[USER_ID],
                                      'sudo'])
        if exit == 0:
            debug("User %s is allowed to run sudo" % self.user[USER_ID])
            # sudo allows a wide range of configurations, such as controlling
            # which binaries the user can execute with sudo.
            # For now, we will just check whether the user is allowed to run
            # any command with sudo.
            out, err, exit = run_command(['sudo', '-l', '-U',
                                          self.user[USER_ID]])
            for line in out.split('\n'):
                if line and re.search("(ALL)", line):
                    self.user[USER_SUDO] = True
                    debug("User %s can run any command with sudo" %
                          self.user[USER_ID])
                    return self.user[USER_SUDO]
            debug("User %s can only run some commands with sudo" %
                  self.user[USER_ID])
        else:
            debug("User %s is not allowed to run sudo" % self.user[USER_ID])
        return self.user[USER_SUDO]

    def get_user(self):
        return self.user


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
                resp.append(('', 0))
            elif qtype == PAM.PAM_PROMPT_TEXT_INFO:
                resp.append(('', 0))
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
        msg_args = {'userid': username, 'code': code}
        raise OperationFailed("KCHAUTH0001E", msg_args)

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
    cherrypy.session.acquire_lock()
    session = cherrypy.session.get(USER_ID, None)
    cherrypy.session.release_lock()
    if session is not None:
        debug("Session authenticated for user %s" % session)
        kimchiRobot = cherrypy.request.headers.get('Kimchi-Robot')
        if kimchiRobot == "kimchi-robot":
            if (time.time() - cherrypy.session[REFRESH] >
               cherrypy.session.timeout * 60):
                cherrypy.session[USER_ID] = None
                cherrypy.lib.sessions.expire()
                raise cherrypy.HTTPError(401)
        else:
            cherrypy.session[REFRESH] = time.time()
        return True

    debug("Session not found")
    return False


def check_auth_httpba():
    """
    REST API users may authenticate with HTTP Basic Auth.  This is not allowed
    for the UI because web browsers would cache the credentials and make it
    impossible for the user to log out without closing their browser completely
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
        return None
    user = User(userid)
    debug("User verified, establishing session")
    cherrypy.session.acquire_lock()
    cherrypy.session.regenerate()
    cherrypy.session[USER_ID] = userid
    cherrypy.session[USER_GROUPS] = user.get_groups()
    cherrypy.session[USER_SUDO] = user.has_sudo()
    cherrypy.session[REFRESH] = time.time()
    cherrypy.session.release_lock()
    return user.get_user()


def logout():
    cherrypy.session.acquire_lock()
    cherrypy.session[USER_ID] = None
    cherrypy.session[REFRESH] = 0
    cherrypy.session.release_lock()
    cherrypy.lib.sessions.expire()


def has_permission(admin_methods):
    cherrypy.session.acquire_lock()
    has_sudo = cherrypy.session.get(USER_SUDO, None)
    cherrypy.session.release_lock()

    return not admin_methods or \
        cherrypy.request.method not in admin_methods or \
        (cherrypy.request.method in admin_methods and has_sudo)


def kimchiauth(admin_methods=None):
    debug("Entering kimchiauth...")
    if check_auth_session():
        if not has_permission(admin_methods):
            raise cherrypy.HTTPError(403)
        return

    if check_auth_httpba():
        if not has_permission(admin_methods):
            raise cherrypy.HTTPError(403)
        return

    if not from_browser():
        cherrypy.response.headers['WWW-Authenticate'] = 'Basic realm=kimchi'

    e = InvalidOperation('KCHAUTH0002E')
    raise cherrypy.HTTPError(401, e.message)
