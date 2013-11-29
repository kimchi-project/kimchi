#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Royce Lv <lvroyce@linux.vnet.ibm.com>
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
#

import glob
import os.path
import shutil
import tempfile
import time
import uuid


from kimchi.isoinfo import probe_iso
from kimchi.utils import kimchi_log


class Scanner(object):
    SCAN_TTL = 300

    def __init__(self, record_clean_cb):
        self.clean_cb = record_clean_cb

    def delete(self):
        self.clean_stale(-1)

    def clean_stale(self, window=SCAN_TTL):
        """
        Clear scan pools generated before time window,
        Clear all scan pools if window is -1.
        """
        try:
            now = time.time()
            clean_list = glob.glob("/tmp/kimchi-scan-*")
            for d in clean_list:
                transient_pool = \
                    os.path.basename(d).replace('kimchi-scan-', '')[0: -6]
                if now - os.path.getmtime(d) > window:
                    shutil.rmtree(d)
                    self.clean_cb(transient_pool)
        except OSError as e:
            kimchi_log.debug(
                    "Exception %s occured when cleaning stale pool, ignore" % e.message)

    def scan_dir_prepare(self, name, path='/'):
        # clean stale scan storage pools
        self.clean_stale()
        return tempfile.mkdtemp(prefix='kimchi-scan-' + name, dir='/tmp')

    def start_scan(self, cb, params):
        def updater(iso_info):
            iso_path = iso_info['path'][:-3] + str(uuid.uuid4()) + '.iso'
            link_name = os.path.join(
                params['pool_path'],
                os.path.basename(iso_path))
            os.symlink(iso_info['path'], link_name)

        scan_params = dict(path=params['scan_path'], updater=updater)
        probe_iso(None, scan_params)
        cb('', True)
