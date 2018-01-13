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


if (typeof CanvasPixelArray != 'undefined' && !CanvasPixelArray.prototype.set) {
	CanvasPixelArray.prototype.set = function(u8) {
		var length = u8.length;
		for (var i=0; i<length; i++) {
			this[i] = u8[i];
		}
	};
}

wdi.graphics = {
	tmpCanvas: document.createElement('canvas'),
	imageLoader: new Image(),

	getRect: function(box, image) {
		//if the subpart is the whole image, return image
		if (box.x === 0 && box.y === 0 && box.width === image.width && box.height === image.height) {
			return image;
		}

		var cnv = this.getImageFromData(image);
		//get a subpart of the image

		//first, create a canvas to hold the new image
		var tmp_canvas = wdi.graphics.getNewTmpCanvas(box.width, box.height);
		var tmp_context = tmp_canvas.getContext('2d');

		tmp_context.drawImage(cnv, box.x, box.y, box.width, box.height, 0, 0, box.width, box.height);
		return tmp_canvas;
	},

	//TODO: why this is not argb?
	argbToImageData: function(bytes, width, height) {
		var length = bytes.length;
		var canvas = wdi.graphics.getTmpCanvas(width, height);
		var context = canvas.getContext('2d');
		var imageData = context.createImageData(width, height);

		for (var i = 0; i < length; i += 4) {
			imageData.data[i] = bytes[i]; //r
			imageData.data[i + 1] = bytes[i + 1]; //g
			imageData.data[i + 2] = bytes[i + 2]; //b
			imageData.data[i + 3] = bytes[i + 3]; //a
		}

		return imageData;
	},

	align: function(a, size) {
		return (((a) + ((size) - 1)) & ~((size) - 1));
	},

	monoMask: [1, 2, 4, 8, 16, 32, 64, 128],

	monoToImageData: function(bytes, width, height) {
		var stride = this.align(width, 8) >>> 3;
		var length = bytes.length;
		var half = length / 2;

		var canvas = wdi.graphics.getTmpCanvas(width, height);
		var context = canvas.getContext('2d');

		var result = context.createImageData(width, height);

		var andMask = [];
		var xorMask = [];

		for (var i = 0; i < length; i++) {
			var currentByte = bytes[i];
			var bitsLeft = 8;

			if (i >= half) {
				while (bitsLeft--) {
					var bit = (currentByte & this.monoMask[bitsLeft]) && true;
					andMask.push(bit);
				}
			} else if (i < half) {
				while (bitsLeft--) {
					var bit = (currentByte & this.monoMask[bitsLeft]) && true;
					xorMask.push(bit);
				}
			}
		}

		var pos = 0;
		half = xorMask.length;

		for (i = 0; i < half; i++) {
			pos = i * 4;
			if (!andMask[i] && !xorMask[i]) {
				result.data[pos] = 0;
				result.data[pos + 1] = 0;
				result.data[pos + 2] = 0;
				result.data[pos + 3] = 255;
			} else if (!andMask[i] && xorMask[i]) {
				result.data[pos] = 255;
				result.data[pos + 1] = 255;
				result.data[pos + 2] = 255;
				result.data[pos + 3] = 0;
			} else if (andMask[i] && !xorMask[i]) {
				result.data[pos] = 255;
				result.data[pos + 1] = 255;
				result.data[pos + 2] = 255;
				result.data[pos + 3] = 255;
			} else if (andMask[i] && xorMask[i]) {
				result.data[pos] = 0;
				result.data[pos + 1] = 0;
				result.data[pos + 2] = 0;
				result.data[pos + 3] = 255;
			}
		}
		return result;
	},

	drawJpeg: function (imageDescriptor, jpegData, callback, previousScope) {
		return this.drawBrowserImage(imageDescriptor, jpegData, callback, previousScope, 'jpeg', false);
	},

    drawBrowserImage: function (imageDescriptor, jpegData, callback, previousScope, type, alreadyEncoded) {
        var tmpstr;
        var img = wdi.GlobalPool.create('Image');
		var url;
        img.onload = function() {
			URL.revokeObjectURL(url)
			try {
				if (imageDescriptor.flags & wdi.SpiceImageFlags.SPICE_IMAGE_FLAGS_CACHE_ME) {
					var myImage = wdi.graphics.getTmpCanvas(this.width, this.height);
					var tmp_context = myImage.getContext('2d');
					tmp_context.drawImage(this, 0, 0);
					wdi.ImageCache.addImage(imageDescriptor, myImage);
				}

                callback.call(previousScope, this);
            } catch (e) {
                wdi.Debug.error(e.message);
            } finally {
                wdi.ExecutionControl.currentProxy.end();
            }
        };

        img.onerror = function() {
			URL.revokeObjectURL(url)
            wdi.Debug.error('failed to load JPEG image');
            wdi.ExecutionControl.currentProxy.end();
        };

		if(!alreadyEncoded) {
			url = wdi.SpiceObject.bytesToURI(jpegData);
			img.src = url;
		} else {
			tmpstr = jpegData;
			img.src = tmpstr;
		}
    },

	getImageFromSpice: function (imageDescriptor, imageData, clientGui, callback, previousScope, options) {
		var myImage;
		var source_img = null;
		var opaque;
		var brush;
		var raw;

		if (options) {
			opaque = options['opaque'];
			brush = options['brush'];
			raw = options['raw'];
		} else {
			opaque = false;
			raw = false;
			brush = false;
		}




		switch (imageDescriptor.type) {
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_RGB:
				source_img = this.processLz(imageDescriptor, imageData, brush, opaque, clientGui);
				break;

			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_PLT:
				wdi.Debug.log('lz plt decode');
				source_img = wdi.LZSS.convert_spice_lz_to_web(clientGui.getContext(0), imageData, imageDescriptor, opaque);
				break;

			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_QUIC:
				source_img = this.processQuic(imageDescriptor, imageData, brush, opaque, clientGui);
				break;

            case wdi.SpiceImageType.SPICE_IMAGE_TYPE_JPEG:
				wdi.Debug.log('JPEG decode');
				wdi.ExecutionControl.sync = false;
                this.drawJpeg(imageDescriptor, imageData.subarray(4), callback, previousScope);
                return;

            case wdi.SpiceImageType.SPICE_IMAGE_TYPE_JPEG_ALPHA:
                wdi.Debug.log('JPEG Alpha decode');
                wdi.ExecutionControl.sync = false;
                var jpeg_data = imageData.subarray(9);
                this.drawJpeg(imageDescriptor, jpeg_data, callback, previousScope);

                // TODO: extract alpha mask and apply

                return;

            case wdi.SpiceImageType.SPICE_IMAGE_TYPE_BITMAP:
				wdi.Debug.log('BMP');

				if (imageData.toJSArray) {
					imageData = imageData.toJSArray();
				}

				//Spice BMP Headers
				source_img = new wdi.BMP2(imageData).marshall(clientGui.getContext(0));
				break;
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_FROM_CACHE_LOSSLESS:
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_FROM_CACHE:
                wdi.ExecutionControl.sync = false;
				wdi.ImageCache.getImageFrom(imageDescriptor, function(img) {
                    callback.call(previousScope, img);
                    wdi.ExecutionControl.currentProxy.end();
                });
				return;
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_SURFACE:
				var origin_surface_id = wdi.SpiceObject.bytesToInt32(imageData.toJSArray());
				var context = clientGui.getContext(origin_surface_id);
				source_img = context.canvas;
				break;
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_CANVAS:
				source_img = imageData;
				break;
			case wdi.SpiceImageType.SPICE_IMAGE_TYPE_PNG:
				wdi.ExecutionControl.sync = false;
				imageData = wdi.SpiceObject.bytesToString(imageData.toJSArray());
				this.drawBrowserImage(imageDescriptor, imageData, callback, previousScope, "png", true);
				return;
			default:
				wdi.Debug.log('Unknown image type: ' + imageDescriptor.type);
				wdi.ExecutionControl.currentProxy.end();
				return;
		}
		myImage = null;
		if (imageDescriptor.flags & wdi.SpiceImageFlags.SPICE_IMAGE_FLAGS_CACHE_ME) {
			wdi.ImageCache.addImage(imageDescriptor, source_img);
		}

		if(source_img.getContext || raw) {
			myImage = source_img;
		} else {
			myImage = this.getImageFromData(source_img);
		}

		if (imageDescriptor.flags & wdi.SpiceImageFlags.SPICE_IMAGE_FLAGS_CACHE_ME) {
			wdi.ImageCache.addImage(imageDescriptor, myImage);
		}

		if (wdi.ExecutionControl.sync) callback.call(previousScope, myImage);
	},

	processUncompress: function (imageDescriptor, imageData, brush, opaque, clientGui, callback) {
		var scope = this;
		var imageUncompressor = wdi.ImageUncompressor.getSyncInstance();

		imageUncompressor.process(
			imageDescriptor, imageData, brush, opaque, clientGui, callback, scope
		);
	},

	processQuic: function(imageDescriptor, imageData, brush, opaque, clientGui) {
		var source_img;

		var callback = function(data) {
			var u8 = new Uint8ClampedArray(data);
			source_img = new ImageData(u8, imageDescriptor.width, imageDescriptor.height);
		};

		this.processUncompress(imageDescriptor, imageData, brush, opaque, clientGui, callback);

		return source_img;
	},

	processLz: function(imageDescriptor, imageData, brush, opaque, clientGui) {
		var source_img;
		var self = this;
		function callback(data) {
			var imageUncompressor = wdi.ImageUncompressor.getSyncInstance();
			var extractedData = imageUncompressor.extractLzHeader(imageData, brush);

			var u8 = new Uint8ClampedArray(data);
			source_img = new ImageData(u8, imageDescriptor.width, imageDescriptor.height);

			if (!extractedData.header.top_down && !opaque) {
				source_img = this.imageFlip(source_img);
			}
		};


		this.processUncompress(imageDescriptor, imageData, brush, opaque, clientGui, callback);
		return source_img;
	},

	imageFlip: function (source_img) {
		return wdi.RasterOperation.flip(this.getImageFromData(source_img));
	},

	//given an imagedata it returns a canvas
	getImageFromData: function(data, notUsePool) {
		if(data.getContext || data instanceof Image) {
			return data;
		}
		var sourceCanvas;
		if (!notUsePool) {
			sourceCanvas = this.getNewTmpCanvas(data.width, data.height);
		} else {
			sourceCanvas = $('<canvas/>').attr({
				'width': data.width,
				'height': data.height
			})[0]; //this.getNewTmpCanvas(data.width, data.height);
		}

		var srcCtx = sourceCanvas.getContext('2d');
		srcCtx.putImageData(data, 0, 0);
		return sourceCanvas;
	},

	//given a canvas it returns a ImageData
	getDataFromImage: function(canvas) {
		return canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
	},


	getBoxFromSrcArea: function(src_area) {
		var box = {
			width: src_area.right - src_area.left,
			height: src_area.bottom - src_area.top,
			x: src_area.left,
			y: src_area.top
		};
		return box;
	},

	setBrush: function(clientGui, context, brush, box, ropd) {
		var pattern, imageDescriptor, type, imageData;
		if (brush.type === wdi.SpiceBrushType.SPICE_BRUSH_TYPE_PATTERN) {
			imageDescriptor = brush.pattern.image;
			this.getImageFromSpice(imageDescriptor, brush.pattern.imageData, clientGui, function(sourceImg) {
				pattern = context.createPattern(sourceImg, "repeat");


				if (ropd === wdi.SpiceRopd.SPICE_ROPD_OP_PUT) { //no rop, direct draw
					context.fillStyle = pattern;
					context.fillRect(box.x, box.y, box.width, box.height);
				} else {
					//Creating brushImg to raster
					var tmp_canvas = wdi.graphics.getTmpCanvas(box.width, box.height);
					var tmp_context = tmp_canvas.getContext('2d');
					tmp_context.fillStyle = pattern;
					tmp_context.fillRect(0, 0, box.width, box.height);
					var dest = wdi.graphics.getRect(box, context.canvas);
					imageData = wdi.RasterOperation.process(ropd, tmp_canvas, dest);
					//draw to screen, imageData is a canvas
					context.drawImage(imageData, box.x, box.y, box.width, box.height);
				}
			}, this, {
				'opaque': true
			});

		} else if (brush.type === wdi.SpiceBrushType.SPICE_BRUSH_TYPE_SOLID) {
			if (ropd === wdi.SpiceRopd.SPICE_ROPD_OP_PUT) { //no rop, direct draw
                if(context.fillStyle != brush.color.simple_html_color) {
                    context.fillStyle = brush.color.simple_html_color;
                }
				context.fillRect(box.x, box.y, box.width, box.height);

			} else { //if we need rop, we need intermediate canvas...
				//Creating brushImg to raster
				var tmp_canvas = wdi.graphics.getTmpCanvas(box.width, box.height);
				var tmp_context = tmp_canvas.getContext('2d');
				tmp_context.fillStyle = brush.color.html_color;
				tmp_context.fillRect(0, 0, box.width, box.height);
				var dest = wdi.graphics.getRect(box, context.canvas);
				imageData = wdi.RasterOperation.process(ropd, tmp_canvas, dest);

				//draw to screen, imageData is a canvas
				context.drawImage(imageData, box.x, box.y, box.width, box.height);
			}
		}
	},

    imageIsEntireColor: function(r,g,b, size, data) {
        var pos = 0;
        var equal;

        do {
            equal = data[pos] === r && data[pos+1] === g && data[pos+2] === b;
            pos+= 4;
        } while(pos != size && equal);

        return equal;
    },

	drawBackText: function(clientGui, context, text) {
		var back_brush = text.back_brush;
		var back_mode = text.back_mode;

		var box = wdi.graphics.getBoxFromSrcArea(text.base.box);

		this.setBrush(clientGui, context, back_brush, box, back_mode);
	},

	drawString: function(context, string, bpp, fore_brush, clip_type, display) {
		var color = fore_brush.color;
		var length = string.len;

		var render_pos, glyph_origin;
		var width;
		var height;
		var data;
		var lines;
		var imgData;
		var factor;
		var x;
		var y;
		var i;
		var buf, buf8, rawData;
		var bytesLeft;
		var bytesTotal;
		var subData;

		var rasterArray = string.raster_glyph;
		var currentRaster;

		var rawLine;
		var bitsLeft;
		var byteCounter;
		var alpha;
		var index;

		var box;


		if (bpp === 1) {
			factor = 255;
		} else if (bpp === 4) {
			factor = 17;
		} else {
			factor = 1;
		}

		for (i = 0; i < length; i++) {

			currentRaster = rasterArray[i];
			//Loop for each Glyph
			render_pos = currentRaster.render_pos;
			glyph_origin = currentRaster.glyph_origin;
			width = currentRaster.width;
			height = currentRaster.height;
			data = currentRaster.data;

			lines = height;

			buf = new ArrayBuffer(width * height * 4);
			buf8 = new Uint8ClampedArray(buf);
			rawData = new Uint32Array(buf);

			x = 0;
			y = 0;

			while (lines--) { //glyphline, not text line
				//Loop for each line
				bytesLeft = Math.ceil(width * bpp / 8);
				bytesTotal = bytesLeft;
				subData = [];

				while (bytesTotal--) {
					subData.push(data.pop());
				}

				while (bytesLeft--) {
					rawLine = subData.pop();
					bitsLeft = 8;
					byteCounter = 0;

					while (bitsLeft) {
						alpha = wdi.bppMask[bpp][byteCounter] & rawLine;
						if (bpp === 1 && alpha) {
							alpha = 1;
						} else if (bpp === 4 && alpha && alpha > 15) {
							alpha = alpha >> 4;
						}
						if (alpha) {
							index = (y * width + x);
							rawData[index] = factor * alpha << 24 | // alpha
							color.b << 16 | // blue
							color.g << 8 | // green
							color.r; // red
						}
						bitsLeft -= bpp;
						x++;
						byteCounter++;
					}
				}
				y++;
				x = 0;
			}

			box = {
				'x': render_pos.x + glyph_origin.x,
				'y': render_pos.y + glyph_origin.y - 1,
				'width': width,
				'height': height
			};

			imgData = new ImageData(buf8, width, height);
			var tmpCanvas = wdi.graphics.getImageFromData(imgData);
			display.drawClip(tmpCanvas, box, context);
			wdi.GlobalPool.discard('Canvas', tmpCanvas);

		}
	},

	getImgDataPosition: function(x, y, width) {
		var index = (y * width + x) * 4;
		return index;
	},

	//returns the shared canvas
	getTmpCanvas: function(width, height) {
		var canvas = this.tmpCanvas;
		canvas.width = width;
		canvas.height = height;
		return canvas;
	},

	//return always a new canvas
	getNewTmpCanvas: function(width, height) {
		//pool!
		var sourceCanvas = wdi.GlobalPool.create('Canvas');
		sourceCanvas.width = width;
		sourceCanvas.height = height;
		return sourceCanvas;
	}
}

wdi.Rop3 = {
	0x01: function(pat, src, dest) {
		return~ (pat | src | dest)
	},
	0x02: function(pat, src, dest) {
		return~ (pat | src) & dest
	},
	0x04: function(pat, src, dest) {
		return~ (pat | dest) & src
	},
	0x06: function(pat, src, dest) {
		return~ (~(src ^ dest) | pat)
	},
	0x07: function(pat, src, dest) {
		return~ ((src & dest) | pat)
	},
	0x08: function(pat, src, dest) {
		return~ pat & dest & src
	},
	0x09: function(pat, src, dest) {
		return~ ((src ^ dest) | pat)
	},
	0x0b: function(pat, src, dest) {
		return~ ((~dest & src) | pat)
	},
	0x0d: function(pat, src, dest) {
		return~ ((~src & dest) | pat)
	},
	0x0e: function(pat, src, dest) {
		return~ (~(src | dest) | pat)
	},
	0x10: function(pat, src, dest) {
		return~ (src | dest) & pat
	},
	0x12: function(pat, src, dest) {
		return~ (~(pat ^ dest) | src)
	},
	0x13: function(pat, src, dest) {
		return~ ((pat & dest) | src)
	},
	0x14: function(pat, src, dest) {
		return~ (~(pat ^ src) | dest)
	},
	0x15: function(pat, src, dest) {
		return~ ((pat & src) | dest)
	},
	0x16: function(pat, src, dest) {
		return (~(pat & src) & dest) ^ src ^ pat
	},
	0x17: function(pat, src, dest) {
		return~ (((src ^ dest) & (src ^ pat)) ^ src)
	},
	0x18: function(pat, src, dest) {
		return (src ^ pat) & (pat ^ dest)
	},
	0x19: function(pat, src, dest) {
		return~ ((~(pat & src) & dest) ^ src)
	},
	0x1a: function(pat, src, dest) {
		return ((pat & src) | dest) ^ pat
	},
	0x1b: function(pat, src, dest) {
		return~ (((pat ^ src) & dest) ^ src)
	},
	0x1c: function(pat, src, dest) {
		return ((pat & dest) | src) ^ pat
	},
	0x1d: function(pat, src, dest) {
		return~ (((pat ^ dest) & src) ^ dest)
	},
	0x1e: function(pat, src, dest) {
		return (dest | src) ^ pat
	},
	0x1f: function(pat, src, dest) {
		return~ ((src | dest) & pat)
	},
	0x20: function(pat, src, dest) {
		return~ src & pat & dest
	},
	0x21: function(pat, src, dest) {
		return~ ((pat ^ dest) | src)
	},
	0x23: function(pat, src, dest) {
		return~ ((~dest & pat) | src)
	},
	0x24: function(pat, src, dest) {
		return (src ^ pat) & (dest ^ src)
	},
	0x25: function(pat, src, dest) {
		return~ ((~(src & pat) & dest) ^ pat)
	},
	0x26: function(pat, src, dest) {
		return ((src & pat) | dest) ^ src
	},
	0x27: function(pat, src, dest) {
		return (~(src ^ pat) | dest) ^ src
	},
	0x28: function(pat, src, dest) {
		return (pat ^ src) & dest
	},
	0x29: function(pat, src, dest) {
		return~ (((src & pat) | dest) ^ src ^ pat)
	},
	0x2a: function(pat, src, dest) {
		return~ (src & pat) & dest
	},
	0x2b: function(pat, src, dest) {
		return~ (((pat ^ dest) & (src ^ pat)) ^ src)
	},
	0x2c: function(pat, src, dest) {
		return ((src | dest) & pat) ^ src
	},
	0x2d: function(pat, src, dest) {
		return (~dest | src) ^ pat
	},
	0x2e: function(pat, src, dest) {
		return ((pat ^ dest) | src) ^ pat
	},
	0x2f: function(pat, src, dest) {
		return~ ((~dest | src) & pat)
	},
	0x31: function(pat, src, dest) {
		return~ ((~pat & dest) | src)
	},
	0x32: function(pat, src, dest) {
		return (src | pat | dest) ^ src
	},
	0x34: function(pat, src, dest) {
		return ((src & dest) | pat) ^ src
	},
	0x35: function(pat, src, dest) {
		return (~(src ^ dest) | pat) ^ src
	},
	0x36: function(pat, src, dest) {
		return (pat | dest) ^ src
	},
	0x37: function(pat, src, dest) {
		return~ ((pat | dest) & src)
	},
	0x38: function(pat, src, dest) {
		return ((pat | dest) & src) ^ pat
	},
	0x39: function(pat, src, dest) {
		return (~dest | pat) ^ src
	},
	0x3a: function(pat, src, dest) {
		return ((src ^ dest) | pat) ^ src
	},
	0x3b: function(pat, src, dest) {
		return~ ((~dest | pat) & src)
	},
	0x3d: function(pat, src, dest) {
		return (~(src | dest) | pat) ^ src
	},
	0x3e: function(pat, src, dest) {
		return ((~src & dest) | pat) ^ src
	},
	0x40: function(pat, src, dest) {
		return~ dest & src & pat
	},
	0x41: function(pat, src, dest) {
		return~ ((src ^ pat) | dest)
	},
	0x42: function(pat, src, dest) {
		return (src ^ dest) & (pat ^ dest)
	},
	0x43: function(pat, src, dest) {
		return~ ((~(src & dest) & pat) ^ src)
	},
	0x45: function(pat, src, dest) {
		return~ ((~src & pat) | dest)
	},
	0x46: function(pat, src, dest) {
		return ((dest & pat) | src) ^ dest
	},
	0x47: function(pat, src, dest) {
		return~ (((pat ^ dest) & src) ^ pat)
	},
	0x48: function(pat, src, dest) {
		return (pat ^ dest) & src
	},
	0x49: function(pat, src, dest) {
		return~ (((dest & pat) | src) ^ dest ^ pat)
	},
	0x4a: function(pat, src, dest) {
		return ((dest | src) & pat) ^ dest
	},
	0x4b: function(pat, src, dest) {
		return (~src | dest) ^ pat
	},
	0x4c: function(pat, src, dest) {
		return~ (pat & dest) & src
	},
	0x4d: function(pat, src, dest) {
		return~ (((src ^ dest) | (src ^ pat)) ^ src)
	},
	0x4e: function(pat, src, dest) {
		return ((pat ^ src) | dest) ^ pat
	},
	0x4f: function(pat, src, dest) {
		return~ ((~src | dest) & pat)
	},
	0x51: function(pat, src, dest) {
		return~ ((~pat & src) | dest)
	},
	0x52: function(pat, src, dest) {
		return ((dest & src) | pat) ^ dest
	},
	0x53: function(pat, src, dest) {
		return~ (((src ^ dest) & pat) ^ src)
	},
	0x54: function(pat, src, dest) {
		return~ (~(src | pat) | dest)
	},
	0x56: function(pat, src, dest) {
		return (src | pat) ^ dest
	},
	0x57: function(pat, src, dest) {
		return~ ((src | pat) & dest)
	},
	0x58: function(pat, src, dest) {
		return ((pat | src) & dest) ^ pat
	},
	0x59: function(pat, src, dest) {
		return (~src | pat) ^ dest
	},
	0x5b: function(pat, src, dest) {
		return (~(dest | src) | pat) ^ dest
	},
	0x5c: function(pat, src, dest) {
		return ((dest ^ src) | pat) ^ dest
	},
	0x5d: function(pat, src, dest) {
		return~ ((~src | pat) & dest)
	},
	0x5e: function(pat, src, dest) {
		return ((~dest & src) | pat) ^ dest
	},
	0x60: function(pat, src, dest) {
		return (src ^ dest) & pat
	},
	0x61: function(pat, src, dest) {
		return~ (((src & dest) | pat) ^ src ^ dest)
	},
	0x62: function(pat, src, dest) {
		return ((dest | pat) & src) ^ dest
	},
	0x63: function(pat, src, dest) {
		return (~pat | dest) ^ src
	},
	0x64: function(pat, src, dest) {
		return ((src | pat) & dest) ^ src
	},
	0x65: function(pat, src, dest) {
		return (~pat | src) ^ dest
	},
	0x67: function(pat, src, dest) {
		return (~(src | pat) | dest) ^ src
	},
	0x68: function(pat, src, dest) {
		return~ ((~(src | dest) | pat) ^ src ^ dest)
	},
	0x69: function(pat, src, dest) {
		return~ (src ^ dest ^ pat)
	},
	0x6a: function(pat, src, dest) {
		return (src & pat) ^ dest
	},
	0x6b: function(pat, src, dest) {
		return~ (((src | pat) & dest) ^ src ^ pat)
	},
	0x6c: function(pat, src, dest) {
		return (pat & dest) ^ src
	},
	0x6d: function(pat, src, dest) {
		return~ (((dest | pat) & src) ^ dest ^ pat)
	},
	0x6e: function(pat, src, dest) {
		return ((~src | pat) & dest) ^ src
	},
	0x6f: function(pat, src, dest) {
		return~ (~(src ^ dest) & pat)
	},
	0x70: function(pat, src, dest) {
		return~ (src & dest) & pat
	},
	0x71: function(pat, src, dest) {
		return~ (((dest ^ pat) & (src ^ dest)) ^ src)
	},
	0x72: function(pat, src, dest) {
		return ((src ^ pat) | dest) ^ src
	},
	0x73: function(pat, src, dest) {
		return~ ((~pat | dest) & src)
	},
	0x74: function(pat, src, dest) {
		return ((dest ^ pat) | src) ^ dest
	},
	0x75: function(pat, src, dest) {
		return~ ((~pat | src) & dest)
	},
	0x76: function(pat, src, dest) {
		return ((~src & pat) | dest) ^ src
	},
	0x78: function(pat, src, dest) {
		return (src & dest) ^ pat
	},
	0x79: function(pat, src, dest) {
		return~ (((src | dest) & pat) ^ src ^ dest)
	},
	0x7a: function(pat, src, dest) {
		return ((~dest | src) & pat) ^ dest
	},
	0x7b: function(pat, src, dest) {
		return~ (~(pat ^ dest) & src)
	},
	0x7c: function(pat, src, dest) {
		return ((~src | dest) & pat) ^ src
	},
	0x7d: function(pat, src, dest) {
		return~ (~(src ^ pat) & dest)
	},
	0x7e: function(pat, src, dest) {
		return (src ^ dest) | (pat ^ src)
	},
	0x7f: function(pat, src, dest) {
		return~ (src & pat & dest)
	},
	0x80: function(pat, src, dest) {
		return src & pat & dest
	},
	0x81: function(pat, src, dest) {
		return~ ((src ^ dest) | (pat ^ src))
	},
	0x82: function(pat, src, dest) {
		return~ (src ^ pat) & dest
	},
	0x83: function(pat, src, dest) {
		return~ (((~src | dest) & pat) ^ src)
	},
	0x84: function(pat, src, dest) {
		return~ (pat ^ dest) & src
	},
	0x85: function(pat, src, dest) {
		return~ (((~pat | src) & dest) ^ pat)
	},
	0x86: function(pat, src, dest) {
		return ((src | dest) & pat) ^ src ^ dest
	},
	0x87: function(pat, src, dest) {
		return~ ((src & dest) ^ pat)
	},
	0x89: function(pat, src, dest) {
		return~ (((~src & pat) | dest) ^ src)
	},
	0x8a: function(pat, src, dest) {
		return (~pat | src) & dest
	},
	0x8b: function(pat, src, dest) {
		return~ (((dest ^ pat) | src) ^ dest)
	},
	0x8c: function(pat, src, dest) {
		return (~pat | dest) & src
	},
	0x8d: function(pat, src, dest) {
		return~ (((src ^ pat) | dest) ^ src)
	},
	0x8e: function(pat, src, dest) {
		return ((dest ^ pat) & (dest ^ src)) ^ src
	},
	0x8f: function(pat, src, dest) {
		return~ (~(src & dest) & pat)
	},
	0x90: function(pat, src, dest) {
		return~ (src ^ dest) & pat
	},
	0x91: function(pat, src, dest) {
		return~ (((~src | pat) & dest) ^ src)
	},
	0x92: function(pat, src, dest) {
		return ((pat | dest) & src) ^ pat ^ dest
	},
	0x93: function(pat, src, dest) {
		return~ ((dest & pat) ^ src)
	},
	0x94: function(pat, src, dest) {
		return ((src | pat) & dest) ^ src ^ pat
	},
	0x95: function(pat, src, dest) {
		return~ ((src & pat) ^ dest)
	},
	0x96: function(pat, src, dest) {
		return src ^ pat ^ dest
	},
	0x97: function(pat, src, dest) {
		return (~(src | pat) | dest) ^ src ^ pat
	},
	0x98: function(pat, src, dest) {
		return~ ((~(src | pat) | dest) ^ src)
	},
	0x9a: function(pat, src, dest) {
		return (~src & pat) ^ dest
	},
	0x9b: function(pat, src, dest) {
		return~ (((src | pat) & dest) ^ src)
	},
	0x9c: function(pat, src, dest) {
		return (~dest & pat) ^ src
	},
	0x9d: function(pat, src, dest) {
		return~ (((dest | pat) & src) ^ dest)
	},
	0x9e: function(pat, src, dest) {
		return ((src & dest) | pat) ^ src ^ dest
	},
	0x9f: function(pat, src, dest) {
		return~ ((src ^ dest) & pat)
	},
	0xa1: function(pat, src, dest) {
		return~ (((~pat & src) | dest) ^ pat)
	},
	0xa2: function(pat, src, dest) {
		return (~src | pat) & dest
	},
	0xa3: function(pat, src, dest) {
		return~ (((dest ^ src) | pat) ^ dest)
	},
	0xa4: function(pat, src, dest) {
		return~ ((~(pat | src) | dest) ^ pat)
	},
	0xa6: function(pat, src, dest) {
		return (~pat & src) ^ dest
	},
	0xa7: function(pat, src, dest) {
		return~ (((pat | src) & dest) ^ pat)
	},
	0xa8: function(pat, src, dest) {
		return (src | pat) & dest
	},
	0xa9: function(pat, src, dest) {
		return~ ((src | pat) ^ dest)
	},
	0xab: function(pat, src, dest) {
		return~ (src | pat) | dest
	},
	0xac: function(pat, src, dest) {
		return ((src ^ dest) & pat) ^ src
	},
	0xad: function(pat, src, dest) {
		return~ (((dest & src) | pat) ^ dest)
	},
	0xae: function(pat, src, dest) {
		return (~pat & src) | dest
	},
	0xb0: function(pat, src, dest) {
		return (~src | dest) & pat
	},
	0xb1: function(pat, src, dest) {
		return~ (((pat ^ src) | dest) ^ pat)
	},
	0xb2: function(pat, src, dest) {
		return ((src ^ dest) | (pat ^ src)) ^ src
	},
	0xb3: function(pat, src, dest) {
		return~ (~(pat & dest) & src)
	},
	0xb4: function(pat, src, dest) {
		return (~dest & src) ^ pat
	},
	0xb5: function(pat, src, dest) {
		return~ (((dest | src) & pat) ^ dest)
	},
	0xb6: function(pat, src, dest) {
		return ((pat & dest) | src) ^ pat ^ dest
	},
	0xb7: function(pat, src, dest) {
		return~ ((pat ^ dest) & src)
	},
	0xb8: function(pat, src, dest) {
		return ((dest ^ pat) & src) ^ pat
	},
	0xb9: function(pat, src, dest) {
		return~ (((dest & pat) | src) ^ dest)
	},
	0xba: function(pat, src, dest) {
		return (~src & pat) | dest
	},
	0xbc: function(pat, src, dest) {
		return (~(src & dest) & pat) ^ src
	},
	0xbd: function(pat, src, dest) {
		return~ ((dest ^ pat) & (dest ^ src))
	},
	0xbe: function(pat, src, dest) {
		return (src ^ pat) | dest
	},
	0xbf: function(pat, src, dest) {
		return~ (src & pat) | dest
	},
	0xc1: function(pat, src, dest) {
		return~ (((~src & dest) | pat) ^ src)
	},
	0xc2: function(pat, src, dest) {
		return~ ((~(src | dest) | pat) ^ src)
	},
	0xc4: function(pat, src, dest) {
		return (~dest | pat) & src
	},
	0xc5: function(pat, src, dest) {
		return~ (((src ^ dest) | pat) ^ src)
	},
	0xc6: function(pat, src, dest) {
		return (~pat & dest) ^ src
	},
	0xc7: function(pat, src, dest) {
		return~ (((pat | dest) & src) ^ pat)
	},
	0xc8: function(pat, src, dest) {
		return (pat | dest) & src
	},
	0xc9: function(pat, src, dest) {
		return~ ((dest | pat) ^ src)
	},
	0xca: function(pat, src, dest) {
		return ((dest ^ src) & pat) ^ dest
	},
	0xcb: function(pat, src, dest) {
		return~ (((src & dest) | pat) ^ src)
	},
	0xcd: function(pat, src, dest) {
		return~ (pat | dest) | src
	},
	0xce: function(pat, src, dest) {
		return (~pat & dest) | src
	},
	0xd0: function(pat, src, dest) {
		return (~dest | src) & pat
	},
	0xd1: function(pat, src, dest) {
		return~ (((pat ^ dest) | src) ^ pat)
	},
	0xd2: function(pat, src, dest) {
		return (~src & dest) ^ pat
	},
	0xd3: function(pat, src, dest) {
		return~ (((src | dest) & pat) ^ src)
	},
	0xd4: function(pat, src, dest) {
		return ((dest ^ pat) & (pat ^ src)) ^ src
	},
	0xd5: function(pat, src, dest) {
		return~ (~(src & pat) & dest)
	},
	0xd6: function(pat, src, dest) {
		return ((src & pat) | dest) ^ src ^ pat
	},
	0xd7: function(pat, src, dest) {
		return~ ((src ^ pat) & dest)
	},
	0xd8: function(pat, src, dest) {
		return ((pat ^ src) & dest) ^ pat
	},
	0xd9: function(pat, src, dest) {
		return~ (((src & pat) | dest) ^ src)
	},
	0xda: function(pat, src, dest) {
		return (~(dest & src) & pat) ^ dest
	},
	0xdb: function(pat, src, dest) {
		return~ ((src ^ dest) & (pat ^ src))
	},
	0xdc: function(pat, src, dest) {
		return (~dest & pat) | src
	},
	0xde: function(pat, src, dest) {
		return (pat ^ dest) | src
	},
	0xdf: function(pat, src, dest) {
		return~ (pat & dest) | src
	},
	0xe0: function(pat, src, dest) {
		return (src | dest) & pat
	},
	0xe1: function(pat, src, dest) {
		return~ ((src | dest) ^ pat)
	},
	0xe2: function(pat, src, dest) {
		return ((dest ^ pat) & src) ^ dest
	},
	0xe3: function(pat, src, dest) {
		return~ (((pat & dest) | src) ^ pat)
	},
	0xe4: function(pat, src, dest) {
		return ((src ^ pat) & dest) ^ src
	},
	0xe5: function(pat, src, dest) {
		return~ (((pat & src) | dest) ^ pat)
	},
	0xe6: function(pat, src, dest) {
		return (~(src & pat) & dest) ^ src
	},
	0xe7: function(pat, src, dest) {
		return~ ((dest ^ pat) & (pat ^ src))
	},
	0xe8: function(pat, src, dest) {
		return ((src ^ dest) & (pat ^ src)) ^ src
	},
	0xe9: function(pat, src, dest) {
		return~ ((~(src & dest) & pat) ^ src ^ dest)
	},
	0xea: function(pat, src, dest) {
		return (src & pat) | dest
	},
	0xeb: function(pat, src, dest) {
		return~ (src ^ pat) | dest
	},
	0xec: function(pat, src, dest) {
		return (pat & dest) | src
	},
	0xed: function(pat, src, dest) {
		return~ (pat ^ dest) | src
	},
	0xef: function(pat, src, dest) {
		return~ pat | dest | src
	},
	0xf1: function(pat, src, dest) {
		return~ (src | dest) | pat
	},
	0xf2: function(pat, src, dest) {
		return (~src & dest) | pat
	},
	0xf4: function(pat, src, dest) {
		return (~dest & src) | pat
	},
	0xf6: function(pat, src, dest) {
		return (src ^ dest) | pat
	},
	0xf7: function(pat, src, dest) {
		return~ (src & dest) | pat
	},
	0xf8: function(pat, src, dest) {
		return (src & dest) | pat
	},
	0xf9: function(pat, src, dest) {
		return~ (src ^ dest) | pat
	},
	0xfb: function(pat, src, dest) {
		return~ src | pat | dest
	},
	0xfd: function(pat, src, dest) {
		return~ dest | src | pat
	},
	0xfe: function(pat, src, dest) {
		return src | pat | dest
	}
};
