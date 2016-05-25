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

import cherrypy
import libvirt
import time

from wok.exception import OperationFailed


class LibvirtEvents(object):
    def __init__(self):
        # Register default implementation of event handlers
        if libvirt.virEventRegisterDefaultImpl() < 0:
            raise OperationFailed('KCHEVENT0001E')

        # Run a background thread with the event loop. Using cherrypy
        # BackgroundTask class due to issues when using threading module with
        # cherrypy.
        self.event_loop_thread = cherrypy.process.plugins.BackgroundTask(
            2,
            self._event_loop_run
        )
        self.event_loop_thread.setName('KimchiLibvirtEventLoop')
        self.event_loop_thread.setDaemon(True)
        self.event_loop_thread.start()

        # Set an event timeout to control the self._event_loop_run
        if libvirt.virEventAddTimeout(0, self._kimchi_EventTimeout, None) < 0:
            raise OperationFailed('KCHEVENT0002E')

    # Event loop method to be executed in background as thread
    def _event_loop_run(self):
        while True:
            if libvirt.virEventRunDefaultImpl() < 0:
                raise OperationFailed('KCHEVENT0003E')

    def is_event_loop_alive(self):
        return self.event_loop_thread.isAlive()

    # Event loop handler used to limit length of waiting for any other event.
    def _kimchi_EventTimeout(self, timer, opaque):
        time.sleep(0.01)
