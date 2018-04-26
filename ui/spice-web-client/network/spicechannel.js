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
//Must fire event types: connectionId and message

wdi.SpiceChannel = $.spcExtend(wdi.EventObject.prototype, {
	counter: 0,
	ackWindow: 0,
	connectionId: 0,
	socketQ: null,
	packetReassembler: null,
	channel: 1,
	proxy: null,
	token: null,
	
	init: function(c) {
		this.superInit();
		this.socketQ = c.socketQ || new wdi.SocketQueue();
		this.packetReassembler = c.packetReassembler || wdi.ReassemblerFactory.getPacketReassembler(this.socketQ);
		this.setListeners();
		this.ackWindow = 0;
	},

	setListeners: function() {
		var date;
		this.packetReassembler.addListener('packetComplete', function(e) {
			var rawMessage = e;
			if (rawMessage.status === 'spicePacket') {
				if (wdi.logOperations) {
					wdi.DataLogger.logNetworkTime();
					date = Date.now();
				}
				var rsm = this.getRawSpiceMessage(rawMessage.data);
				if (rsm) {
					if (wdi.logOperations && rsm.channel === wdi.SpiceVars.SPICE_CHANNEL_DISPLAY) {
						wdi.DataLogger.setStartTime(date);
					}
					this.fire('message', rsm);
				}
			} else if (rawMessage.status === 'reply') {
				var packet = this.getRedLinkReplyBytes(rawMessage.data);
				this.send(packet);
			} else if (rawMessage.status === 'errorCode') {
				var packet = this.getErrorCodeBytes(rawMessage.data);
				if (packet) {
					this.send(packet);
				}
				this.fire('channelConnected');
			}
		}, this);
		
		this.socketQ.addListener('open', function() {
			var packet = this.getRedLinkMessBytes();
			this.send(packet);
			this.proxy ? this.proxy.end() : false;
		}, this);

		this.socketQ.addListener('close', function(e) {
			if (this.channel === 1) {
				this.fire('error', e);
			}
			this.socketQ.disconnect();
		}, this);

		this.socketQ.addListener('error', function() {
			this.fire('error', 3);
			this.socketQ.disconnect();
//			throw new wdi.Exception({message:"Socket error", errorCode: 2});
		}, this);
	},

	connect: function(connectionInfo, channel, connectionId, proxy) {
		var url = wdi.Utils.generateWebSocketUrl(connectionInfo.protocol, connectionInfo.host, connectionInfo.port, connectionInfo.vmHost, connectionInfo.vmPort, 'spice', connectionInfo.vmInfoToken);
		this.channel = channel;
		this.connectionId = connectionId || 0;
		this.socketQ.connect(url);
		this.proxy = proxy;
		this.token = connectionInfo.token;
		this.packetReassembler.start();
	},

	disconnect: function () {
		this.socketQ.disconnect();
	},

	send: function(data, flush) {
		this.socketQ.send(data, flush);
	},

	sendObject: function(data, type, flush) {
		var packet = new wdi.SpiceDataHeader({
			type:type, 
			size:data.length
		}).marshall();
		
		packet = packet.concat(data);
		
		this.send(packet, flush);
	},
	
	setAckWindow: function(window) {
		this.ackWindow = window;
		this.counter = 0;
	},

	getRawSpiceMessage: function (rawData) {
		var headerQueue = wdi.GlobalPool.create('ViewQueue');
		var body = wdi.GlobalPool.create('ViewQueue');

		var header = new Uint8Array(rawData, 0, wdi.SpiceDataHeader.prototype.objectSize);
		headerQueue.setData(header);
		var headerObj = new wdi.SpiceDataHeader().demarshall(headerQueue);
		wdi.GlobalPool.discard('ViewQueue', headerQueue);
		var rawBody = rawData.subarray(wdi.SpiceDataHeader.prototype.objectSize);
		body.setData(rawBody);

		this.counter++;

		if(this.ackWindow && this.counter === this.ackWindow) {
			this.counter = 0;
			var ack = new wdi.SpiceDataHeader({
				type: wdi.SpiceVars.SPICE_MSGC_ACK,
				size:0
			}).marshall();
			this.send(ack);
		}

		var packet = wdi.PacketLinkFactory.extract(headerObj, body) || false;
		if (packet) {
			wdi.PacketLinkProcess.process(headerObj, packet, this);
			wdi.GlobalPool.discard('ViewQueue', body);
			return false;
		} else {
			var rawSpiceMessage = wdi.GlobalPool.create('RawSpiceMessage');
			rawSpiceMessage.set(headerObj, body, this.channel);
			return rawSpiceMessage;
		}
	},


	//This functions are to avoid hardcoded values on logic
	getRedLinkReplyBytes: function(data) {
		if (this.token) {
			var newq = new wdi.ViewQueue();
			newq.setData(data);
			newq.eatBytes(wdi.SpiceLinkHeader.prototype.objectSize)
			var myBody = new wdi.SpiceLinkReply().demarshall(newq);

			//Returnnig void bytes or encrypted ticket
			var key = wdi.SpiceObject.stringHexToBytes(RSA_public_encrypt(this.token, myBody.pub_key));
			return key;
		} else {
			return wdi.SpiceObject.stringToBytesPadding('', 128);
		}
	},

	getRedLinkMessBytes: function() {
		var header = new wdi.SpiceLinkHeader({magic:1363428690, major_version:2, minor_version:2, size:22}).marshall();
		var body = new wdi.SpiceLinkMess({
			connection_id:this.connectionId, 
			channel_type:this.channel, 
			caps_offset:18,
			num_common_caps: 1,
			common_caps: (1 << wdi.SpiceVars.SPICE_COMMON_CAP_MINI_HEADER)
		}).marshall();
		return header.concat(body);
	},

	getErrorCodeBytes: function (data) {
		var errorQ = wdi.GlobalPool.create('ViewQueue');
		errorQ.setData(data);
		var errorCode = wdi.SpiceObject.bytesToInt32NoAllocate(errorQ);
		wdi.GlobalPool.discard('ViewQueue', errorQ);
		if (errorCode === 0) {
			if (this.channel === wdi.SpiceVars.SPICE_CHANNEL_DISPLAY) {
				var redDisplayInit = new wdi.SpiceDataHeader({type: wdi.SpiceVars.SPICE_MSGC_DISPLAY_INIT, size: 14}).marshall();
				//TODO: ultrahardcoded value here, move to configuration

				//DUE To high level storage the memory specified for cache
				//is 2-3 times bigger than expected.
				var cache_size = 0*1024*1024;

				var body = new wdi.SpiceCDisplayInit({
					pixmap_cache_id:1,
					pixmap_cache_size: cache_size,
					glz_dictionary_id: 0,
					glz_dictionary_window_size: 1
				}).marshall();

				return redDisplayInit.concat(body);
			} else if(this.channel == wdi.SpiceVars.SPICE_CHANNEL_MAIN) {
				return new wdi.SpiceDataHeader({type: wdi.SpiceVars.SPICE_MSGC_MAIN_ATTACH_CHANNELS, size: 0}).marshall();
			}
		} else {
			throw new wdi.Exception({message: "Server refused client", errorCode: 2});
		}
	}
});
