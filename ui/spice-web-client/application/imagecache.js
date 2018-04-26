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

wdi.ImageCache = {
	images: {},
	cursor: {},
	palettes: {},

	getImageFrom: function(descriptor, cb) {
	//see http://jsperf.com/todataurl-vs-getimagedata-to-base64/7
		var cnv = wdi.GlobalPool.create('Canvas');
		var imgData = this.images[descriptor.id.toString()];
		cnv.width = imgData.width;
		cnv.height = imgData.height;
		cnv.getContext('2d').putImageData(imgData,0,0);
		cb(cnv);
	},

	isImageInCache: function(descriptor) {
		if(descriptor.id.toString() in this.images) {
			return true;
		}
		return false;
	},

	delImage: function(id) {
		delete this.images[id.toString()];
	},

	addImage: function(descriptor, canvas) {
		if(canvas.getContext) {
			this.images[descriptor.id.toString()] = canvas.getContext('2d').getImageData(0,0,canvas.width, canvas.height);
		} else {
			this.images[descriptor.id.toString()] = canvas;
		}

	},

	getCursorFrom: function(cursor) {
		return this.cursor[cursor.header.unique.toString()];
	},

	addCursor: function(cursor, imageData) {
		this.cursor[cursor.header.unique.toString()] = imageData;
	},

	getPalette: function(id) {
		return this.palettes[id.toString()];
	},

	addPalette: function(id, palette) {
		this.palettes[id.toString()] = palette;
	},

	clearPalettes: function() {
		this.palettes = {};
	}
};
