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

wdi.SocketQueue = $.spcExtend(wdi.EventObject.prototype, {
	rQ: null,
	sQ: null,
	socket: null,
	
	init: function(c) {
		this.superInit();
		this.socket = c.socket || new wdi.Socket();
		this.rQ = c.rQ || new wdi.FixedQueue();
		this.sQ = c.sQ || new wdi.Queue();
		this.setup();
	},
	
	setup: function() {
		this.socket.addListener('open', function() {
			this.fire('open');
		}, this);
		this.socket.addListener('message', function(data) {
			this.rQ.push(new Uint8Array(data));
			this.fire('message');
		}, this);
		this.socket.addListener('close', function(e) {
			this.fire('close', e);
		}, this);
		this.socket.addListener('error', function(e) {
			this.fire('error', e);
		}, this);
	},
	
	getStatus: function() {
		return this.socket.getStatus();
	},
	
	connect: function(uri) {
		this.socket.connect(uri);
	},
	
	disconnect: function() {
		this.socket.disconnect();
	},
	
	send: function(data, shouldFlush) {
		//check for shouldFlush parameter, by default is true
		if (shouldFlush === undefined) {
			var flush = true;
		} else {
			var flush = shouldFlush;
		}

		//performance: avoid passing through the queue if there is no queue and
		//we have flush!
		if(this.sQ.getLength() == 0 && flush) {
			this.socket.send(data);
			return;
		}

		//normal operation, append to buffer and send if flush
		this.sQ.push(data);
		if (flush) this.flush();
	},
	
	flush: function() {
		var data = this.sQ.shift();
		this.socket.send(data);
	}
});
