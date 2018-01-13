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

wdi.BusConnection = $.spcExtend(wdi.EventObject.prototype, {
	ws: null,
	subscriptions: [],
	_busUser: null,
	_busPass: null,
	fileServerBaseUrl: null,
	queue: '',
	binary: false,

	init: function(c) {
		this.superInit();
		this.ws = c.websocket || new wdi.WebSocketWrapper();
		this.clusterNodeChooser = c.clusterNodeChooser || new wdi.ClusterNodeChooser();
		this.binary = c.binary || false;
	},

	connect: function(c) {
		if (!c['useBus']) {
			wdi.Debug.warn("Not using the bus");
			return;
		}
        this._vdiBusToken = c['vdiBusToken'];
		if (!c['busHostList']) {
			wdi.Debug.warn("Deprecated: using old busHost & busPort params");
			c['busHostList'] = [{
				host: c['busHost'],
				port: c['busPort']
			}];
		}
		this.clusterNodeChooser.setNodeList(c['busHostList']);
		if (Modernizr['websocketsbinary']) {
			this.binary = true;
		}
		this._busUser = c['busUser'];
		this._busPass = c['busPass'];
		this._websockifyProtocol = c['protocol'];
		this._websockifyHost = c['host'];
		this._websockifyPort = c['port'];
		this.fileServerBaseUrl = c['busFileServerBaseUrl'];
		this.subscriptions = c['busSubscriptions'];

		this._connectToNextHost();
	},

	_connectToNextHost: function () {
		var busData = this.clusterNodeChooser.getAnother();

		// c['protocol'] is the protocol we use to connect to websockify
		// ie: ws, wss, https, ...
		var url = wdi.Utils.generateWebSocketUrl(
			this._websockifyProtocol,
			this._websockifyHost,
			this._websockifyPort,
			busData.host,
			busData.port,
			'raw',
            this._vdiBusToken
		);
		var websocketProtocol = 'base64';
		if (this.binary) {
			websocketProtocol = 'binary';
		}
		this.ws.connect(url, websocketProtocol);

		wdi.Debug.log("BusConnection: using protocol: " + websocketProtocol);

		if (this.binary) {
			this.ws.setBinaryType('arraybuffer');
		}
		this.setListeners();
	},

	disconnect: function() {
		this.ws.close();
	},

	setListeners: function() {
		var self = this;
		this.ws.onOpen(function(e) {
			self._send("CONNECT\nlogin:" + self._busUser + "\npasscode:" + self._busPass + "\n\n\x00");
		});

		this.ws.onMessage(function(e) {
			var message;
			var result;
			if (!self.binary) {
				message = Base64.decodeStr(e.data);
			} else {
				message = String.fromCharCode.apply(null, new Uint8Array(e.data));
				// Fix accented chars
				// [ http://stackoverflow.com/questions/5396560/how-do-i-convert-special-utf-8-chars-to-their-iso-8859-1-equivalent-using-javasc ]
				message = decodeURIComponent(escape(message));
			}
			var subChunks = message.split("\0");
			if (subChunks.length == 1) {
				// there is no \0 in the full message, add it to the queue
				self.queue += subChunks[0];
			} else {
				// at least one \0, process all but the last subchunk (that has no \0)
				for (var i = 0; i < subChunks.length - 1; i++) {
					message = self.queue + subChunks[i];
					result = self.parseMessage(message);
					self.fire('busMessage', result);
					self.queue = '';
				}
				// last chunk is now the queue
				self.queue = subChunks[subChunks.length - 1];
			}
		});

		this.ws.onClose(function(e) {
			wdi.Debug.log('BusConnection CLOSED! connecting again in 1 second');
			self.fire('error', e);
		});

		this.ws.onError(function(e) {
			wdi.Debug.error('BusConnection ERROR:',  e);
		});
	},

	parseMessage: function(message) {
		try {
			var arr = message.split("\n\n");
			var header = arr[0].trim();
			var body = arr[1].replace(/\x00/, '').trim();
			if (body.length != 0) {
				// there is content, so convert to object
				body = JSON.parse(body);
			} else {
				body = null;
			}
			arr = header.split("\n");
			var verb = arr.shift();
			header = "{";
			var len = arr.length;
			for (var i = 0;i < len;i++) {
				var headerName = arr[i].split(':')[0];
				header += '"' + headerName + '":"' + arr[i].replace(headerName + ':', '') + '"';
				if (i != len-1) {
					header += ",";
				}
			}
			header += "}";

			return {'verb':verb, 'header':JSON.parse(header), 'body':body};
		} catch (e) {
			wdi.Debug.error("Error parsing Bus Info: ", e);
			return {"verb":"ERROR"};
		}
	},

	setSubscriptions: function() {
		var len = this.subscriptions.length;
		for (var i = 0; i < len;i++) {
			this.subscribe(this.subscriptions[i]);
		}
	},

	send: function(message) {
		var destination = this.subscriptions[0];
		this._send("SEND\ndestination:" + destination + "\ncontent-type:text/plain\n\n" + JSON.stringify(message) + "\x00");
	},

	subscribe: function(destination) {
		//header browser: true for queue's to multiple subscribers
		this._send("SUBSCRIBE\ndestination:" + destination + "\n\n\x00");
	},

	_send: function(message) {
		if (!this.binary) {
			this.ws.send(Base64.encodeStr(message));
		} else {
			this.ws.send(message);
		}
	}
});
