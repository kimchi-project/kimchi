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

wdi.ImageUncompressor = $.spcExtend(wdi.EventObject.prototype, {
	init: function (c) {
		this.syncAsyncHandler = c.syncAsyncHandler || new wdi.SyncAsyncHandler({
			isAsync: c.isAsync
		});
	},

	lzHeaderSize: 32,

	extractLzHeader: function (imageData, brush) {
		var headerData, header;
		if (!brush) { //brushes are still js arrays
			if (Object.prototype.toString.call(imageData) === "[object Array]") {
				headerData = imageData.slice(0, this.lzHeaderSize);
				imageData = imageData.slice(this.lzHeaderSize); //skip the header
			} else {
				headerData = imageData.subarray(0, this.lzHeaderSize).toJSArray();
				imageData = imageData.subarray(this.lzHeaderSize); //skip the header
			}
			header = wdi.LZSS.demarshall_rgb(headerData);
		} else {
			header = wdi.LZSS.demarshall_rgb(imageData);
		}

		return {
			header: header,
			imageData: imageData
		};
	},

	processLz: function (imageData, brush, opaque, clientGui, callback, scope) {
		var extractedData, u8, buffer, number, context;

		extractedData = this.extractLzHeader(imageData, brush);
		imageData = extractedData.imageData;
		number = extractedData.header.width * extractedData.header.height * 4;

		buffer = new ArrayBuffer(imageData.length + 16);
		u8 = new Uint8Array(buffer);

		u8[0] = 1; //LZ_RGB
		u8[1] = opaque;
		u8[2] = extractedData.header.type;
		u8[3] = extractedData.header.top_down; //padding

		for (var i = 0; i < 4; i++) { //iterations because of javascript number size
			u8[4 + i] = number & (255); //Get only the last byte
			number = number >> 8; //Remove the last byte
		}

		var view = new DataView(buffer);
		view.setUint32(8, extractedData.header.width);
		view.setUint32(12, extractedData.header.height);

		u8.set(imageData, 16);

		this.syncAsyncHandler.dispatch(buffer, callback, scope);
	},

	processQuic: function (imageData, opaque, clientGui, callback, scope) {
		wdi.Debug.log('Quic decode');
		buffer = new ArrayBuffer(imageData.length + 4);
		view = new Uint8Array(buffer);

		view.set(imageData, 4);
		view[3] = opaque ? 1 : 0;
		view[0] = 0; //quic

		this.syncAsyncHandler.dispatch(buffer, callback, scope);
	},

	process: function (imageDescriptor, imageData, brush, opaque, clientGui, callback, scope) {
		switch(imageDescriptor.type) {
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_QUIC:
				this.processQuic(imageData, opaque, clientGui, callback, scope);
				break;
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_RGB:
				this.processLz(imageData, brush, opaque, clientGui, callback, scope);
				break;
		}
	},

	dispose: function () {
		this.syncAsyncHandler.dispose();
	}
});

var syncInstance;
var asyncInstance;

wdi.ImageUncompressor.getSyncInstance = function () {
	if (!syncInstance) {
		syncInstance = new wdi.ImageUncompressor({
			isAsync: false
		});
	}

	return syncInstance;
};

wdi.ImageUncompressor.getAsyncInstance = function () {
	if (!asyncInstance) {
		asyncInstance = new wdi.ImageUncompressor({
			isAsync: true
		});
	}

	return asyncInstance;
};
