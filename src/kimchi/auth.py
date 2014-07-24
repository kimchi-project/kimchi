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
import fcntl
import multiprocessing
import os
import PAM
import pty
import re
import termios
import time
import urllib2


from kimchi import template
from kimchi.exception import InvalidOperation, OperationFailed
from kimchi.utils import get_all_tabs, run_command


USER_NAME = 'username'
USER_GROUPS = 'groups'
USER_ROLES = 'roles'
REFRESH = 'robot-refresh'

tabs = get_all_tabs()


def redirect_login():
    url = "/login.html"
    if cherrypy.request.path_info.endswith(".html"):
        next_url = cherrypy.serving.request.request_line.split()[1]
        next_url = urllib2.quote(next_url.encode('utf-8'), safe="")
        url = "/login.html?next=%s" % next_url

    raise cherrypy.HTTPRedirect(url, 303)


def debug(msg):
    pass
    # cherrypy.log.error(msg)


class User(object):

    def __init__(self, username):
        self.user = {}
        self.user[USER_NAME] = username
        self.user[USER_GROUPS] = None
        # after adding support to change user roles that info should be read
        # from a specific objstore and fallback to default only if any entry is
        # found
        self.user[USER_ROLES] = dict.fromkeys(tabs, 'user')

    def get_groups(self):
        out, err, rc = run_command([ 'id', '-Gn', self.user[USER_NAME] ])
        if rc == 0:
            self.user[USER_GROUPS] = out.rstrip().split(" ")

        return self.user[USER_GROUPS]

    def get_roles(self):
        if self.has_sudo():
            # after adding support to change user roles that info should be
            # read from a specific objstore and fallback to default only if
            # any entry is found
            self.user[USER_ROLES] = dict.fromkeys(tabs, 'admin')

        return self.user[USER_ROLES]

    def has_sudo(self):
        result = multiprocessing.Value('i', 0, lock=False)
        p = multiprocessing.Process(target=self._has_sudo, args=(result,))
        p.start()
        p.join()

        return result.value

    def _has_sudo(self, result):
        result.value = False

        _master, slave = pty.openpty()
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

        out, err, exit = run_command(['sudo', '-l', '-U', self.user[USER_NAME],
                                      'sudo'])
        if exit == 0:
            debug("User %s is allowed to run sudo" % self.user[USER_NAME])
            # sudo allows a wide range of configurations, such as controlling
            # which binaries the user can execute with sudo.
            # For now, we will just check whether the user is allowed to run
            # any command with sudo.
            out, err, exit = run_command(['sudo', '-l', '-U',
                                          self.user[USER_NAME]])
            for line in out.split('\n'):
                if line and re.search("(ALL)", line):
                    result.value = True
                    debug("User %s can run any command with sudo" %
                          result.value)
                    return
            debug("User %s can only run some commands with sudo" %
                  self.user[USER_NAME])
        else:
            debug("User %s is not allowed to run sudo" % self.user[USER_NAME])

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
    except PAM.error:
        raise

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
    session = cherrypy.session.get(USER_NAME, None)
    cherrypy.session.release_lock()
    if session is not None:
        debug("Session authenticated for user %s" % session)
        kimchiRobot = cherrypy.request.headers.get('Kimchi-Robot')
        if kimchiRobot == "kimchi-robot":
            if (time.time() - cherrypy.session[REFRESH] >
                    cherrypy.session.timeout * 60):
                cherrypy.session[USER_NAME] = None
                cherrypy.lib.sessions.expire()
                raise cherrypy.HTTPError(401, "sessionTimeout")
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
    username, password = decodeddata.decode().split(":", 1)

    return login(username, password)


def login(username, password, **kwargs):
    try:
        if not authenticate(username, password):
            debug("User cannot be verified with the supplied password")
            return None
    except PAM.error, (resp, code):
        msg_args = {'username': username, 'code': code}
        raise OperationFailed("KCHAUTH0001E", msg_args)

    user = User(username)
    debug("User verified, establishing session")
    cherrypy.session.acquire_lock()
    cherrypy.session.regenerate()
    cherrypy.session[USER_NAME] = username
    cherrypy.session[USER_GROUPS] = user.get_groups()
    cherrypy.session[USER_ROLES] = user.get_roles()
    cherrypy.session[REFRESH] = time.time()
    cherrypy.session.release_lock()
    return user.get_user()


def logout():
    cherrypy.session.acquire_lock()
    cherrypy.session[USER_NAME] = None
    cherrypy.session[REFRESH] = 0
    cherrypy.session.release_lock()
    cherrypy.lib.sessions.close()


def kimchiauth():
    debug("Entering kimchiauth...")
    session_missing = cherrypy.session.missing
    if check_auth_session():
        return

    if check_auth_httpba():
        return

    # not a REST full request, redirect login page directly
    if ("Accept" in cherrypy.request.headers and
       not template.can_accept('application/json')):
        redirect_login()

    # from browser, and it stays on one page.
    if session_missing and cherrypy.request.cookie.get("lastPage") is not None:
        raise cherrypy.HTTPError(401, "sessionTimeout")

    if not from_browser():
        cherrypy.response.headers['WWW-Authenticate'] = 'Basic realm=kimchi'

    e = InvalidOperation('KCHAUTH0002E')
    raise cherrypy.HTTPError(401, e.message.encode('utf-8'))
