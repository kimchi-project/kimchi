#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  ShaoHe Feng <shaohef@linux.vnet.ibm.com>
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

import cherrypy
import os
import re
import subprocess
import urllib2
from threading import Timer

from cherrypy.lib.reprconf import Parser
from kimchi.config import paths, PluginPaths
from kimchi.exception import TimeoutExpired


from kimchi import config
from kimchi.asynctask import AsyncTask
from kimchi.exception import InvalidParameter, TimeoutExpired


kimchi_log = cherrypy.log.error_log
task_id = 0


def _uri_to_name(collection, uri):
    expr = '/%s/(.*?)/?$' % collection
    m = re.match(expr, uri)
    if not m:
        raise InvalidParameter(uri)
    return m.group(1)


def template_name_from_uri(uri):
    return _uri_to_name('templates', uri)


def pool_name_from_uri(uri):
    return _uri_to_name('storagepools', uri)


def get_next_task_id():
    global task_id
    task_id += 1
    return task_id


def add_task(target_uri, fn, objstore, opaque=None):
    id = get_next_task_id()
    AsyncTask(id, target_uri, fn, objstore, opaque)
    return id


def is_digit(value):
    if isinstance(value, int):
        return True
    elif isinstance(value, basestring):
        value = value.strip()
        return value.isdigit()
    else:
        return False


def _load_plugin_conf(name):
    plugin_conf = PluginPaths(name).conf_file
    if not os.path.exists(plugin_conf):
        cherrypy.log.error_log.error("Plugin configuration file %s"
                                     " doesn't exist." % plugin_conf)
        return
    try:
        return Parser().dict_from_file(plugin_conf)
    except ValueError as e:
        cherrypy.log.error_log.error("Failed to load plugin "
                                     "conf from %s: %s" %
                                     (plugin_conf, e.message))


def get_enabled_plugins():
    plugin_dir = paths.plugins_dir
    try:
        dir_contents = os.listdir(plugin_dir)
    except OSError:
        return
    for name in dir_contents:
        if os.path.isdir(os.path.join(plugin_dir, name)):
            plugin_config = _load_plugin_conf(name)
            try:
                if plugin_config['kimchi']['enable']:
                    yield (name, plugin_config)
            except (TypeError, KeyError):
                continue


def import_class(class_path):
    module_name, class_name = class_path.rsplit('.', 1)
    try:
        mod = import_module(module_name)
        return getattr(mod, class_name)
    except (ImportError, AttributeError):
        raise ImportError('Class %s can not be imported' % class_path)


def import_module(module_name):
    return __import__(module_name, globals(), locals(), [''])


def check_url_path(path):
    try:
        code = urllib2.urlopen(path).getcode()
        if code != 200:
            return False
    except (urllib2.URLError, ValueError):
        return False

    return True


def run_command(cmd, timeout=None):
    """
    cmd is a sequence of command arguments.
    timeout is a float number in seconds.
    timeout default value is None, means command run without timeout.
    """
    def kill_proc(proc, timeout_flag):
        try:
            proc.kill()
        except OSError:
            pass
        else:
            timeout_flag[0] = True

    proc = None
    timer = None
    timeout_flag = [False]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if timeout is not None:
            timer = Timer(timeout, kill_proc, [proc, timeout_flag])
            timer.setDaemon(True)
            timer.start()

        out, error = proc.communicate()
        kimchi_log.debug("Run command: '%s'", " ".join(cmd))

        if out or error:
            kimchi_log.debug("out:\n %s\nerror:\n %s", out, error)

        if timeout_flag[0]:
            msg = ("subprocess is killed by signal.SIGKILL for "
                   "timeout %s seconds" % timeout)
            kimchi_log.error(msg)
            raise TimeoutExpired(msg)

        return out, error, proc.returncode
    except TimeoutExpired:
        raise
    except Exception as e:
        msg = "Failed to run command: %s." % " ".join(cmd)
        msg = msg if proc is None else msg + "\n  error code: %s."
        kimchi_log.error("%s\n  %s", msg, e)

        if proc:
            return out, error, proc.returncode
        else:
            return None, None, None
    finally:
        if timer and not timeout_flag[0]:
            timer.cancel()


def parse_cmd_output(output, output_items):
    res = []
    for line in output.split("\n"):
        if line:
            res.append(dict(zip(output_items, line.split())))
    return res


def patch_find_nfs_target(nfs_server):
    cmd = ["showmount", "--no-headers", "--exports", nfs_server]
    try:
        out = run_command(cmd, 10)[0]
    except TimeoutExpired:
        kimchi_log.warning("server %s query timeout, may not have any path "
                           "exported", nfs_server)
        return list()

    targets = parse_cmd_output(out, output_items=['target'])
    for target in targets:
        target['type'] = 'nfs'
        target['host_name'] = nfs_server
    return targets


def listPathModules(path):
    modules = set()
    for f in os.listdir(path):
        base, ext = os.path.splitext(f)
        if ext in ('.py', '.pyc', '.pyo'):
            modules.add(base)
    return sorted(modules)
