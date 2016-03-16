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

import libvirt
import os
import socket
import sys
import threading
import time

from multiprocessing import Process

from wok.plugins.kimchi import model
from wok.plugins.kimchi.config import config
from wok.utils import wok_log


SOCKET_QUEUE_BACKLOG = 0
CTRL_Q = '\x11'
BASE_DIRECTORY = '/run'


class SocketServer(Process):
    """Unix socket server for guest console access.

    Implements a unix socket server for each guest, this server will receive
    data from a particular client, forward that data to the guest console,
    receive the response from the console and send the response back to the
    client.

    Features:
        - one socket server per client connection;
        - server listens to unix socket;
        - exclusive connection per guest;
        - websockity handles the proxy between the client websocket to the
          local unix socket;

    Note:
        - old versions (< 0.6.0)of websockify don't handle their children
        processes accordingly, leaving a zombie process behind (this also
        happens with novnc).
    """

    def __init__(self, guest_name, URI):
        """Constructs a unix socket server.

        Listens to connections on /run/<guest name>.
        """
        Process.__init__(self)

        self._guest_name = guest_name
        self._uri = URI
        self._server_addr = os.path.join(BASE_DIRECTORY, guest_name)
        if os.path.exists(self._server_addr):
            raise RuntimeError('There is an existing connection to %s' %
                               guest_name)

        self._socket = socket.socket(socket.AF_UNIX,
                                     socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET,
                                socket.SO_REUSEADDR,
                                1)
        self._socket.bind(self._server_addr)
        self._socket.listen(SOCKET_QUEUE_BACKLOG)
        wok_log.info('[%s] socket server to guest %s created', self.name,
                     guest_name)

    def run(self):
        """Implements customized run method from Process.
        """
        self.listen()

    def _is_vm_listening_serial(self, console):
        """Checks if the guest is listening (reading/writing) to the serial
        console.
        """
        is_listening = []

        def _test_output(stream, event, opaque):
            is_listening.append(1)

        def _event_loop():
            while not is_listening:
                libvirt.virEventRunDefaultImpl()

        console.eventAddCallback(libvirt.VIR_STREAM_EVENT_READABLE,
                                 _test_output,
                                 None)
        libvirt_loop = threading.Thread(target=_event_loop)
        libvirt_loop.start()

        console.send("\n")
        libvirt_loop.join(1)

        if not libvirt_loop.is_alive():
            console.eventRemoveCallback()
            return True

        console.eventRemoveCallback()
        return False

    def _send_to_client(self, stream, event, opaque):
        """Handles libvirt stream readable events.

        Each event will be send back to the client socket.
        """
        try:
            data = stream.recv(1024)

        except Exception as e:
            wok_log.info('[%s] Error when reading from console: %s',
                         self.name, e.message)
            return

        # return if no data received or client socket(opaque) is not valid
        if not data or not opaque:
            return

        opaque.send(data)

    def libvirt_event_loop(self, guest, client):
        """Runs libvirt event loop.
        """
        # stop the event loop when the guest is not running
        while guest.is_running():
            libvirt.virEventRunDefaultImpl()

        # shutdown the client socket to unblock the recv and stop the
        # server as soon as the guest shuts down
        client.shutdown(socket.SHUT_RD)

    def listen(self):
        """Prepares the environment before starts to accept connections

        Initializes and destroy the resources needed to accept connection.
        """
        libvirt.virEventRegisterDefaultImpl()
        try:
            guest = LibvirtGuest(self._guest_name, self._uri, self.name)

        except Exception as e:
            wok_log.error('[%s] Cannot open the guest %s due to %s',
                          self.name, self._guest_name, e.message)
            self._socket.close()
            sys.exit(1)

        except (KeyboardInterrupt, SystemExit):
            self._socket.close()
            sys.exit(1)

        console = None
        try:
            console = guest.get_console()
            if console is None:
                wok_log.error('[%s] Cannot get the console to %s',
                              self.name, self._guest_name)
                return

            if not self._is_vm_listening_serial(console):
                sys.exit(1)

            self._listen(guest, console)

        # clear resources aquired when the process is killed
        except (KeyboardInterrupt, SystemExit):
            pass

        finally:
            wok_log.info("[%s] Shutting down the socket server to %s console",
                         self.name, self._guest_name)
            self._socket.close()
            if os.path.exists(self._server_addr):
                os.unlink(self._server_addr)

            try:
                console.eventRemoveCallback()

            except Exception as e:
                wok_log.info('[%s] Callback is probably removed: %s',
                             self.name, e.message)

            guest.close()

    def _listen(self, guest, console):
        """Accepts client connections.

        Each connection is directly linked to the desired guest console. Thus
        any data received from the client can be send to the guest console as
        well as any response from the guest console can be send back to the
        client console.
        """
        client, client_addr = self._socket.accept()
        client.settimeout(config.get('kimchi', {}).
                          get('SERIAL_CONSOLE_TIMEOUT', 120))
        wok_log.info('[%s] Client connected to %s', self.name,
                     self._guest_name)

        # register the callback to receive any data from the console
        console.eventAddCallback(libvirt.VIR_STREAM_EVENT_READABLE,
                                 self._send_to_client,
                                 client)

        # start the libvirt event loop in a python thread
        libvirt_loop = threading.Thread(target=self.libvirt_event_loop,
                                        args=(guest, client))
        libvirt_loop.start()

        while True:
            data = ''
            try:
                data = client.recv(1024)

            except Exception as e:
                wok_log.info('[%s] Client disconnected from %s: %s',
                             self.name, self._guest_name, e.message)
                break

            if not data or data == CTRL_Q:
                break

            # if the console can no longer be accessed, close everything
            # and quits
            try:
                console.send(data)

            except:
                wok_log.info('[%s] Console of %s is not accessible',
                             self.name, self._guest_name)
                break

        # clear used resources when the connection is closed and, if possible,
        # tell the client the connection was lost.
        try:
            client.send('\r\n\r\nClient disconnected\r\n')

        except:
            pass
# socket_server


class LibvirtGuest(object):

    def __init__(self, guest_name, uri, process_name):
        """
        Constructs a guest object that opens a connection to libvirt and
        searchs for a particular guest, provided by the caller.
        """
        self._proc_name = process_name
        try:
            libvirt = model.libvirtconnection.LibvirtConnection(uri)
            self._guest = model.vms.VMModel.get_vm(guest_name, libvirt)

        except Exception as e:
            wok_log.error('[%s] Cannot open guest %s: %s', self._proc_name,
                          guest_name, e.message)
            raise

        self._libvirt = libvirt.get()
        self._name = guest_name
        self._stream = None

    def is_running(self):
        """
        Checks if this guest is currently in a running state.
        """
        return self._guest.state(0)[0] == libvirt.VIR_DOMAIN_RUNNING or \
            self._guest.state(0)[0] == libvirt.VIR_DOMAIN_PAUSED

    def get_console(self):
        """
        Opens a console to this guest and returns a reference to it.
        Note: If another instance (eg: virsh) has an existing console opened
        to this guest, this code will steal that console.
        """
        # guest must be in a running state to get its console
        counter = 10
        while not self.is_running():
            wok_log.info('[%s] Guest %s is not running, waiting for it',
                         self._proc_name, self._name)

            counter -= 1
            if counter <= 0:
                return None

            time.sleep(1)

        # attach a stream in the guest console so we can read from/write to it
        if self._stream is None:
            wok_log.info('[%s] Opening the console for guest %s',
                         self._proc_name, self._name)
            self._stream = self._libvirt.newStream(libvirt.VIR_STREAM_NONBLOCK)
            self._guest.openConsole(None,
                                    self._stream,
                                    libvirt.VIR_DOMAIN_CONSOLE_FORCE |
                                    libvirt.VIR_DOMAIN_CONSOLE_SAFE)
        return self._stream

    def close(self):
        """Closes the libvirt connection.
        """
        self._libvirt.close()
# guest


def main(guest_name, URI='qemu:///system'):
    """Main entry point to create a socket server.

    Starts a new socket server to listen messages to/from the guest.
    """
    server = None
    try:
        server = SocketServer(guest_name, URI)

    except Exception as e:
        wok_log.error('Cannot create the socket server: %s', e.message)
        raise

    server.start()
    return server


if __name__ == '__main__':
    """Executes a stand alone instance of the socket server.

    This may be useful for testing/debugging.

    In order to debug, add the path  before importing kimchi/wok code:
        sys.path.append('../../../')

    start the server:
        python serialconsole.py <guest_name>

    and, on another terminal, run:
        netcat -U /run/<guest_name>
    """
    argc = len(sys.argv)
    if argc != 2:
        print 'usage: ./%s <guest_name>' % sys.argv[0]
        sys.exit(1)

    main(sys.argv[1])
