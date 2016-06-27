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

from wok.control.base import Collection, Resource
from wok.control.utils import UrlSubNode


TEMPLATES_REQUESTS = {
    'POST': {'default': "KCHTMPL0001L"},
}

TEMPLATE_REQUESTS = {
    'DELETE': {'default': "KCHTMPL0002L"},
    'PUT': {'default': "KCHTMPL0003L"},
    'POST': {
        'clone': "KCHTMPL0004L",
    },
}


@UrlSubNode('templates', True)
class Templates(Collection):
    def __init__(self, model):
        super(Templates, self).__init__(model)
        self.role_key = 'templates'
        self.admin_methods = ['GET', 'POST']
        self.resource = Template

        # set user log messages and make sure all parameters are present
        self.log_map = TEMPLATES_REQUESTS
        self.log_args.update({'name': ''})


class Template(Resource):
    def __init__(self, model, ident):
        super(Template, self).__init__(model, ident)
        self.role_key = 'templates'
        self.admin_methods = ['PUT', 'POST', 'DELETE']
        self.uri_fmt = "/templates/%s"
        self.clone = self.generate_action_handler('clone')
        self.log_map = TEMPLATE_REQUESTS

    @property
    def data(self):
        return {
            'name': self.ident,
            'icon': self.info['icon'],
            'invalid': self.info['invalid'],
            'os_distro': self.info['os_distro'],
            'os_version': self.info['os_version'],
            'memory': self.info['memory'],
            'cdrom': self.info.get('cdrom', None),
            'disks': self.info['disks'],
            'networks': self.info['networks'],
            'folder': self.info.get('folder', []),
            'graphics': self.info['graphics'],
            'cpu_info': self.info.get('cpu_info')
        }
