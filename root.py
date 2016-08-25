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

import json
import os
import cherrypy

from wok.plugins.kimchi import config, mockmodel, websocket
from wok.plugins.kimchi.i18n import messages
from wok.plugins.kimchi.control import sub_nodes
from wok.plugins.kimchi.model import model as kimchiModel
from wok.plugins.kimchi.utils import upgrade_objectstore_data
from wok.plugins.kimchi.utils import upgrade_objectstore_memory
from wok.plugins.kimchi.utils import upgrade_objectstore_template_disks
from wok.root import WokRoot
from wok.utils import upgrade_objectstore_schema


class Kimchi(WokRoot):
    def __init__(self, wok_options):
        make_dirs = [
            os.path.dirname(os.path.abspath(config.get_object_store())),
            os.path.abspath(config.get_distros_store()),
            os.path.abspath(config.get_screenshot_path()),
            os.path.abspath(config.get_virtviewerfiles_path())
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
        super(Kimchi, self).__init__(self.model, dev_env)

        for ident, node in sub_nodes.items():
            setattr(self, ident, node(self.model))

        if isinstance(self.model, kimchiModel.Model):
            ws_proxy = websocket.new_ws_proxy()
            cherrypy.engine.subscribe('exit', ws_proxy.terminate)

        self.api_schema = json.load(open(os.path.join(os.path.dirname(
                                    os.path.abspath(__file__)), 'API.json')))
        self.paths = config.kimchiPaths
        self.domain = 'kimchi'
        self.messages = messages

        # Some paths or URI's present in the objectstore have changed after
        # Kimchi 2.0.0 release. Check here if an upgrade in the schema and data
        # are necessary.
        if upgrade_objectstore_schema(config.get_object_store(), 'version'):
            upgrade_objectstore_data('icon', 'images', 'plugins/kimchi/')
            upgrade_objectstore_data('storagepool', '/storagepools',
                                     '/plugins/kimchi')
            upgrade_objectstore_template_disks(self.model.conn)

        # Upgrade memory data, if necessary
        upgrade_objectstore_memory()

    def get_custom_conf(self):
        return config.KimchiConfig()
