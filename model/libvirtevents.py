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
from wok.message import WokMessage
from wok.model.notifications import add_notification
from wok.utils import wok_log


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

    def event_enospc_cb(self, conn, dom, path, dev, action, reason, args):
        if reason == "enospc":
            info = {
                "vm": dom.name(),
                "srcPath": path,
                "devAlias": dev,
            }
            add_notification("KCHEVENT0004W", info, '/plugins/kimchi')
            msg = WokMessage("KCHEVENT0004W", info, '/plugins/kimchi')
            wok_log.warning(msg.get_text())

    def handleEnospc(self, conn):
        """
        Register Libvirt IO_ERROR_REASON event to handle host ENOSPC
        """
        try:
            conn.get().domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON,
                self.event_enospc_cb,
                libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON
            )
        except (libvirt.libvirtError, AttributeError) as e:
            if type(e) == AttributeError:
                reason = 'Libvirt service is not running'
            else:
                reason = e.message
            wok_log.error("Register of ENOSPC event failed: %s" % reason)

    def registerAttachDevicesEvent(self, conn, cb, arg):
        """
        register libvirt event to listen to devices attachment
        """
        try:
            return conn.get().domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_ADDED,
                cb,
                arg)

        except (AttributeError, libvirt.libvirtError), e:
            wok_log.error("register attach event failed: %s" % e.message)

    def registerDetachDevicesEvent(self, conn, cb, arg):
        """
        register libvirt event to listen to devices detachment
        """
        try:
            return conn.get().domainEventRegisterAny(
                None,
                libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_REMOVED,
                cb,
                arg)

        except libvirt.libvirtError as e:
            wok_log.error("register detach event failed: %s" % e.message)
