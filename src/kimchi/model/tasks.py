#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
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


import time

from kimchi.exception import TimeoutExpired


class TasksModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']

    def get_list(self):
        with self.objstore as session:
            return session.get_list('task')


class TaskModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']

    def lookup(self, id):
        with self.objstore as session:
            return session.get('task', str(id))

    def wait(self, id, timeout=10):
        """Wait for a task until it stops running (successfully or due to
        an error). If the Task finishes its execution before <timeout>, this
        function returns normally; otherwise an exception is raised.

        Parameters:
        id -- The Task ID.
        timeout -- The maximum time, in seconds, that this function should wait
            for the Task. If the Task runs for more than <timeout>,
            "TimeoutExpired" is raised.
        """
        for i in range(0, timeout):
            with self.objstore as session:
                task = session.get('task', str(id))

            if task['status'] != 'running':
                return

            time.sleep(1)

        raise TimeoutExpired('KCHASYNC0003E', {'seconds': timeout,
                                               'task': task['target_uri']})
