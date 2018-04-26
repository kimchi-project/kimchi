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

wdi.DisplayRouter = $.spcExtend(wdi.EventObject.prototype, {

	init: function(c) {
		this.clientGui = c.clientGui;
		this.rasterEngine = c.rasterEngine || new wdi.RasterEngine({clientGui: this.clientGui});
		if(c.routeList) {
			this.routeList = c.routeList;
		} else {
			this._initRoutes();
		}

	},

	_initRoutes: function() {
		this.routeList = {};
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_SURFACE_CREATE] = this.rasterEngine.drawCanvas;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_SURFACE_DESTROY] = this.rasterEngine.removeCanvas;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_COPY] = this.rasterEngine.drawImage;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_FILL] = this.rasterEngine.drawFill;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_ALPHA_BLEND] = this.rasterEngine.drawAlphaBlend;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_WHITENESS] = this.rasterEngine.drawWhiteness;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_BLACKNESS] = this.rasterEngine.drawBlackness;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_TRANSPARENT] = this.rasterEngine.drawTransparent;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_COPY_BITS] = this.rasterEngine.drawCopyBits;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_TEXT] = this.rasterEngine.drawText;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_STROKE] = this.rasterEngine.drawStroke;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_ROP3] = this.rasterEngine.drawRop3;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_INVERS] = this.rasterEngine.drawInvers;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_CREATE] = this.rasterEngine.handleStreamCreate;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_DESTROY] = this.rasterEngine.handleStreamDestroy;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_DATA] = this.rasterEngine.handleStreamData;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_STREAM_CLIP] = this.rasterEngine.handleStreamClip;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_DRAW_BLEND] = this.rasterEngine.drawBlend;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_INVAL_LIST] = this.rasterEngine.invalList;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_INVAL_ALL_PALETTES] = this.rasterEngine.invalPalettes;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_MARK] = false;
		this.routeList[wdi.SpiceVars.SPICE_MSG_DISPLAY_RESET] = false;
	},

	processPacket: function(spiceMessage) {
		//filter out empty messages
		if(!spiceMessage) {
			wdi.Debug.log('DisplayProcess processPacket: Skipping empty message...');
			return;
		}

		var route = this.routeList[spiceMessage.messageType];
		if (route) {
			route.call(this.rasterEngine, spiceMessage);
		}
	}
});
