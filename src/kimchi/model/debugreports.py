#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
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
from kimchi.model.tasks import TaskModel
from kimchi.utils import add_task, kimchi_log
from kimchi.utils import run_command


class DebugReportsModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)

    def create(self, params):
        ident = params.get('name').strip()
        # Generate a name with time and millisec precision, if necessary
        if ident is None or ident == "":
            ident = 'report-' + str(int(time.time() * 1000))
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

        raise OperationFailed("KCHDR0002E")

    @staticmethod
    def sosreport_generate(cb, name):
        try:
            command = ['sosreport', '--batch', '--name=%s' % name]
            output, error, retcode = run_command(command)

            if retcode != 0:
                raise OperationFailed("KCHDR0003E", {'name': name,
                                                     'err': retcode})

            # SOSREPORT might create file in /tmp or /var/tmp
            # FIXME: The right way should be passing the tar.xz file directory
            # though the parameter '--tmp-dir', but it is failing in Fedora 20
            patterns = ['/tmp/sosreport-%s-*', '/var/tmp/sosreport-%s-*']
            reports = []
            reportFile = None
            for p in patterns:
                reports = reports + [f for f in glob.glob(p % name)]
            for f in reports:
                if not fnmatch.fnmatch(f, '*.md5'):
                    reportFile = f
                    break
            # Some error in sosreport happened
            if reportFile is None:
                kimchi_log.error('Debug report file not found. See sosreport '
                                 'output for detail:\n%s', output)
                fname = (patterns[0] % name).split('/')[-1]
                raise OperationFailed('KCHDR0004E', {'name': fname})

            md5_report_file = reportFile + '.md5'
            report_file_extension = '.' + reportFile.split('.', 1)[1]
            path = config.get_debugreports_path()
            target = os.path.join(path, name + report_file_extension)
            # Moving report
            msg = 'Moving debug report file "%s" to "%s"' % (reportFile,
                                                             target)
            kimchi_log.info(msg)
            shutil.move(reportFile, target)
            # Deleting md5
            msg = 'Deleting report md5 file: "%s"' % (md5_report_file)
            kimchi_log.info(msg)
            md5 = open(md5_report_file).read().strip()
            kimchi_log.info('Md5 file content: "%s"', md5)
            os.remove(md5_report_file)
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
            raise OperationFailed("KCHDR0005E", {'name': name, 'err': e})

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
            raise NotFoundError("KCHDR0001E", {'name': name})

        ctime = os.stat(file_target).st_ctime
        ctime = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(ctime))
        file_target = os.path.split(file_target)[-1]
        file_target = os.path.join("/data/debugreports", file_target)
        return {'uri': file_target,
                'ctime': ctime}

    def delete(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name + '.*')
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError("KCHDR0001E", {'name': name})

        os.remove(file_target)


class DebugReportContentModel(object):
    def __init__(self, **kargs):
        self._debugreport = DebugReportModel()

    def lookup(self, name):
        return self._debugreport.lookup(name)
