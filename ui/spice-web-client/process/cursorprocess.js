wdi.CursorProcess = $.spcExtend(wdi.EventObject.prototype, {
	imageData: null,
	
	process: function(spiceMessage) {
		switch (spiceMessage.messageType) {
			case wdi.SpiceVars.SPICE_MSG_CURSOR_INIT:
			case wdi.SpiceVars.SPICE_MSG_CURSOR_SET:
				var wdiCursor = this.extractCursor(spiceMessage);
				if(wdiCursor) {
					wdi.VirtualMouse.setHotspot(0, 0);
					wdi.VirtualMouse.setMouse(wdiCursor.data, wdiCursor.header.hot_spot_x, wdiCursor.header.hot_spot_y);
				}
				break;
		}
	},

	_toUrl:function(data) {
		var imageData = $('<canvas/>').attr({
			'width': data.width,
			'height': data.height
		})[0];
		var ctx = imageData.getContext('2d');
		ctx.putImageData(data, 0, 0);
		return imageData.toDataURL("image/png");
	},
	
	extractCursor: function(spiceMessage) {
		var flags = spiceMessage.args.cursor.flags;
		var position = spiceMessage.args.position;
		var visible = spiceMessage.args.visible;
		
		//if there is no cursor, return null
		if(flags & 1) {
			return null;
		}
	
		var imageData = null;
		
		//cursor from cache?
		if(flags & wdi.SpiceCursorFlags.SPICE_CURSOR_FLAGS_FROM_CACHE) {
			imageData = wdi.ImageCache.getCursorFrom(spiceMessage.args.cursor);			
		} else {
			//cursor from packet
			//any case should return url
			switch (spiceMessage.args.cursor.header.type) {

				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_ALPHA:
					imageData = this._toUrl(wdi.graphics.argbToImageData(spiceMessage.args.cursor.data, spiceMessage.args.cursor.header.width, spiceMessage.args.cursor.header.height));
					break;
				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_MONO:
					imageData = this._toUrl(wdi.graphics.monoToImageData(spiceMessage.args.cursor.data, spiceMessage.args.cursor.header.width, spiceMessage.args.cursor.header.height));
					break;
				case 8:
					imageData = wdi.SpiceObject.bytesToString(spiceMessage.args.cursor.data);
					break;
				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_COLOR4:
				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_COLOR8:
				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_COLOR16:
				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_COLOR24:
				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_COLOR32:
				case wdi.SpiceCursorType.SPICE_CURSOR_TYPE_ENUM_END:
					break;
			}	
		}
	
		//got no cursor? error!
		if(!imageData) {
			return null;
		}
	
		//we have cursor, cache it?
		if(flags & wdi.SpiceCursorFlags.SPICE_CURSOR_FLAGS_CACHE_ME) {
			wdi.ImageCache.addCursor(spiceMessage.args.cursor, imageData);
		}
		
		return {
			data: imageData, 
			position: position, 
			visible: visible,
			header: spiceMessage.args.cursor.header
		};
	}
});
