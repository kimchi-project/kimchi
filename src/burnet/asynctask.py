#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
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

import threading

class NotProperOps(Exception):
    pass

class AsyncTask(object):
    def __init__(self, id, target_uri, fn, objstore, opaque=None):
        if objstore == None:
            raise NotProperOps("Initiate datastore in the model object")
        self.id = str(id)
        self.target_uri = target_uri
        self.fn = fn
        self.objstore = objstore
        self.status = 'running'

        self.message = 'OK'
        self._save_helper()
        self.thread = threading.Thread(target=self._run_helper,
                                       args=(opaque, self._status_cb))
        self.thread.setDaemon(True)
        self.thread.start()

    def _status_cb(self, message, success=None):
        if success == None:
           self.message = message
           self._save_helper()
           return

        if success:
            self.status = 'finished'
        else:
            self.status = 'failed'
        self.message = message
        self._save_helper()

    def _save_helper(self):
        obj = {}
        for attr in ('id', 'target_uri', 'message', 'status'):
            obj[attr] = getattr(self, attr)
        with self.objstore as session:
            session.store('task', self.id, obj)

    def _run_helper(self, opaque, cb):
        try:
            self.fn(cb, opaque)
        except Exception, e:
            cb("Unexpected exception: %s" % str(e), False)
