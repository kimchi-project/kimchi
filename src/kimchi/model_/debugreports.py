#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

import fnmatch
import glob
import logging
import os
import shutil
import subprocess
import time

from kimchi import config
from kimchi.exception import NotFoundError, OperationFailed
from kimchi.model_.tasks import TaskModel
from kimchi.utils import add_task, kimchi_log


class DebugReportsModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)

    def create(self, params):
        ident = params['name']
        taskid = self._gen_debugreport_file(ident)
        return self.task.lookup(taskid)

    def get_list(self):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, '*.*')
        file_lists = glob.glob(file_pattern)
        file_lists = [os.path.split(file)[1] for file in file_lists]
        name_lists = [file.split('.', 1)[0] for file in file_lists]

        return name_lists

    def _gen_debugreport_file(self, name):
        gen_cmd = self.get_system_report_tool()

        if gen_cmd is not None:
            return add_task('', gen_cmd, self.objstore, name)

        raise OperationFailed("debugreport tool not found")

    @staticmethod
    def sosreport_generate(cb, name):
        command = 'sosreport --batch --name "%s"' % name
        try:
            retcode = subprocess.call(command, shell=True,
                                      stdout=subprocess.PIPE)
            if retcode < 0:
                raise OperationFailed('Command terminated with signal')
            elif retcode > 0:
                raise OperationFailed('Command failed: rc = %i' % retcode)
            pattern = '/tmp/sosreport-%s-*' % name
            for reportFile in glob.glob(pattern):
                if not fnmatch.fnmatch(reportFile, '*.md5'):
                    output = reportFile
                    break
            else:
                # sosreport tends to change the name mangling rule and
                # compression file format between different releases.
                # It's possible to fail to match a report file even sosreport
                # runs successfully. In future we might have a general name
                # mangling function in kimchi to format the name before passing
                # it to sosreport. Then we can delete this exception.
                raise OperationFailed('Can not find generated debug report '
                                      'named by %s' % pattern)
            ext = output.split('.', 1)[1]
            path = config.get_debugreports_path()
            target = os.path.join(path, name)
            target_file = '%s.%s' % (target, ext)
            shutil.move(output, target_file)
            os.remove('%s.md5' % output)
            cb('OK', True)

            return

        except OSError:
            raise

        except Exception, e:
            # No need to call cb to update the task status here.
            # The task object will catch the exception rasied here
            # and update the task status there
            log = logging.getLogger('Model')
            log.warning('Exception in generating debug file: %s', e)
            raise OperationFailed(e)

    @staticmethod
    def get_system_report_tool():
        # Please add new possible debug report command here
        # and implement the report generating function
        # based on the new report command
        report_tools = ({'cmd': 'sosreport --help',
                         'fn': DebugReportsModel.sosreport_generate},)

        # check if the command can be found by shell one by one
        for helper_tool in report_tools:
            try:
                retcode = subprocess.call(helper_tool['cmd'], shell=True,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
                if retcode == 0:
                    return helper_tool['fn']
            except Exception, e:
                kimchi_log.info('Exception running command: %s', e)

        return None


class DebugReportModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name)
        file_pattern = file_pattern + '.*'
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError('no such report')

        ctime = os.stat(file_target).st_ctime
        ctime = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(ctime))
        file_target = os.path.split(file_target)[-1]
        file_target = os.path.join("/data/debugreports", file_target)
        return {'file': file_target,
                'ctime': ctime}

    def delete(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name + '.*')
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError('no such report')

        os.remove(file_target)


class DebugReportContentModel(object):
    def __init__(self, **kargs):
        self._debugreport = DebugReportModel()

    def lookup(self, name):
        return self._debugreport.lookup(name)
