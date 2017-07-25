#
# Project Kimchi
#
# Copyright IBM Corp, 2015-2017
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

from wok.basemodel import BaseModel
from wok.objectstore import ObjectStore
from wok.plugins.kimchi import config
from wok.pushserver import send_wok_notification
from wok.utils import get_all_model_instances, get_model_instances

from wok.plugins.kimchi.model.libvirtconnection import LibvirtConnection
from wok.plugins.kimchi.model.libvirtevents import LibvirtEvents


class Model(BaseModel):
    def __init__(self, libvirt_uri=None, objstore_loc=None):

        self.objstore = ObjectStore(objstore_loc or config.get_object_store())
        self.conn = LibvirtConnection(libvirt_uri)

        # Register for libvirt events
        self.events = LibvirtEvents()
        self.events.handleEnospc(self.conn)
        self.events.registerPoolEvents(self.conn, self._events_handler,
                                       'storages')

        kargs = {'objstore': self.objstore, 'conn': self.conn,
                 'eventsloop': self.events}

        models = get_all_model_instances(__name__, __file__, kargs)

        # Import task model from Wok
        instances = get_model_instances('wok.model.tasks')
        for instance in instances:
            models.append(instance(**kargs))

        super(Model, self).__init__(models)

    def _events_handler(self, conn, pool, ev, details, opaque):
        # Do not use any known method (POST, PUT, DELETE) as it is used by Wok
        # engine and may lead in having 2 notifications for the same action
        send_wok_notification('/plugins/kimchi', opaque, 'METHOD')
