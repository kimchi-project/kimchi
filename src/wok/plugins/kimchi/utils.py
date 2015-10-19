#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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
#

import contextlib
import os
import re
import urllib2
from httplib import HTTPConnection, HTTPException
from urlparse import urlparse

from wok.exception import InvalidParameter


MAX_REDIRECTION_ALLOWED = 5


def _uri_to_name(collection, uri):
    expr = '/plugins/kimchi/%s/(.*?)$' % collection
    m = re.match(expr, uri)
    if not m:
        raise InvalidParameter("KCHUTILS0001E", {'uri': uri})
    return m.group(1)


def template_name_from_uri(uri):
    return _uri_to_name('templates', uri)


def pool_name_from_uri(uri):
    return _uri_to_name('storagepools', uri)


def check_url_path(path, redirected=0):
    if redirected > MAX_REDIRECTION_ALLOWED:
        return False
    try:
        code = ''
        parse_result = urlparse(path)
        server_name = parse_result.netloc
        urlpath = parse_result.path
        if not urlpath:
            # Just a server, as with a repo.
            with contextlib.closing(urllib2.urlopen(path)) as res:
                code = res.getcode()
        else:
            # socket.gaierror could be raised,
            #   which is a child class of IOError
            conn = HTTPConnection(server_name, timeout=15)
            # Don't try to get the whole file:
            conn.request('HEAD', path)
            response = conn.getresponse()
            code = response.status
            conn.close()
        if code == 200:
            return True
        elif code == 301 or code == 302:
            for header in response.getheaders():
                if header[0] == 'location':
                    return check_url_path(header[1], redirected+1)
        else:
            return False
    except (urllib2.URLError, HTTPException, IOError, ValueError):
        return False
    return True


def validate_repo_url(url):
    url_parts = url.split('://')  # [0] = prefix, [1] = rest of URL

    if url_parts[0] == '':
        raise InvalidParameter("KCHREPOS0002E")

    if url_parts[0] in ['http', 'https', 'ftp']:
        if not check_url_path(url):
            raise InvalidParameter("WOKUTILS0001E", {'url': url})
    elif url_parts[0] == 'file':
        if not os.path.exists(url_parts[1]):
            raise InvalidParameter("WOKUTILS0001E", {'url': url})
    else:
        raise InvalidParameter("KCHREPOS0002E")
