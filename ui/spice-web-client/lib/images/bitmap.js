wdi.BMP2 = $.spcExtend(wdi.SpiceObject, {
	objectSize: 0,
	mapper: [0, 1, 1, 4, 4, 8, 16, 24, 32, 32],

	init: function(imageData) {
		var type = this.bytesToInt8(imageData);
		var flags = this.bytesToInt8(imageData); // bit 1 => normal, bit 2 => palette cache (...)
		var width = this.bytesToInt32(imageData); // width in pixels
		var height = this.bytesToInt32(imageData); // height in pixels
		var stride = this.bytesToInt32(imageData); // width in bytes including padding
		var len;
		var bpp = this.mapper[type];
		var i;


		var paletteSize = 0, unique, paletteData, numEnts = 0;
		if (bpp <= 8 && bpp > 0) {
			var palette = [];
			if (flags & 1) {
				var paletteOffset = this.bytesToInt32(imageData); // From the begininig of the spice packet?
				len = imageData.length;
				paletteSize = 4*Math.pow(2,bpp);
				var paletteDataSize = paletteSize + 8 + 2; //palette + unique(64b) + numEnts (16b)
				len -= paletteDataSize;
				paletteData = imageData.splice(len, paletteDataSize);
				unique = this.bytesToInt64(paletteData);
				numEnts = this.bytesToInt16(paletteData);
				var queue;

				for (i = 0; i < numEnts*4; i+=4) {
					queue = new wdi.Queue();
					queue.setData(paletteData.slice(i, i+4));
					palette.push(new wdi.SpiceColor().demarshall(queue));
				}
				wdi.ImageCache.addPalette(unique, palette);
			} else {
				//get palette from cache
				unique = this.bytesToInt64(imageData);
				len = imageData.length;
				palette = wdi.ImageCache.getPalette(unique);
				var spiceColors;
				paletteData = [];
				numEnts = palette.length;
				for (i =0; i < numEnts; i++ ) {
					spiceColors = palette[i].marshall();
					spiceColors.push(0);
					paletteData = paletteData.concat(spiceColors);
				}

			}
			// imageData = paletteData.concat(imageData);

		} else {
			// Removing 4 bytes from the image data to fix index out of range error.
			var unknown = this.bytesToInt32(imageData);
		}

		this.setContent({
			imageSize: len,
			width: width,
			height: height,
			bpp: bpp,
			imageData: imageData,
			paletteSize: numEnts * 4,
			palette: palette,
			stride: stride,
			type: type
		});
	},
	
	setContent: function(c) {
		this.imageSize = c.imageSize;
		this.width = c.width;
		this.height = c.height;
		this.bpp = c.bpp;
		this.imageData = c.imageData;
		this.palette = c.palette;
		this.offset = c.paletteSize + 0x36; //0x36 === Current harcoded header size (BMP + DIB)
		this.size = this.offset + this.imageSize;
		this.stride = c.stride;
		this.type = c.type;
	},
	
	marshall: function(context) {
		var type = this.type;
		var palette = this.palette;
        var width = this.width;
        var height = this.height;
		var stride = this.stride;
		var data = this.imageData;
		var size = data.length;

		var pixelsStride = stride * 8/this.bpp;
		var bytesStride = pixelsStride * 4;
		var buf = new ArrayBuffer(bytesStride * height);
		var buf8 = new Uint8ClampedArray(buf);
		var buf32 = new Uint32Array(buf);
		var topdown = false;

		var oct, i, pos, buffPos, spiceColor;
		var b;
		if (palette) {
			buffPos = 0
			if (type === wdi.SpiceBitmapFmt.SPICE_BITMAP_FMT_1BIT_BE) {
				spiceColor = palette[1];
				var foreColor = spiceColor.r << 24 | spiceColor.g << 16 | spiceColor.b << 8 | 255;

				spiceColor = palette[0];
				var backColor = spiceColor.r << 24 | spiceColor.g << 16 | spiceColor.b << 8 | 255;

				var PLT1_MASK = [1, 2, 4, 8, 16, 32, 64, 128];

				for (pos = 0; pos < size; pos++) {
					oct = data[pos];

					for (i = 7; i >= 0; i--) {
						if (oct & PLT1_MASK[i]) {
							buf32[buffPos++] = foreColor;
						} else {
							buf32[buffPos++] = backColor;
						}
					}
				}
			} else if (type === wdi.SpiceBitmapFmt.SPICE_BITMAP_FMT_4BIT_BE) {
				for (pos = 0; pos < size; pos++) {
					oct = data[pos];
					spiceColor = palette[oct >>> 4];
					buf32[buffPos++] = spiceColor.r << 24 | spiceColor.g << 16 | spiceColor.b << 8 | 255;
					spiceColor = palette[oct & 0x0f];
					buf32[buffPos++] = spiceColor.r << 24 | spiceColor.g << 16 | spiceColor.b << 8 | 255;
				}
			}

		} else {
			if (type === wdi.SpiceBitmapFmt.SPICE_BITMAP_FMT_32BIT) {
				for (pos = 0; pos < size; pos += 4) {
					b = data[pos];
					data[pos] = data[pos + 2];
					data[pos + 2] = b;
					data[pos + 3] = 255;
				}

			} else if (type === wdi.SpiceBitmapFmt.SPICE_BITMAP_FMT_RGBA) {
				topdown = true;
				for (pos = 0; pos < size; pos+=4) {
					b = data[pos];
					data[pos] = data[pos+2];
					data[pos+2] = b;
				}
			} else if (type === wdi.SpiceBitmapFmt.SPICE_BITMAP_FMT_24BIT) {
				for (pos = 0; pos < size; pos+=3) {
					b = data[pos];
					data[pos] = data[pos+2];
					data[pos+2] = b;
				}
			}
			buf8 = new Uint8ClampedArray(data);
		}

		var ret = new ImageData(buf8, pixelsStride, height);

		var tmpCanvas = wdi.graphics.getNewTmpCanvas(width, height);
		tmpCanvas.getContext('2d').putImageData(ret, 0, 0, 0, 0, width, height);
		ret = tmpCanvas;

		if(!topdown) {
			ret = wdi.RasterOperation.flip(ret);
		}

		return ret;

	}
});
