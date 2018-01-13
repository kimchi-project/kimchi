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

wdi.socketStatus = {
	'idle':0,
	'prepared':1,
	'connected':2,
	'disconnected':3,
	'failed':4
};
//Works only with arrays of bytes (this means each value is a number in 0 to 255)
wdi.Socket = $.spcExtend(wdi.EventObject.prototype, {
	websocket: null,
	status: wdi.socketStatus.idle,
	binary: false,
	
	connect: function(uri) {
		var self = this;
		var protocol = 'base64'; //default protocol
		
		if(Modernizr['websocketsbinary']) {
			protocol = 'binary';
			this.binary = true;
		}

		this.websocket = new WebSocket(uri, protocol);
		
		wdi.Debug.log("Socket: using protocol: "+protocol);
		
		if(this.binary) {
			this.websocket.binaryType = 'arraybuffer';
		}
		
		this.status = wdi.socketStatus.prepared;
		this.websocket.onopen = function() {
			self.status = wdi.socketStatus.connected;
			self.fire('open');
		};
		this.websocket.onmessage = function(e) {
			self.fire('message', e.data);
		};
		this.websocket.onclose = function(e) {
			self.status = wdi.socketStatus.disconnected;
			console.warn('Spice Web Client: ', e.code, e.reason);
			self.disconnect();
			self.fire('error', e);
		};
		this.websocket.onerror = function(e) {
			self.status = wdi.socketStatus.failed;
			self.fire('error', e);
		};
	},

	setOnMessageCallback: function(callback) {
		this.websocket.onmessage = callback;
	},
	
	send: function(message) {
		try {
			this.websocket.send(this.encode_message(message));
		} catch (err) {
			this.status = wdi.socketStatus.failed;
			this.fire('error', err);
		}
	},
	
	disconnect: function() {
		if (this.websocket) {
			this.websocket.onopen = function() {};
			this.websocket.onmessage = function() {};
			this.websocket.onclose = function() {};
			this.websocket.onerror = function() {};
			this.websocket.close();
			this.websocket = null;
		}
	},
	
	setStatus: function(status) {
		this.status = status;
		this.fire('status', status);
	},
	
	getStatus: function() {
		return this.status;
	},
	
	encode_message: function(mess) {
		if(!this.binary) {
			var arr = Base64.encode(mess);
			return arr;
		} 
		
		var len = mess.length;
		
		var buffer = new ArrayBuffer(len);
		var u8 = new Uint8Array(buffer);
		
		u8.set(mess);
	
		return u8;
	}
});
