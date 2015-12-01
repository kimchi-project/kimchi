#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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

import json
import os
import cherrypy

from wok.plugins.kimchi import config, mockmodel, vnc
from wok.plugins.kimchi.i18n import messages
from wok.plugins.kimchi.control import sub_nodes
from wok.plugins.kimchi.model import model as kimchiModel
from wok.plugins.kimchi.utils import upgrade_objectstore_data
from wok.plugins.kimchi.utils import upgrade_objectstore_schema
from wok.root import WokRoot


class KimchiRoot(WokRoot):
    def __init__(self, wok_options):
        make_dirs = [
            os.path.dirname(os.path.abspath(config.get_object_store())),
            os.path.abspath(config.get_distros_store()),
            os.path.abspath(config.get_screenshot_path())
        ]
        for directory in make_dirs:
            if not os.path.isdir(directory):
                os.makedirs(directory)

        if hasattr(wok_options, "model"):
            self.model = wok_options.model
        elif wok_options.test:
            self.model = mockmodel.MockModel()
        else:
            self.model = kimchiModel.Model()

        dev_env = wok_options.environment != 'production'
        super(KimchiRoot, self).__init__(self.model, dev_env)

        for ident, node in sub_nodes.items():
            setattr(self, ident, node(self.model))

        if isinstance(self.model, kimchiModel.Model):
            vnc_ws_proxy = vnc.new_ws_proxy()
            cherrypy.engine.subscribe('exit', vnc_ws_proxy.terminate)

        self.api_schema = json.load(open(os.path.join(os.path.dirname(
                                    os.path.abspath(__file__)), 'API.json')))
        self.paths = config.kimchiPaths
        self.domain = 'kimchi'
        self.messages = messages

        # Some paths or URI's present in the objectstore have changed after
        # Kimchi 2.0.0 release. Check here if an upgrade in the schema and data
        # are necessary.
        if upgrade_objectstore_schema('version'):
            upgrade_objectstore_data('icon', 'images', 'plugins/kimchi/')
            upgrade_objectstore_data('storagepool', '/storagepools',
                                     '/plugins/kimchi')

    def get_custom_conf(self):
        return config.KimchiConfig()
