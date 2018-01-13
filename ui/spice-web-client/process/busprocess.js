wdi.BUS_TYPES = {
	file: 0,  // obsolete
	print: 1, // obsolete
	launchApplication: 2,
	windowManagement: 3,
	menu: 5,
	networkDriveManagement: 6,


	// Messages used during developing (for benchmarks and whatever).
	// you should not use them in code for production purposes.
	killApplicationDoNotUseInProductionEver: 34423423
};

wdi.BusProcess = $.spcExtend(wdi.EventObject.prototype, {
	busConnection: null,
	clientGui: null,

	init: function(c) {
		this.superInit();
		this.clientGui = c.clientGui;
		this.busConnection = c.busConnection;
	},

	process: function(message) {
		switch(message['verb']) {
			case "CONNECTED":
				this.busConnection.setSubscriptions();
				this.fire('busConnected');
				break;
			case "MESSAGE":
				this.parseMessage(message['body']);
				break;
			case "ERROR":
				console.error("Bus error");
				break;
			default:
				wdi.Debug.warn("Not implemented Stomp Verb: " + message['verb']);
		}
	},

	parseMessage: function(body) {
		switch(parseInt(body['type'])) {
			case wdi.BUS_TYPES.launchApplication:
				this.parseLaunchApplicationMessage(body);
				break;
			case wdi.BUS_TYPES.killApplicationDoNotUseInProductionEver:
				// this is a message we send to the other side of the bus
				// so do nothing.
				break;
			case wdi.BUS_TYPES.windowManagement:
				this.parseWindowManagementMessage(body);
				break;
			case wdi.BUS_TYPES.menu:
				this.handleMenuMessage(body);
				break;
			case wdi.BUS_TYPES.networkDriveManagement:
				this._handleNetworkDriveMessage(body);
				break;
			default:
				wdi.Debug.info("Bus type '" + body['type'] + "' not implemented.");
		}
	},

	_handleNetworkDriveMessage : function(message) {
		if(message.event != 'reMountNetworkDrive') {
			this.fire('networkDriveResponse', message);
		}
	},

	getMenu: function() {
		this.busConnection.send(
			{
				"type": wdi.BUS_TYPES.menu,
				"value": false,
				"event": 'request'
			}
		)
	},

	handleMenuMessage: function(message) {
		if(message.event == 'response') {
			this.fire('menuResponse', message);
		}
	},

	parseWindowManagementMessage: function(message) {
		switch (message['event']) {
			case 'windowList':
			case 'windowCreated':
			case 'windowClosed':
			case 'windowMoved':
			case 'windowResized':
			case 'windowFocused':
			case 'windowMinimized':
			case 'windowRestored':
			case 'windowMaximized':
				this.fire(message['event'], message['value']);
				break;
			default:
				wdi.Debug.info("Event '" + message['event'] + "' not implemented.")
		}
	},

	closeWindow: function(hwnd) {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'closeWindow',
					"hwnd": hwnd
				}
			)
		);
	},

	moveWindow: function(hwnd, x, y) {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'moveWindow',
					"hwnd": hwnd,
					"left": x,
					"top": y
				}
			)
		);
	},

	minimizeWindow: function(hwnd) {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'minimizeWindow',
					"hwnd": hwnd
				}
			)
		);
	},

	maximizeWindow: function(hwnd) {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'maximizeWindow',
					"hwnd": hwnd
				}
			)
		);
	},

	restoreWindow: function(hwnd) {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'restoreWindow',
					"hwnd": hwnd
				}
			)
		);
	},

	focusWindow: function(hwnd) {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'focusWindow',
					"hwnd": hwnd
				}
			)
		);
	},

	resizeWindow: function(hwnd, width, height) {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'resizeWindow',
					"hwnd": hwnd,
					"width": width,
					"height": height
				}
			)
		);
	},

	requestWindowList: function() {
		this.busConnection.send(
			this._constructWindowManagementMessage(
				{
					"event": 'getWindowList'
				}
			)
		)
	},

	executeCommand: function(cmd) {
		this.busConnection.send(
			{
				"type": wdi.BUS_TYPES.launchApplication,
				"application": cmd
			}
		)

	},

	_constructWindowManagementMessage: function(obj) {
		if (obj['event'] === undefined) {
			throw new Error("You should pass an 'event' attribute in the object");
		}
		var ret = {
			'type': wdi.BUS_TYPES.windowManagement,
			'event': obj['event'],
			'value': {}
		};
		for (var i in obj) {
			if (i != 'event' && obj.hasOwnProperty(i)) {
				ret['value'][i] = obj[i];
			}
		}
		return ret;
	},

	reMountNetworkDrive: function(host, username, password) {
		this.busConnection.send(
			{
				"type": wdi.BUS_TYPES.networkDriveManagement,
				"event": "reMountNetworkDrive",
				"host": host,
				"username": username,
				"password": password
			}
		)
	},

	parseLaunchApplicationMessage: function (message) {
		switch (message['event']) {
			case 'applicationLauncherWrongAppPathError':
				this.fire('wrongPathError', message);
				break;
			case 'applicationLaunchedSuccessfully':
				this.fire('applicationLaunchedSuccessfully', message);
				break;
			default:
				wdi.Debug.info("Event '" + message['event'] + "' not implemented.")
		}
	}
});
