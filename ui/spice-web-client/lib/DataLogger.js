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

wdi.DataLogger = {
	testStartTime: 0,
	testStopTime: 0,
	networkStart:0,
	networkTotalTime: 0,
    data: {},
	routeList: {},
	imageTypes: {},
	startTimes: [],
	init: function() {
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_SURFACE_CREATE] = 'drawCanvas';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_SURFACE_DESTROY] = 'removeCanvas';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_COPY] = 'drawImage';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_FILL] = 'drawFill';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_ALPHA_BLEND] = 'drawAlphaBlend';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_WHITENESS] = 'drawWhiteness';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_BLACKNESS] = 'drawBlackness';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_TRANSPARENT] = 'drawTransparent';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_COPY_BITS] = 'drawCopyBits';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_TEXT] = 'drawText';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_STROKE] = 'drawStroke';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_ROP3] = 'drawRop3';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_INVERS] = 'drawInvers';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_CREATE] = 'handleStreamCreate';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_DESTROY] = 'handleStreamDestroy';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_DATA] = 'handleStreamData';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_CLIP] = 'handleStreamClip';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_BLEND] = 'drawBlend';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_INVAL_LIST] = 'invalList';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_INVAL_ALL_PALETTES] = 'invalPalettes';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_MARK] = 'displayMark';
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_RESET] = 'displayReset';

		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_BITMAP] = 'bitmap';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_QUIC] = 'quic';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_RESERVED] = 'reserved';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_PNG] = 'png';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_PLT] = 'lz_plt';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_RGB] = 'lz_rgb';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_GLZ_RGB] = 'glz_rgb';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_FROM_CACHE] = 'cache';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_SURFACE] = 'surface';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_JPEG] = 'jpeg';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_FROM_CACHE_LOSSLESS] = 'cache_lossless';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_ZLIB_GLZ_RGB] = 'zlib_glz_rgb';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_JPEG_ALPHA] = 'jpeg_alpha';
		this.imageTypes[wdi.SpiceImageType.SPICE_IMAGE_TYPE_CANVAS] = 'canvas';
	},

	setStartTime: function (time) {
		this.startTimes.push(time);
	},

	getSpiceMessageType: function (spiceMessage, prepend, append) {
		var type = this.routeList[spiceMessage.messageType];

		if (type === 'drawImage') {
			type += '_' + this.imageTypes[spiceMessage.args.image.imageDescriptor.type];
		}

		return (prepend || '') + type + (append || '');
	},

	setNetworkTimeStart: function (time) {
		this.networkStart = this.networkStart || time || Date.now();
	},

	logNetworkTime: function () {
		if (this.networkStart) {
			this.networkTotalTime += Date.now() - this.networkStart;
			this.networkStart = 0;
		}
	},

	startTestSession: function () {
		this.clear();
		wdi.logOperations = true;
		this.testStartTime = Date.now();
	},

	stopTestSession: function () {
		this.testStopTime = Date.now();
		wdi.logOperations = false;
	},

	log: function(spiceMessage, start, customType, useTimeQueue, prepend, append) {
		var end = Date.now();
		var type;
		if(customType) {
			type = customType;
		} else {
			type = this.getSpiceMessageType(spiceMessage, prepend, append);
		}

        if(!this.data.hasOwnProperty(type)) {
            this.data[type] = [];
        }

		if (useTimeQueue) {
			start = this.startTimes.shift();
		}

        this.data[type].push({start: start, end: end});
    },

    clear: function() {
		this.data = {};
		this.testStartTime = 0;
		this.testStopTime = 0;
		this.networkTotalTime = 0;
		this.networkStart = 0;
    },

    getData: function() {
        return this.data;
    },

	getStats: function() {
		var networkTime = this.networkTotalTime;
		var numOperations = 0;
		var totalTimeSpent = networkTime;
		var totalTime = this.testStopTime - this.testStartTime;

		var dataSource = this.data;
		var partialTimes = {};
		var result = "";
		var data;

		for(var i in this.data) {
			if(this.data.hasOwnProperty(i)) {
				data = dataSource[i];
				numOperations += data.length;
				partialTimes[i] = 0;
				for(var x = 0;x< data.length;x++) {
					partialTimes[i] += data[x].end - data[x].start;
				}
				totalTimeSpent += partialTimes[i];
			}
		}

		result += "Total operations by number:\n";

		var partial = 0;
		for(var i in dataSource) {
			if(dataSource.hasOwnProperty(i)) {
				partial = (dataSource[i].length / numOperations) * 100;
				result += i+': '+(~~partial)+"% (" + dataSource[i].length + ")\n";
			}
		}

		result += "Total numOperations: " + numOperations + "\n";
		result += "---------------------------------\n";
		result += "\n";

		result += "Total Operations by time:\n";

		for(i in partialTimes) {
			if(partialTimes.hasOwnProperty(i)) {
				partial = (partialTimes[i] / totalTime) * 100;
				result += i+': '+(~~partial)+"% ("+partialTimes[i]+"ms)\n";
			}
		}

		var idleTime = totalTime - totalTimeSpent;
		partial = (idleTime / totalTime) * 100;
		result += "Idle: "+(~~partial)+"% ("+idleTime+"ms)\n";
		partial = (networkTime / totalTime) * 100;
		result += "Network: " + (~~partial) + "% (" + networkTime + "ms)\n";

		result += 'Total time: ' + totalTime + 'ms \n';

		return "BEGIN OF PERFORMANCE STATS\n" + result + "\nEND OF PERFORMANCE STATS\n";
	}
};

wdi.DataLogger.init();
