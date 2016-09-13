#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2016
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
import platform
import re
import sqlite3
import time
import os
import urllib2
from httplib import HTTPConnection, HTTPException
from urlparse import urlparse

from wok.exception import InvalidParameter, OperationFailed
from wok.plugins.kimchi import config
from wok.plugins.kimchi.osinfo import get_template_default
from wok.stringutils import encode_value
from wok.utils import run_command, wok_log
from wok.xmlutils.utils import xpath_get_text

MAX_REDIRECTION_ALLOWED = 5


def _uri_to_name(collection, uri):
    expr = '/plugins/kimchi/%s/(.*?)$' % collection
    m = re.match(expr, uri)
    if not m:
        raise InvalidParameter("WOKUTILS0001E", {'uri': uri})
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
        wok_log.error("Error while upgrading objectstore data: %s", e.args[0])
        raise OperationFailed("KCHUTILS0006E")
    finally:
        if conn:
            conn.close()
        wok_log.info("%d '%s' entries upgraded in objectstore.", total, item)


def upgrade_objectstore_template_disks(libv_conn):
    """
        Upgrade the value of a given JSON's item of all Templates.
        Removes 'storagepool' entry and adds
        'pool: { name: ..., type: ... }'
    """
    total = 0
    try:
        conn = sqlite3.connect(config.get_object_store(), timeout=10)
        cursor = conn.cursor()
        sql = "SELECT id, json FROM objects WHERE type='template'"
        cursor.execute(sql)
        for row in cursor.fetchall():
            template = json.loads(row[1])

            # Get pool info
            pool_uri = template['storagepool']
            pool_name = pool_name_from_uri(pool_uri)
            pool = libv_conn.get().storagePoolLookupByName(
                pool_name.encode("utf-8"))
            pool_type = xpath_get_text(pool.XMLDesc(0), "/pool/@type")[0]

            # Update json
            new_disks = []
            for disk in template['disks']:
                disk['pool'] = {'name': pool_uri,
                                'type': pool_type}
                new_disks.append(disk)
            template['disks'] = new_disks
            del template['storagepool']

            sql = "UPDATE objects SET json=? WHERE id=?"
            cursor.execute(sql, (json.dumps(template), row[0]))
            conn.commit()
            total += 1
    except sqlite3.Error, e:
        if conn:
            conn.rollback()
        wok_log.error("Error while upgrading objectstore data: %s", e.args[0])
        raise OperationFailed("KCHUTILS0006E")
    finally:
        if conn:
            conn.close()
        wok_log.info("%d 'template' entries upgraded in objectstore.", total)


def upgrade_objectstore_memory():
    """
        Upgrade the value of a given JSON's item of all Templates.
        Changes 'memory': XXX by 'memory': {'current': XXXX,
                                            'maxmemory': XXXX}
    """
    total = 0
    try:
        conn = sqlite3.connect(config.get_object_store(), timeout=10)
        cursor = conn.cursor()
        sql = "SELECT id,json FROM objects WHERE type='template'"
        cursor.execute(sql)
        for row in cursor.fetchall():
            template = json.loads(row[1])

            # Get memory info
            memory = template['memory']
            # New memory is a dictionary with 'current' and 'maxmemory'
            if type(memory) is not dict:
                maxmem = get_template_default('modern',
                                              'memory').get('maxmemory')
                if maxmem < memory:
                    maxmem = memory
                template['memory'] = {'current': memory,
                                      'maxmemory': maxmem}
            else:
                continue

            sql = "UPDATE objects SET json=? WHERE id=?"
            cursor.execute(sql, (json.dumps(template), row[0]))
            conn.commit()
            total += 1
    except sqlite3.Error, e:
        if conn:
            conn.rollback()
        wok_log.error("Error while upgrading objectstore data: %s", e.args[0])
        raise OperationFailed("KCHUTILS0006E")
    finally:
        if conn:
            conn.close()
        if total > 0:
            wok_log.info(
                "%d 'template' memory entries upgraded in objectstore.", total)


def get_next_clone_name(all_names, basename, name_suffix='', ts=False):
    """Find the next available name for a cloned resource.

    If any resource named "<basename>-clone-<number><name_suffix>" is found
    in "all_names", use the maximum "number" + 1; else, use 1.

    Arguments:
    all_names -- All existing names for the resource type. This list will
        be used to make sure the new name won't conflict with
        existing names.
    basename -- The name of the original resource.
    name_suffix -- The resource name suffix (optional). This parameter
        exist so that a resource named "foo.img" gets the name
        "foo-clone-1.img" instead of "foo.img-clone-1". If this parameter
        is used, the suffix should not be present in "basename".
    ts -- use timestamp, instead of incremental numbers

    Return:
    A UTF-8 string in the format "<basename>-clone-<number><name_suffix>".
    """
    re_group_num = 'num'

    # Use timestamps or increase clone number
    if ts:
        # Microsecond precision
        ts_suffix = int(time.time() * 1000000)
        new_name = u'%s-clone-%d' % (basename, ts_suffix)
    else:
        re_expr = u'%s-clone-(?P<%s>\d+)' % (basename, re_group_num)
        if name_suffix != '':
            re_expr = u'%s%s' % (re_expr, name_suffix)

        max_num = 0
        re_compiled = re.compile(re_expr)

        for n in all_names:
            match = re_compiled.match(n)
            if match is not None:
                max_num = max(max_num, int(match.group(re_group_num)))

        # increments the maximum "clone number" found
        new_name = u'%s-clone-%d' % (basename, max_num + 1)

    if name_suffix != '':
        new_name = new_name + name_suffix

    return new_name


def is_libvirtd_up():
    """
    Checks if libvirtd.service is up.
    """
    distro, _, _ = platform.linux_distribution()
    if distro.lower() == 'ubuntu':
        cmd = ['systemctl', 'is-active', 'libvirt-bin.service']
    else:
        cmd = ['systemctl', 'is-active', 'libvirtd.service']

    output, error, rc = run_command(cmd, silent=True)
    return True if output == 'active\n' else False


def is_s390x():
    """
    Check if current arch is 's390x'
    Returns:
    """
    if os.uname()[4] == 's390x':
        return True

    return False


def create_disk_image(format_type, path, capacity):
    """
    Create a disk image for the Guest
    Args:
        format: Format of the storage. e.g. qcow2
        path: Path where the virtual disk will be created
        capacity: Capacity of the virtual disk in GBs

    Returns:

    """
    out, err, rc = run_command(
        ["/usr/bin/qemu-img", "create", "-f", format_type, "-o",
         "preallocation=metadata", path, encode_value(capacity) + "G"])

    if rc != 0:
        raise OperationFailed("KCHTMPL0041E", {'err': err})

    return
