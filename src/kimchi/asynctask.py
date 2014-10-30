#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
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
import threading
import traceback


from kimchi.exception import OperationFailed


class AsyncTask(object):
    def __init__(self, id, target_uri, fn, objstore, opaque=None):
        if objstore is None:
            raise OperationFailed("KCHASYNC0001E")

        self.id = str(id)
        self.target_uri = target_uri
        self.fn = fn
        self.objstore = objstore
        self.status = 'running'
        self.message = 'OK'
        self._save_helper()
        self._cp_request = cherrypy.serving.request
        self.thread = threading.Thread(target=self._run_helper,
                                       args=(opaque, self._status_cb))
        self.thread.setDaemon(True)
        self.thread.start()

    def _status_cb(self, message, success=None):
        if success is None:
            self.message = message
            self._save_helper()
            return

        if success is not None:
            self.status = 'finished' if success else 'failed'
        self.message = message
        self._save_helper()

    def _save_helper(self):
        obj = {}
        for attr in ('id', 'target_uri', 'message', 'status'):
            obj[attr] = getattr(self, attr)
        try:
            with self.objstore as session:
                session.store('task', self.id, obj)
        except Exception as e:
            raise OperationFailed('KCHASYNC0002E', {'err': e.message})

    def _run_helper(self, opaque, cb):
        cherrypy.serving.request = self._cp_request
        try:
            self.fn(cb, opaque)
        except Exception, e:
            cherrypy.log.error_log.error("Error in async_task %s " % self.id)
            cherrypy.log.error_log.error(traceback.format_exc())
            cb("Unexpected exception: %s" % e.message, False)
