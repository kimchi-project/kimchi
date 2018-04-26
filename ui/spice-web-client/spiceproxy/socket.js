var net = require('net');

wdi.socketStatus = {
	'idle':0,
	'prepared':1,
	'connected':2,
	'disconnected':3,
	'failed':4
};

//Works only with arrays of bytes (this means each value is a number in 0 to 255)
wdi.Socket = $.spcExtend(wdi.EventObject.prototype, {
	netSocket: null,
	status: wdi.socketStatus.idle,
	binary: false,

	connect: function (uri) {
		var self = this;

		var uriParts = uri.split(':');
		var port = uriParts.pop();
		var host = uriParts.pop();

		this.netSocket = new net.Socket();
		this.netSocket.connect(port, host);

		this.status = wdi.socketStatus.prepared;

		this.netSocket.on('spiceMessage', function (data) {
			self.fire('message', new Uint8Array(data));
		});
	},

	send: function (message) {
		this.netSocket.write(message);
	},
	
	disconnect: function () {
		this.netSocket.removeAllListeners();
		this.netSocket.end();
	},
	
	setStatus: function (status) {
		this.status = status;
	},
	
	getStatus: function () {
		return this.status;
	},

	getSocket: function () {
		return this.netSocket;
	}
	
});
