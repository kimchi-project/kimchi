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

wdi.VirtualMouse = {
	eventLayers: [],
	mouseData:null,
	visible: null,
	lastLayer: null,
	hotspot: {
		x: 0,
		y: 0
	},
	lastMousePosition: {
		x: 0,
		y: 0,
		width: 0,
		height: 0
	},

	setHotspot: function(x, y) {
		this.hotspot.x = x;
		this.hotspot.y = y;
	},

	setEventLayer: function(ev, x, y, width, height, position) {
		this.eventLayers.push({
			layer: ev,
			left: x,
			top: y,
			right: x+width,
			bottom: y+height,
			position: position
		});
	},

	removeEventLayer: function(ev) {
		var len = this.eventLayers.length;
		for(var i=0;i<len;i++) {
			if(this.eventLayers[i].layer.id === ev.id) {
				this.eventLayers[ev.id] = undefined;
			}
		}
	},

	getEventLayer: function(x, y) {
		var len = this.eventLayers.length;
		var layer = null;
		for(var i=0;i<len;i++) {
			layer = this.eventLayers[i];
			if(x >= layer.left && x <= layer.right && y >= layer.top && y <= layer.bottom) {
				return layer.layer;
			}
		}
	},

	setMouse: function(mouseData, x, y) {
        //if(!Modernizr.touch) {
            var layer = null;
            var len = this.eventLayers.length;
            for(var i=0;i<len;i++) {
                layer = this.eventLayers[i];
                layer.layer.style.cursor = 'url('+mouseData+') ' + x + ' ' + y + ', default';
            }
        //}
	}
}
