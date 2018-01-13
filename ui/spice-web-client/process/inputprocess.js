wdi.InputProcess = $.spcExtend(wdi.EventObject.prototype, {
	clientGui: null,
	spiceConnection: null,
	
	init: function(c) {
		this.superInit();
		this.clientGui = c.clientGui;
		this.spiceConnection = c.spiceConnection;
	},
	
	process: function(spiceMessage) {
		switch (spiceMessage.messageType) {
			case wdi.SpiceVars.SPICE_MSG_INPUTS_MOUSE_MOTION_ACK:
				this.clientGui.motion_ack();
				break;
		}
	},
	
	send: function(data, type) {
		var packet, scanCodes, i;
		if(type == 'mousemove') {
			packet = new wdi.SpiceMessage({
				messageType: wdi.SpiceVars.SPICE_MSGC_INPUTS_MOUSE_POSITION, 
				channel: wdi.SpiceVars.SPICE_CHANNEL_INPUTS, 
				args: new wdi.RedcMousePosition({
					x:data[1][0]+wdi.VirtualMouse.hotspot.x,
					y:data[1][1]+wdi.VirtualMouse.hotspot.y,
					buttons_state:data[1][2],
					display_id:0
				})
			});
			this.spiceConnection.send(packet);
		} else if(type == 'mousedown') {
			packet = new wdi.SpiceMessage({
				messageType: wdi.SpiceVars.SPICE_MSGC_INPUTS_MOUSE_PRESS, 
				channel: wdi.SpiceVars.SPICE_CHANNEL_INPUTS, 
				args: new wdi.RedcMousePress({
					button_id:data[1]+1,
					buttons_state:1<<data[1]
				})
			});
			this.spiceConnection.send(packet);			
		} else if(type == 'mouseup') {
			packet = new wdi.SpiceMessage({
				messageType: wdi.SpiceVars.SPICE_MSGC_INPUTS_MOUSE_RELEASE, 
				channel: wdi.SpiceVars.SPICE_CHANNEL_INPUTS, 
				args: new wdi.RedcMousePress({
					button_id:data[1]+1,
					buttons_state:0
				})
			});
			this.spiceConnection.send(packet);				
		} else if (type == 'keydown' || type == 'keypress') {
			scanCodes = wdi.Keymap.getScanCodes(data[1][0]);
			for (i= 0; i<scanCodes.length;i++) {
				packet = new wdi.SpiceMessage({
					messageType: wdi.SpiceVars.SPICE_MSGC_INPUTS_KEY_DOWN,
					channel: wdi.SpiceVars.SPICE_CHANNEL_INPUTS,
					args: new wdi.SpiceScanCode(scanCodes[i])
				});
				this.spiceConnection.send(packet);
			}
		} else if (type == 'keyup') {
			scanCodes = wdi.Keymap.getScanCodes(data[1][0]);
			for (i= 0; i<scanCodes.length;i++) {
				packet = new wdi.SpiceMessage({
					messageType: wdi.SpiceVars.SPICE_MSGC_INPUTS_KEY_UP,
					channel: wdi.SpiceVars.SPICE_CHANNEL_INPUTS,
					args: new wdi.SpiceScanCode(scanCodes[i])
				});
				this.spiceConnection.send(packet);
			}
		} else if(type == 'joystick') {
			packet = new wdi.SpiceMessage({
				messageType: wdi.SpiceVars.SPICE_MSGC_INPUTS_MOUSE_MOTION, 
				channel: wdi.SpiceVars.SPICE_CHANNEL_INPUTS, 
				args: new wdi.RedcMouseMotion({
					x:data[1][0],
					y:data[1][1],
					buttons_state:0
				})
			});
			this.spiceConnection.send(packet);
		}
	}
});
