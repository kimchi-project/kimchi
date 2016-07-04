#
# Project Kimchi
#
# Copyright IBM Corp, 2016
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
import libvirt
import os

from wok.config import config as wok_config
from wok.exception import InvalidOperation, OperationFailed
from wok.plugins.kimchi import config as kimchi_config
from wok.plugins.kimchi.model.vms import VMModel
from wok.utils import run_command, wok_log


def write_virt_viewer_file(params):
    file_template = """\
[virt-viewer]
type=%(type)s
host=%(host)s
port=%(graphics_port)s
"""
    file_contents = file_template % params

    if params.get('graphics_passwd'):
        file_contents += 'password=%s\n' % params['graphics_passwd']

    try:
        with open(params.get('path'), 'w') as vv_file:
            vv_file.write(file_contents)
    except Exception:
        raise


def _get_request_host():
    host = cherrypy.request.headers.get('Host')
    if not host:
        host = wok_config.get("server", "host")
    host = host.split(':')[0]
    return host


def create_virt_viewer_file(vm_name, graphics_info):
    graphics_type = graphics_info[0]
    graphics_port = graphics_info[2]
    graphics_passwd = graphics_info[3]

    try:
        host = _get_request_host()

        default_dir = kimchi_config.get_virtviewerfiles_path()
        file_path = os.path.join(default_dir, '%s-access.vv' % vm_name)

        file_params = {
            'type': graphics_type,
            'graphics_port': graphics_port,
            'graphics_passwd': graphics_passwd,
            'host': host,
            'path': file_path
        }
        write_virt_viewer_file(file_params)
        return file_path

    except Exception as e:
        raise OperationFailed("KCHVM0084E",
                              {'name': vm_name, 'err': e.message})


class VMVirtViewerFileModel(object):
    def __init__(self, **kargs):
        self.conn = kargs['conn']

    def _check_if_vm_running(self, name):
        dom = VMModel.get_vm(name, self.conn)
        d_info = dom.info()
        if d_info[0] != libvirt.VIR_DOMAIN_RUNNING:
            raise InvalidOperation("KCHVM0083E", {'name': name})

    def lookup(self, name):
        self._check_if_vm_running(name)
        graphics_info = VMModel.get_graphics(name, self.conn)
        file_path = create_virt_viewer_file(name, graphics_info)

        return 'plugins/kimchi/data/virtviewerfiles/%s' %\
               os.path.basename(file_path)


class FirewallManager(object):

    @staticmethod
    def check_if_firewall_cmd_enabled():
        _, _, r_code = run_command(['firewall-cmd', '--state', '-q'])
        return r_code == 0

    @staticmethod
    def check_if_ufw_enabled():
        _, _, r_code = run_command(['ufw', 'status'])
        return r_code == 0

    def __init__(self):
        self.opened_ports = {}
        self.firewall_provider = None

        if self.check_if_firewall_cmd_enabled():
            self.firewall_provider = FirewallCMDProvider()
        elif self.check_if_ufw_enabled():
            self.firewall_provider = UFWProvider()
        else:
            self.firewall_provider = IPTablesProvider()

    def add_vm_graphics_port(self, vm_name, port):
        self.firewall_provider.enable_tcp_port(port)
        self.opened_ports[vm_name] = port

    def remove_vm_graphics_port(self, vm_name):
        port = self.opened_ports.pop(vm_name, None)
        if port:
            self.firewall_provider.disable_tcp_port(port)

    def remove_all_vms_ports(self):
        for port in self.opened_ports.values():
            self.firewall_provider.disable_tcp_port(port)

        self.opened_ports = {}


class FirewallCMDProvider(object):

    @staticmethod
    def enable_tcp_port(port):
        _, err, r_code = run_command(
            ['firewall-cmd', '--add-port=%s/tcp' % port]
        )
        if r_code != 0:
            wok_log.error('Error when adding port to firewall-cmd: %s' % err)

    @staticmethod
    def disable_tcp_port(port):
        _, err, r_code = run_command(
            ['firewall-cmd', '--remove-port=%s/tcp' % port]
        )
        if r_code != 0:
            wok_log.error('Error when removing port from '
                          'firewall-cmd: %s' % err)


class UFWProvider(object):

    @staticmethod
    def enable_tcp_port(port):
        _, err, r_code = run_command(['ufw', 'allow', '%s/tcp' % port])
        if r_code != 0:
            wok_log.error('Error when adding port to ufw: %s' % err)

    @staticmethod
    def disable_tcp_port(port):
        _, err, r_code = run_command(['ufw', 'deny', '%s/tcp' % port])
        if r_code != 0:
            wok_log.error('Error when removing port from ufw: %s' % err)


class IPTablesProvider(object):

    @staticmethod
    def enable_tcp_port(port):
        cmd = ['iptables', '-I', 'INPUT', '-p', 'tcp', '--dport',
               port, '-j', 'ACCEPT']
        _, err, r_code = run_command(cmd)
        if r_code != 0:
            wok_log.error('Error when adding port to iptables: %s' % err)

    @staticmethod
    def disable_tcp_port(port):
        cmd = ['iptables', '-D', 'INPUT', '-p', 'tcp', '--dport',
               port, '-j', 'ACCEPT']
        _, err, r_code = run_command(cmd)
        if r_code != 0:
            wok_log.error('Error when removing port from itables: %s' % err)
