#
# Project Wok
#
# Copyright IBM, Corp. 2013-2015
#
# Code derived from Project Kimchi
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

import cherrypy
import gettext


from wok.i18n import messages as _messages
from wok.template import get_lang, validate_language


class WokException(Exception):
    def __init__(self, code='', args={}):
        self.code = code

        for key, value in args.iteritems():
            if isinstance(value, unicode):
                continue

            # value is not unicode: convert it
            try:
                # In case the value formats itself to an ascii string.
                args[key] = unicode(str(value), 'utf-8')
            except UnicodeEncodeError:
                # In case the value is a WokException or it formats
                # itself to a unicode string.
                args[key] = unicode(value)

        if cherrypy.request.app:
            msg = self._get_translation()
        else:
            msg = _messages.get(code, code)

        msg = unicode(msg, 'utf-8') % args
        pattern = "%s: %s" % (code, msg)
        Exception.__init__(self, pattern)

    def _get_translation(self):
        lang = validate_language(get_lang())
        paths = cherrypy.request.app.root.paths
        domain = cherrypy.request.app.root.domain
        messages = cherrypy.request.app.root.messages
        text = messages.get(self.code, self.code)

        try:
            translation = gettext.translation(domain, paths.mo_dir, [lang])
        except:
            translation = gettext

        return translation.gettext(text)


class NotFoundError(WokException):
    pass


class OperationFailed(WokException):
    pass


class MissingParameter(WokException):
    pass


class InvalidParameter(WokException):
    pass


class InvalidOperation(WokException):
    pass


class IsoFormatError(WokException):
    pass


class ImageFormatError(WokException):
    pass


class TimeoutExpired(WokException):
    pass


class UnauthorizedError(WokException):
    pass
