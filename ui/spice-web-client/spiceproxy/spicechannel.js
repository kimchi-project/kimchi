wdi.SpiceChannel = $.spcExtend(wdi.EventObject.prototype, {
	socketQ: null,
	packetReassembler: null,

	init: function (c) {
		this.superInit();
		var socketQ = c.socketQ  || new wdi.SocketQueue();
		this.socketQ = socketQ;
		this.packetReassembler = c.packetReassembler || wdi.ReassemblerFactory.getPacketReassembler(socketQ);
		this.setListeners();
	},

	setListeners: function () {
		this.packetReassembler.addListener('packetComplete', function (e) {
			this.send(e);
		}, this);
	},

	connect: function (uri) {
		this.socketQ.connect(uri);
		this.packetReassembler.start();
	},

	send: function (data) {
		this.fire('send', data);
	}
});
