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

import re

from wok.exception import InvalidParameter


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
