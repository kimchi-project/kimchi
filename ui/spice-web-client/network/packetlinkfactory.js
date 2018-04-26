/*
 eyeOS Spice Web Client
Copyright (c) 2015 eyeOS S.L.

Contact Jose Carlos Norte (jose@eyeos.com) for more information about this software.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License version 3 as published by the
Free Software Foundation.
 
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
details.
 
You should have received a copy of the GNU Affero General Public License
version 3 along with this program in the file "LICENSE".  If not, see 
<http://www.gnu.org/licenses/agpl-3.0.txt>.
 
See www.eyeos.org for more details. All requests should be sent to licensing@eyeos.org
 
The interactive user interfaces in modified source and object code versions
of this program must display Appropriate Legal Notices, as required under
Section 5 of the GNU Affero General Public License version 3.
 
In accordance with Section 7(b) of the GNU Affero General Public License version 3,
these Appropriate Legal Notices must retain the display of the "Powered by
eyeos" logo and retain the original copyright notice. If the display of the 
logo is not reasonably feasible for technical reasons, the Appropriate Legal Notices
must display the words "Powered by eyeos" and retain the original copyright notice. 
 */

wdi.PacketLinkFactory = {
	extract: function(header, queue) {
		switch (header.type) {
			case wdi.SpiceVars.SPICE_MSG_SET_ACK:
				return new wdi.RedSetAck().demarshall(queue);
			case wdi.SpiceVars.SPICE_MSG_PING:
				return new wdi.RedPing().demarshall(queue, header.size);
			case wdi.SpiceVars.SPICE_MSG_MIGRATE:
				return new wdi.RedMigrate().demarshall(queue);
			case wdi.SpiceVars.SPICE_MSG_MIGRATE_DATA:
				return new wdi.RedMigrateData().demarshall(queue, header.size);
			case wdi.SpiceVars.SPICE_MSG_WAIT_FOR_CHANNELS:
				return new wdi.RedWaitForChannels().demarshall(queue);
			case wdi.SpiceVars.SPICE_MSG_DISCONNECTING:
				return new wdi.RedDisconnect().demarshall(queue);
			case wdi.SpiceVars.SPICE_MSG_NOTIFY:
				var packet = new wdi.RedNotify().demarshall(queue);
				return packet;
			case wdi.SpiceVars.SPICE_MSG_MAIN_MOUSE_MODE:
				return new wdi.SpiceMouseMode().demarshall(queue);
		}
	}
};

wdi.PacketLinkProcess = {
	process: function(header, packet, channel) {
		switch(header.type) {
			case wdi.SpiceVars.SPICE_MSG_SET_ACK:
				var body = wdi.SpiceObject.numberTo32(packet.generation);
				channel.setAckWindow(packet.window)
				channel.sendObject(body, wdi.SpiceVars.SPICE_MSGC_ACK_SYNC);
				break;
			case wdi.SpiceVars.SPICE_MSG_PING:
				var body = new wdi.RedPing({id: packet.id, time: packet.time}).marshall();
				channel.sendObject(body, wdi.SpiceVars.SPICE_MSGC_PONG);
				break;
			case wdi.SpiceVars.SPICE_MSG_MAIN_MOUSE_MODE:
				channel.fire('mouseMode', packet.current_mode);
				break;
			case wdi.SpiceVars.SPICE_MSG_NOTIFY:
				channel.fire('notify');
				break;
		}
	}
};
