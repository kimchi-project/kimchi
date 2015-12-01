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
import json
import os
import re
import sqlite3
import urllib2
from httplib import HTTPConnection, HTTPException
from urlparse import urlparse

from wok.exception import InvalidParameter, OperationFailed
from wok.plugins.kimchi import config
from wok.utils import wok_log

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


def get_objectstore_fields():
    """
        Return a list with all fields of the objectstore.
    """
    conn = sqlite3.connect(config.get_object_store(), timeout=10)
    cursor = conn.cursor()
    schema_fields = []
    sql = "PRAGMA table_info('objects')"
    cursor.execute(sql)
    for row in cursor.fetchall():
        schema_fields.append(row[1])
    return schema_fields


def upgrade_objectstore_schema(field=None):
    """
        Add a new column (of type TEXT) in the objectstore schema.
    """
    if field is None:
        wok_log.error("Cannot upgrade objectstore schema.")
        return False

    if field in get_objectstore_fields():
        return False
    try:
        conn = sqlite3.connect(config.get_object_store(), timeout=10)
        cursor = conn.cursor()
        sql = "ALTER TABLE objects ADD COLUMN %s TEXT" % field
        cursor.execute(sql)
        wok_log.info("Objectstore schema sucessfully upgraded.")
        conn.close()
    except sqlite3.Error, e:
        if conn:
            conn.rollback()
            conn.close()
        wok_log.error("Cannot upgrade objectstore schema: ", e.args[0])
        return False
    return True


def upgrade_objectstore_data(item, old_uri, new_uri):
    """
        Upgrade the value of a given JSON's item of all Template and VM entries
        of the objectstore from old_uri to new_uri.
    """
    total = 0
    try:
        conn = sqlite3.connect(config.get_object_store(), timeout=10)
        cursor = conn.cursor()
        sql = "SELECT id, json FROM objects WHERE type='template' OR type='vm'"
        cursor.execute(sql)
        for row in cursor.fetchall():
            # execute update here
            template = json.loads(row[1])
            path = (template[item] if item in template else 'none')
            if path.startswith(old_uri):
                template[item] = new_uri + path
                sql = "UPDATE objects SET json=?, version=? WHERE id=?"
                cursor.execute(sql, (json.dumps(template),
                                     config.get_kimchi_version(), row[0]))
                conn.commit()
                total += 1
    except sqlite3.Error, e:
        if conn:
            conn.rollback()
        raise OperationFailed("KCHUTILS0006E")
        wok_log.error("Error while upgrading objectstore data:", e.args[0])
    finally:
        if conn:
            conn.close()
        wok_log.info("%d '%s' entries upgraded in objectstore.", total, item)
