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

Application = $.spcExtend(wdi.DomainObject, {
    spiceConnection: null,
    clientGui: null,
    agent: null,
    externalCallback: null,
    keyboardEnabled: true,
    packetProcess: null,
    inputProcess: null,
    multimediaTime: null,
    lastMultimediaTime: null,
    busConnection: null,
    busProcess: null,
	timeLapseDetector: null,

    init: function (c) {
        wdi.GlobalPool.init();
        this.spiceConnection = c.spiceConnection || new wdi.SpiceConnection();
        this.clientGui = c.clientGui || new wdi.ClientGui();
        this.agent = c.agent || new wdi.Agent({
			app: this
		});

        this.inputProcess = c.inputProcess || new wdi.InputProcess({
			clientGui: this.clientGui,
			spiceConnection: this.spiceConnection
		});
        this.packetProcess = c.packetProcess;
        this.busConnection = c.busConnection || new wdi.BusConnection();
        this.busProcess = c.busProcess || new wdi.BusProcess({
			clientGui: this.clientGui,
			busConnection: this.busConnection
		});
		this.timeLapseDetector = c.timeLapseDetector || new wdi.TimeLapseDetector();
        this.setup();
    },

    run: function (c) {
	    if(c.hasOwnProperty('seamlessDesktopIntegration')) {
		    wdi.SeamlessIntegration = c['seamlessDesktopIntegration'];
	    }

		if (!this.packetProcess) {
			var displayProcess = false;

			if (c.useWorkers === false) {
				displayProcess = new wdi.DisplayProcess({
					clientGui: this.clientGui
				});
			}

			this.packetProcess = new wdi.PacketProcess({
				app: this,
				clientGui: this.clientGui,
				agent: this.agent,
				spiceConnection: this.spiceConnection,
	            inputsProcess: this.inputProcess,
	            displayProcess: displayProcess
	        })
		}
        if (window.vdiLoadTest) {
            this.spiceConnection.addListener('message', this.onMessage, this);
        } else {
            this.spiceConnection.addListener('message', this.packetProcess.process, this.packetProcess);
        }


        this.busConnection.connect(c);
		this.timeLapseDetector.startTimer();

        if (c['canvasMargin']) {
            this.clientGui.setCanvasMargin(c['canvasMargin']);
        }

        if (c['disableClipboard']) {
            this.agent.disableClipboard();
            this.clientGui.disableClipboard();
            this.enableCtrlV();
        }

        if(c['layer']) {
            this.clientGui.setLayer(c['layer']);
        }

        if (this.clientGui.checkFeatures()) {
            if (wdi.SeamlessIntegration) {
                this.disableKeyboard();//keyboard should start disabled is integrated
            }
            wdi.Keymap.loadKeyMap(c['layout']);
            this.setExternalCallback(c['callback'], c['context']);

            try {
                this.connect({
					host: c['host'],
					port: c['port'],
					protocol: c['protocol'],
					vmHost: c['vmHost'],
					vmPort: c['vmPort'],
                    vmInfoToken: c['vmInfoToken'],
					busHost: c['busHost'],
					token: c['token'],
					connectionControl: c['connectionControl'],
                    heartbeatToken: c['heartbeatToken'],
					heartbeatTimeout: c['heartbeatTimeout']
				});
            } catch (e) {
                this.executeExternalCallback('error', 1);
            }

            this.clientGui.setClientOffset(c['clientOffset']['x'], c['clientOffset']['y']);
        }
		if (c.hasOwnProperty('externalClipboardHandling')) {
			this.externalClipoardHandling = c['externalClipboardHandling'];
		}
    },

    end: function () {
        //TODO: end?
    },

    setup: function () {
        this.spiceConnection.addListener('mouseMode', this.onMouseMode, this);
        this.spiceConnection.addListener('initAgent', this.onInitAgent, this);
        this.spiceConnection.addListener('error', this.onDisconnect, this);
		this.spiceConnection.addListener('channelConnected', this.onChannelConnected, this);
        this.clientGui.addListener('input', this.onClientInput, this);
        this.clientGui.addListener('resolution', this.onResolution, this);
        this.clientGui.addListener('paste', this.onPaste, this);
        this.clientGui.addListener('startAudio', this.onStartAudio, this);
        this.busProcess.addListener('windowCreated', this.onWindowCreated, this);
        this.busProcess.addListener('windowClosed', this.onWindowClosed, this);
        this.busProcess.addListener('windowMoved', this.onWindowMoved, this);
        this.busProcess.addListener('windowResized', this.onWindowResized, this);
        this.busProcess.addListener('windowFocused', this.onWindowFocused, this);
        this.busProcess.addListener('windowMinimized', this.onWindowMinimized, this);
        this.busProcess.addListener('windowRestored', this.onWindowRestored, this);
        this.busProcess.addListener('windowMaximized', this.onWindowMaximized, this);
        this.busProcess.addListener('busConnected', this.onBusConnected, this);
	    this.busProcess.addListener('menuResponse', this.onMenuResponse, this);
		this.busProcess.addListener('networkDriveResponse', this.onNetworkDriveResponse, this);
		this.busProcess.addListener('wrongPathError', this.onWrongPathError, this);
		this.busProcess.addListener('applicationLaunchedSuccessfully', this.onApplicationLaunchedSuccessfully, this);
		this.agent.addListener('clipBoardData', this.onClipBoardData, this);
        this.busConnection.addListener('busMessage', this.onBusMessage, this);
        this.busConnection.addListener('error', this.onDisconnect, this);
		this.timeLapseDetector.addListener('timeLapseDetected', this.onTimeLapseDetected, this);
    },

	onChannelConnected: function(params) {
		var channel = params;
		if (channel === wdi.SpiceVars.SPICE_CHANNEL_INPUTS) {
			this.clientGui.releaseAllKeys();
		}
	},

	onNetworkDriveResponse: function(params) {
		this.executeExternalCallback('networkDriveResponse', params);
	},

    onDisconnect: function (params) {
		var error = params;
        this.executeExternalCallback('error', error);
    },

    onResolution: function (params) {
        this.executeExternalCallback('resolution', params);
    },

    onClipBoardData: function (params) {
		if (this.externalClipoardHandling) {
			this.executeExternalCallback('clipboardEvent', params);
		} else {
			this.clientGui.setClipBoardData(params);
		}
    },

    onWindowMinimized: function (params) {
        var window = params;
        var params = this.clientGui.resizeSubCanvas(window);
        this.executeExternalCallback('windowMinimized', params);
    },

    onWindowFocused: function (params) {
        this.executeExternalCallback('windowFocused', params);
    },

    onWindowRestored: function (params) {
        var window = params;
        var params = this.clientGui.resizeSubCanvas(window);
        this.executeExternalCallback('windowRestored', params);
    },

    onWindowMaximized: function (params) {
        var window = params;
        var params = this.clientGui.resizeSubCanvas(window);
        this.executeExternalCallback('windowMaximized', params);
    },

    onWindowResized: function (params) {
        var window = params;
        var params = this.clientGui.resizeSubCanvas(window);
        this.executeExternalCallback('windowResized', params);
    },

    onWindowMoved: function (params) {
        var window = params;
        var params = this.clientGui.moveSubCanvas(window);
        this.executeExternalCallback('windowMoved', params);
    },

    onWindowClosed: function (params) {
        var window = params;
        var params = this.clientGui.deleteSubCanvas(window);
        this.executeExternalCallback('windowClosed', params);
    },

    onWindowCreated: function (params) {
        var window = params;
        var params = this.clientGui.createNewSubCanvas(window);
        this.executeExternalCallback('windowCreated', params);
    },

	onMenuResponse: function(params) {
		var menuData = params;
		this.executeExternalCallback('menuResponse', menuData);
	},

    //Events
    onClientInput: function (params) {
        var data = params;
		var type = data[0];
		this.inputProcess.send(data, type);
	},

    onMessage: function (params) {
        var message = params;
        this.packetProcess.process(message);

        var self = this;

        window.checkResultsTimer && clearTimeout(window.checkResultsTimer);
        window.checkResultsTimer = window.setTimeout(function () {
            self.executeExternalCallback('checkResults');
            window.vdiLoadTest = false;
        }, 5000);

    },

    onBusConnected: function(params) {
        if (wdi.SeamlessIntegration) {
            this.busProcess.requestWindowList(); //request windows list
        }
    },

    onBusMessage: function (params) {
        var message = params;
        this.busProcess.process(message);
    },

    onInitAgent: function (params) {
        this.agent.setClientTokens(params);
        this.agent.sendInitMessage(this);
        this.executeExternalCallback('ready', params);
//		this.clientGui.releaseAllKeys();
	},

    onMouseMode: function (params) {
        this.clientGui.setMouseMode(params);
    },

    onPaste: function (params) {
        this.agent.setClipboard(params);
    },

    onStartAudio: function () {
        this.packetProcess.processors[wdi.SpiceVars.SPICE_CHANNEL_PLAYBACK].startAudio();
    },

	onTimeLapseDetected: function (params) {
		var elapsedMillis = params;
		this.executeExternalCallback('timeLapseDetected', elapsedMillis);
	},

    connect: function (connectionInfo) {
        try {
            this.spiceConnection.connect(connectionInfo);
        } catch (e) {
            this.clientGui.showError(e.message);
        }
    },

    setExternalCallback: function (fn, context) {
        this.externalCallback = [fn, context];
    },

    executeExternalCallback: function (action, params) {
        this.externalCallback[0].call(this.externalCallback[1], action, params);
    },

    sendCommand: function (action, params) {
        switch (action) {
            case "close":
                this.busProcess.closeWindow(params['hwnd']);
                break;
            case "move":
                this.busProcess.moveWindow(params['hwnd'], params['x'], params['y']);
                break;
            case "minimize":
                this.busProcess.minimizeWindow(params['hwnd']);
                break;
            case "maximize":
                this.busProcess.maximizeWindow(params['hwnd']);
                break;
            case "restore":
                this.busProcess.restoreWindow(params['hwnd']);
                break;
            case "focus":
                this.busProcess.focusWindow(params['hwnd']);
                break;
            case "resize":
                this.busProcess.resizeWindow(params['hwnd'], params['width'], params['height']);
                break;
            case "run":
                this.busProcess.executeCommand(params['cmd']);
                break;
            case "setResolution":
                this.agent.setResolution(params['width'], params['height']);
                break;
			case 'getMenu':
				this.busProcess.getMenu();
				break;
			case 'reMountNetworkDrive':
				this.busProcess.reMountNetworkDrive(params['host'], params['username'], params['password']);
				break;
		}
    },

    enableKeyboard: function () {
    	this.clientGui.enableKeyboard();
    },

    disableKeyboard: function () {
		this.clientGui.disableKeyboard();
    },

    enableCtrlV: function () {
        wdi.KeymapES.setCtrlKey(86, 0x2F);
        wdi.KeymapUS.setCtrlKey(86, 0x2F);
    },

	disconnect: function() {
		this.busConnection.disconnect();
		this.spiceConnection.disconnect();
	},

    setMultimediaTime: function (time) {
        this.multimediaTime = time;
        this.lastMultimediaTime = Date.now();
    },

    sendShortcut: function(shortcut) {
        if(shortcut == wdi.keyShortcutsHandled.CTRLV) {
            this.inputProcess.send([
                "keydown",
                [
                    {
                        'generated': true,
                        'type': "keydown",
                        'keyCode': 17,
                        'charCode': 0
                    }
                ]

            ], "keydown"); //ctrl down

            this.inputProcess.send([
                "keydown",
                [
                    {
                        'generated': true,
                        'type': "keydown",
                        'keyCode': 86,
                        'charCode': 0
                    }
                ]

            ], "keydown"); //v

            this.inputProcess.send([
                "keyup",
                [
                    {
                        'generated': true,
                        'type': "keyup",
                        'keyCode': 86,
                        'charCode': 0
                    }
                ]

            ], "keyup"); //v up

            this.inputProcess.send([
                "keyup",
                [
                    {
                        'generated': true,
                        'type': "keyup",
                        'keyCode': 17,
                        'charCode': 0
                    }
                ]

            ], "keyup"); //ctrl up
        }
    },

	dispose: function () {
		this.disableKeyboard();
		this.disconnect();
		this.packetProcess.dispose();
	},

    onWrongPathError: function (params) {
        this.executeExternalCallback('wrongPathError', params);
    },

    onApplicationLaunchedSuccessfully: function (params) {
        this.executeExternalCallback('applicationLaunchedSuccessfully', params);
    },

    getKeyboardHandler: function() {
        return this.clientGui.handleKey;
    },

    getClientGui: function() {
        return this.clientGui;
    },

    setCurrentWindow: function(wnd) {
        this.clientGui.inputManager.setCurrentWindow(wnd);
    }
});

window['Application'] = Application;
Application.prototype['run'] = Application.prototype.run;
Application.prototype['sendCommand'] = Application.prototype.sendCommand;
Application.prototype['enableKeyboard'] = Application.prototype.enableKeyboard;
Application.prototype['disableKeyboard'] = Application.prototype.disableKeyboard;
Application.prototype['dispose'] = Application.prototype.dispose;
Application.prototype['getKeyboardHandler'] = Application.prototype.getKeyboardHandler;
Application.prototype['getClientGui'] = Application.prototype.getClientGui;
Application.prototype['setCurrentWindow'] = Application.prototype.setCurrentWindow;
