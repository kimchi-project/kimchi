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

wdi.InputManager = $.spcExtend(wdi.EventObject.prototype, {

	checkFocus: false,
	input: null,
	window: null,
	stuckKeysHandler: null,

	init: function (c) {
		this.superInit();
		this.input = c.input;
		this.window = c.window;
		this.stuckKeysHandler = c.stuckKeysHandler;
		this.$ = c.jQuery || $;
		if (!c.disableInput) {
			this.inputElement = this.$('<div style="position:absolute"><input type="text" id="inputmanager" style="opacity:0;color:transparent"/></div>');
		}
		this.currentWindow = null;
	},

	setCurrentWindow: function(wnd) {
		wnd = this.$(wnd);
		if(this.currentWindow) {
			this.inputElement.remove();
			//remove listeners
			this.currentWindow.unbind('blur');
		}
		this.$(wnd[0].document.body).prepend(this.inputElement);
		this.input = this.$(wnd[0].document.getElementById('inputmanager'));
		//TODO: remove events from the other window
		this.addListeners(wnd);
		this.currentWindow = wnd;
	},

	addListeners: function (wnd) {
		this._onBlur(wnd);
		this._onInput();
	},

	_onBlur: function (wnd) {
		var self = this;
		wnd.on('blur', function onBlur (e) {
			if (self.checkFocus) {
				self.input.focus();
			}
			self.stuckKeysHandler.releaseSpecialKeysPressed();
		});
	},

	_onInput: function () {
		var self = this;
		this.input.on('input', function input (e) {
			// ctrl-v issue related
			var aux = self.input.val();
			if (aux.length > 1) {
				self.reset();
			}
		});
	},

	enable: function () {
		this.checkFocus = true;
		this.input.select();
	},

	disable: function () {
		this.checkFocus = false;
		this.input.blur();
	},

	reset: function () {
		this.input.val("");
	},

	getValue: function () {
		var val = this.input.val();
		if (val) {
			this.reset();
		}
		return val;
	},

	manageChar: function (val, params) {
		var res = [Object.create(params[0])];
		res[0]['type'] = 'inputmanager';
		res[0]['charCode'] = val.charCodeAt(0);
		return res;
	}

});
