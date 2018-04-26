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


wdi.TimeLapseDetector = $.spcExtend(wdi.EventObject.prototype, {
	lastTime: null,

	init: function timeLapseDetector_Init (c) {
		this.superInit();
	},

	startTimer: function timeLapseDetector_startTimer () {
		var self = this;
		this.lastTime = Date.now();

		window.setInterval(
			function timeLapseDetectorInterval () {
				var now = Date.now();
				// this.constructor == access to the class itself, so you
				// can access to static properties without writing/knowing
				// the class name
				var elapsed = now - self.lastTime;
				if (elapsed >= self.constructor.maxIntervalAllowed) {
					self.fire('timeLapseDetected', elapsed);
				}
				self.lastTime = now;
			},
			wdi.TimeLapseDetector.defaultInterval
		);
	},

	getLastTime: function timeLapseDetector_getLastTime () {
		return this.lastTime;
	},

	setLastTime: function timeLapseDetector_setLastTime (lastTime) {
		this.lastTime = lastTime;
		return this;
	}
});

wdi.TimeLapseDetector.defaultInterval = 5000;
wdi.TimeLapseDetector.maxIntervalAllowed = wdi.TimeLapseDetector.defaultInterval * 3;
