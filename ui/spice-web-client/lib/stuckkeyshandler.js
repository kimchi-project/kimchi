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

wdi.StuckKeysHandler = $.spcExtend(wdi.EventObject.prototype, {
	ctrlTimeoutId: null,
	altTimeoutId: null,
	shiftTimeoutId: null,
	shiftKeyPressed: false,
	ctrlKeyPressed: false,
	altKeyPressed: false,

	handleStuckKeys: function (jqueryEvent) {
		if (jqueryEvent) {
			switch (jqueryEvent.keyCode) {
				case 16:
					this._handleKey('shiftTimeoutId', jqueryEvent.type, 16);
					break;
				case 17:
					this._handleKey('ctrlTimeoutId', jqueryEvent.type, 17);
					break;
				case 18:
					this._handleKey('altTimeoutId', jqueryEvent.type, 18);
					break;
			}
		}
	},

	releaseAllKeys: function releaseAllKeys () {
		var e;
		var i;
		for (i = 0; i < 300; i++) {
			this.releaseKeyPressed(i);
		}
	},

	_handleKey: function (variable, type, keyCode) {
		if (type === 'keydown') {
			this[variable] = this._configureTimeout(keyCode);
		} else if (type === 'keyup') {
			clearTimeout(this[variable]);
		}
	},

	_configureTimeout: function (keyCode) {
		var self = this;
		return setTimeout(function keyPressedTimeout () {
			// added the 'window' for the jQuery call for testing.
			self.releaseKeyPressed(keyCode);
		}, wdi.StuckKeysHandler.defaultTimeout);
	},

	releaseKeyPressed: function (keyCode) {
		var e = window.jQuery.Event("keyup");
		e["which"] = keyCode;
		e["keyCode"] = keyCode;
		e["charCode"] = 0;
		e["generated"] = true;
		this.fire('inputStuck', ['keyup', [e]]);
	},

	checkSpecialKey: function (event, keyCode) {
		switch (keyCode) {
			case 16:
				this.shiftKeyPressed = event === 'keydown';
				break;
			case 17:
				this.ctrlKeyPressed = event === 'keydown';
				break;
			case 18:
				this.altKeyPressed = event === 'keydown';
				break;
		}
	},

	releaseSpecialKeysPressed: function () {
		if (this.shiftKeyPressed) {
			this.releaseKeyPressed(16);
			this.shiftKeyPressed = false;
		}
		if (this.ctrlKeyPressed) {
			this.releaseKeyPressed(17);
			this.ctrlKeyPressed = false;
		}
		if (this.altKeyPressed) {
			this.releaseKeyPressed(18);
			this.altKeyPressed = false;
		}
	}


});

wdi.StuckKeysHandler.defaultTimeout = 2000;
