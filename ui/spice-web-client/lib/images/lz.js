wdi.LZSS = {
	LZ_IMAGE_TYPE_INVALID: 0,
	LZ_IMAGE_TYPE_PLT1_LE: 1,
	LZ_IMAGE_TYPE_PLT1_BE: 2,
	LZ_IMAGE_TYPE_PLT4_LE: 3,
	LZ_IMAGE_TYPE_PLT4_BE: 4,
	LZ_IMAGE_TYPE_PLT8: 5,
	LZ_IMAGE_TYPE_RGB16: 6,
	LZ_IMAGE_TYPE_RGB24: 7,
	LZ_IMAGE_TYPE_RGB32: 8,
	LZ_IMAGE_TYPE_RGBA: 9,
	LZ_IMAGE_TYPE_XXXA: 10,
	LZPALETTE_FLAG_PAL_CACHE_ME: 1,
	LZPALETTE_FLAG_PAL_FROM_CACHE: 2,
	LZPALETTE_FLAG_TOP_DOWN: 4,
	PLT_PIXELS_PER_BYTE: [0, 8, 8, 2, 2, 1],
	PLT1_MASK: [1, 2, 4, 8, 16, 32, 64, 128],

	copy_pixel: function(op, color, out_buf) {
		out_buf[(op) + 0] = color.r;
		out_buf[(op) + 1] = color.g;
		out_buf[(op) + 2] = color.b;
	},
		
	lz_rgb32_decompress_rgb: function(arr) {
		//TODO: global alpha and uncouple code
		var encoder = 0;
		var op = 0;
		var ctrl;
		var in_buf = new Uint8Array(arr);
		var format = in_buf[encoder++];
		var opaque = in_buf[encoder++];
		var type = in_buf[encoder++];
		encoder++; //padding
		
		var low = in_buf[encoder+1]*Math.pow(16, 2)+in_buf[encoder];
		encoder += 2;
		var high = in_buf[encoder+1]*Math.pow(16, 2)+in_buf[encoder];
		encoder += 2;
		var len = high*Math.pow(16, 4)+low;

		var buf = new ArrayBuffer(len);
		var buf8 = new Uint8Array(buf);
		var data = new Uint32Array(buf);
		var out_buf_len = len/4;
		
		var code, ref, len, ofs, ref_4, b_4, b;
 
		for (ctrl = in_buf[encoder++]; op < out_buf_len; ctrl = in_buf[encoder++])
		{
			ref = op;
			len = ctrl >> 5;
			ofs = ((ctrl & 31) << 8);

			if (ctrl > 31) { //>=32
				len--;
	
				if (len === 6) {
					do {
						code = in_buf[encoder++];
						len += code;
					} while (code === 255);
				}
				code = in_buf[encoder++];
				ofs += code;
	
	
				if (code === 255) {
					if ((ofs - code) === (31 << 8)) {
						ofs = in_buf[encoder++] << 8;
						ofs += in_buf[encoder++];
						ofs += 8191;
					}
				}
				len += 1;
				ofs += 1;
				ref -= ofs;
				
				if (ref === (op - 1)) {//plt4/1 what?
					b = ref;
					b_4 = b*4;
					for (; len; --len) {
						data[op] =
							(255   << 24) |    // alpha
							(buf8[(b_4)+2] << 16) |    // blue
							(buf8[(b_4)+1] <<  8) |    // green
							 buf8[(b_4)];            // red
						
						op++;
					}
				} else {

					for (; len; --len) {
						//COPY_REF_PIXEL
						ref_4 = ref*4;

						data[op] =
							(255   << 24) |    // alpha
							(buf8[(ref_4)+2] << 16) |    // blue
							(buf8[(ref_4)+1] <<  8) |    // green
							 buf8[(ref_4)];            // red
						
						op++;ref++;
					}
				}
			} else {
				//COPY_COMP_PIXEL
				ctrl++;

				data[op] =
					(255   << 24) |    // alpha
					(in_buf[encoder] << 16) |    // blue
					(in_buf[encoder + 1] <<  8) |    // green
					 in_buf[encoder + 2];            // red
					 
				encoder += 3;
				
				op++;
				
	
				for (--ctrl; ctrl; ctrl--) {
					//COPY_COMP_PIXEL

					data[op] =
						(255   << 24) |    // alpha
						(in_buf[encoder] << 16) |    // blue
						(in_buf[encoder + 1] <<  8) |    // green
						 in_buf[encoder + 2];            // red
					encoder += 3;
					
					op++;
				}
			}
		}
	
		if (type === this.LZ_IMAGE_TYPE_RGBA && !opaque) {
	
			op = 0;
			ctrl = null;
			encoder--;
			for (ctrl = in_buf[encoder++]; op < out_buf_len; ctrl = in_buf[encoder++])
			{
				var ref = op;
				var len = ctrl >> 5;
				var ofs = ((ctrl & 31) << 8);
				var op_4 = op*4;

				if (ctrl >= 32) {

					var code;
					len--;

					if (len === 7 - 1) {
						do {
							code = in_buf[encoder++];
							len += code;
						} while (code === 255);
					}
					code = in_buf[encoder++];
					ofs += code;


					if (code === 255) {
						if ((ofs - code) === (31 << 8)) {
							ofs = in_buf[encoder++] << 8;
							ofs += in_buf[encoder++];
							ofs += 8191;
						}
					}
					len += 3;

					ofs += 1;

					ref -= ofs;
					if (ref === (op - 1)) {//plt4/1 what?
						var b = ref;

						for (; len; --len) {
							op_4 = op*4;
							//COPY_PIXEL
							buf8[(op_4) + 3] = buf8[(b*4)+3];

							op++;
						}
					} else {

						for (; len; --len) {
							//COPY_REF_PIXEL
							op_4 = op*4;
							buf8[(op_4) + 3] = buf8[(ref*4)+3];

							op++;ref++;
						}
					}
				} else {
					//COPY_COMP_PIXEL
					ctrl++;
					buf8[(op_4) + 3] = in_buf[encoder++];
					op++;


					for (--ctrl; ctrl; ctrl--) {
						//COPY_COMP_PIXEL
						op_4 = op*4; // faster?
						buf8[(op_4) + 3] = in_buf[encoder++];
						op++;
					}
				}
			}	
		}
		return buf;
	},
		
	lz_rgb32_decompress: function(in_buf, at, out_buf, type, default_alpha, palette, opaque) {
		//TODO: global alpha and uncouple code
		var encoder = at;
		var op = 0;
		var ctrl;
		var out_buf_len = out_buf.length/4;
		var is_rgba = type === this.LZ_IMAGE_TYPE_RGBA?true:false;
 
		for (ctrl = in_buf[encoder++]; op < out_buf_len; ctrl = in_buf[encoder++])
		{
			var ref = op;
			var len = ctrl >> 5;
			var ofs = ((ctrl & 31) << 8);
			var op_4 = op*4;

			if (ctrl >= 32) {
	
				var code;
				len--;
	
				if (len === 7 - 1) {
					do {
						code = in_buf[encoder++];
						len += code;
					} while (code === 255);
				}
				code = in_buf[encoder++];
				ofs += code;
	
	
				if (code === 255) {
					if ((ofs - code) === (31 << 8)) {
						ofs = in_buf[encoder++] << 8;
						ofs += in_buf[encoder++];
						ofs += 8191;
					}
				}
				len += 1;
				if (is_rgba || palette)
					len += 2;

				ofs += 1;
				//CAST_PLT_DISTANCE ofs and len
				if (type === this.LZ_IMAGE_TYPE_PLT4_LE || type === this.LZ_IMAGE_TYPE_PLT4_BE) {
					ofs = ofs*2;
					len = len*2;
				} else if (type === this.LZ_IMAGE_TYPE_PLT1_BE || type === this.LZ_IMAGE_TYPE_PLT1_LE) {
					ofs = ofs*8;
					len = len*8;
				}

				ref -= ofs;
				if (ref === (op - 1)) {//plt4/1 what?
					var b = ref;

					for (; len; --len) {
						op_4 = op*4;
						//COPY_PIXEL
						if (is_rgba)
						{
							if(opaque) {
								out_buf[(op_4) + 3] = 255;
							} else {
								out_buf[(op_4) + 3] = out_buf[(b*4)+3];
							}
						}
						else
						{
							for (var i = 0; i < 4; i++)
								out_buf[(op_4) + i] = out_buf[(b*4)+i];
						}
						op++;
					}
				} else {

					for (; len; --len) {
						//COPY_REF_PIXEL
						op_4 = op*4;
						if (is_rgba)
						{
							if(opaque) {
								out_buf[(op_4) + 3] = 255;
							} else {
								out_buf[(op_4) + 3] = out_buf[(ref*4)+3];
							}
							
						}
						else
						{
							for (i = 0; i < 4; i++)
								out_buf[(op_4) + i] = out_buf[(ref*4)+i];
						}
						op++;ref++;
					}
				}
			} else {
				//COPY_COMP_PIXEL
				ctrl++;

				if (is_rgba) {
					if(opaque) {
						out_buf[(op_4) + 3] = 255;encoder++;
					} else {
						out_buf[(op_4) + 3] = in_buf[encoder++];
					}
				} else if (palette) {
					if (type === this.LZ_IMAGE_TYPE_PLT1_LE) {
						var oct = in_buf[encoder++];
						var foreColor = palette[1];
						var backColor = palette[0];

						for (var i = 0; i < 8; i++) {
							if (oct & this.PLT1_MASK[i]) {
								this.copy_pixel(op_4, foreColor, out_buf);
							} else {
								this.copy_pixel(op_4, backColor, out_buf);
							}
							if (default_alpha)
								out_buf[(op_4) + 3] = 255;
							if (i < 7)
								op++;op_4 = op*4;
						}
					} else if (type === this.LZ_IMAGE_TYPE_PLT1_BE) {
						var oct = in_buf[encoder++];
						var foreColor = palette[1];
						var backColor = palette[0];

						for (var i = 7; i >= 0; i--) {
							if (oct & this.PLT1_MASK[i]) {
								this.copy_pixel(op_4, foreColor, out_buf);
							} else {
								this.copy_pixel(op_4, backColor, out_buf);
							}
							if (default_alpha)
								out_buf[(op_4) + 3] = 255;
							if (i > 0)
								op++;op_4 = op*4;
						}
					} else if (type === this.LZ_IMAGE_TYPE_PLT4_LE) {
						var oct = in_buf[encoder++];
						var spiceColor = palette[(oct & 0x0f)];
						this.copy_pixel(op_4, spiceColor, out_buf);
						if (default_alpha)
							out_buf[(op_4) + 3] = 255;
						op++;
						op_4 = op*4;

						var spiceColor = palette[((oct >>> 4) & 0x0f)];
						this.copy_pixel(op_4, spiceColor, out_buf);
						if (default_alpha)
							out_buf[(op_4) + 3] = 255;
					} else if (type === this.LZ_IMAGE_TYPE_PLT4_BE) {
						var oct = in_buf[encoder++];
						var bits1 = ((oct >>> 4) & 0x0f);
						var bits2 = oct & 0x0f;
						var spiceColor = palette[bits1];
						this.copy_pixel(op_4, spiceColor, out_buf);
						if (default_alpha)
							out_buf[(op_4) + 3] = 255;
						op++;
						op_4 = op*4;

						var spiceColor = palette[bits2];
						this.copy_pixel(op_4, spiceColor, out_buf);
						if (default_alpha)
							out_buf[(op_4) + 3] = 255;
					} else if (type === this.LZ_IMAGE_TYPE_PLT8) {
						var posPal = in_buf[encoder++];
						var spiceColor = palette[posPal];
						this.copy_pixel(op_4, spiceColor, out_buf);
						if (default_alpha)
							out_buf[(op_4) + 3] = 255;
					}
				} else {
					out_buf[(op_4) + 0] = in_buf[encoder + 2];
					out_buf[(op_4) + 1] = in_buf[encoder + 1];
					out_buf[(op_4) + 2] = in_buf[encoder + 0];
					if (default_alpha)
						out_buf[(op_4) + 3] = 255;
					encoder += 3;
				}
				op++;
				
	
				for (--ctrl; ctrl; ctrl--) {
					//COPY_COMP_PIXEL
					op_4 = op*4; // faster?
					if (is_rgba) {
						if(opaque) {
							out_buf[(op_4) + 3] = 255;
						} else {
							out_buf[(op_4) + 3] = in_buf[encoder++];
						}
					} else if (palette) {
						if (type === this.LZ_IMAGE_TYPE_PLT1_LE) {
							var oct = in_buf[encoder++];
							var foreColor = palette[1];
							var backColor = palette[0];

							for (var i = 0; i < 8; i++) {
								if (oct & this.PLT1_MASK[i]) {
									this.copy_pixel(op_4, foreColor, out_buf);
								} else {
									this.copy_pixel(op_4, backColor, out_buf);
								}
								if (default_alpha)
									out_buf[(op_4) + 3] = 255;
								if (i < 7)
									op++;op_4 = op*4;
							}
						} else if (type === this.LZ_IMAGE_TYPE_PLT1_BE) {
							var oct = in_buf[encoder++];
							var foreColor = palette[1];
							var backColor = palette[0];

							for (var i = 7; i >=0; i--) {
								if (oct & this.PLT1_MASK[i]) {
									this.copy_pixel(op_4, foreColor, out_buf);
								} else {
									this.copy_pixel(op_4, backColor, out_buf);
								}
								if (default_alpha)
									out_buf[(op_4) + 3] = 255;
								if (i > 0)
									op++;op_4 = op*4;
							}
						} else if (type === this.LZ_IMAGE_TYPE_PLT4_LE) {
							var oct = in_buf[encoder++];
							var spiceColor = palette[(oct & 0x0f)];
							this.copy_pixel(op_4, spiceColor, out_buf);
							if (default_alpha)
								out_buf[(op_4) + 3] = 255;
							op++;
							op_4 = op*4;
							var spiceColor = palette[((oct >>> 4) & 0x0f)];
							this.copy_pixel(op_4, spiceColor, out_buf);
							if (default_alpha)
								out_buf[(op_4) + 3] = 255;
						} else if (type === this.LZ_IMAGE_TYPE_PLT4_BE) {
							var oct = in_buf[encoder++];
							var spiceColor = palette[((oct >>> 4) & 0x0f)];
							this.copy_pixel(op_4, spiceColor, out_buf);
							if (default_alpha)
								out_buf[(op_4) + 3] = 255;
							op++;
							op_4 = op*4;

							var spiceColor = palette[(oct & 0x0f)];
							this.copy_pixel(op_4, spiceColor, out_buf);
							if (default_alpha)
								out_buf[(op_4) + 3] = 255;
						} else if (type === this.LZ_IMAGE_TYPE_PLT8) {
							var posPal = in_buf[encoder++];
							var spiceColor = palette[posPal];
							this.copy_pixel(op_4, spiceColor, out_buf);
							if (default_alpha)
								out_buf[(op_4) + 3] = 255;
						}
					} else {
						out_buf[(op_4) + 0] = in_buf[encoder + 2];
						out_buf[(op_4) + 1] = in_buf[encoder + 1];
						out_buf[(op_4) + 2] = in_buf[encoder + 0];
						if (default_alpha)
							out_buf[(op_4) + 3] = 255;
						encoder += 3;
					}
					op++;
				}
			}
		}
		return encoder - 1;
	},

	convert_spice_lz_to_web: function(context, data, imageDescriptor, opaque) { //TODO: refactor this shit code
		// var aux = data.toJSArray();
		var format = imageDescriptor.type;
        data = data.toJSArray(); //this old functions has no support for typed arrays...
		if (format === wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_PLT) {
			var flags = wdi.SpiceObject.bytesToInt8(data.splice(0, 1));
			if (flags === this.LZPALETTE_FLAG_PAL_FROM_CACHE) {
				var header = data.splice(0, 12);
				var length = wdi.SpiceObject.bytesToInt32(header.splice(0, 4));
                var palette_id = wdi.SpiceObject.bytesToInt64(header.splice(0, 8));

                header = data;

                var magic = wdi.SpiceObject.bytesToStringBE(header.splice(0, 4));
                var version = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
                var type = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
                var width = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
                var height = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
                var stride = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
                var top_down = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));

			} else if (flags === this.LZPALETTE_FLAG_PAL_CACHE_ME) {
				var imageHeaders = imageDescriptor.offset + 1; //+1 because of the Flags byte
				var currentHeaders = 36;
				var header = data.splice(0, currentHeaders);
				var length = wdi.SpiceObject.bytesToInt32(header.splice(0, 4));
				var palette_offset = wdi.SpiceObject.bytesToInt32(header.splice(0, 4));
				var spliceInit = palette_offset-imageHeaders-currentHeaders;
				//LZ Compression headers with its magic
				var magic = wdi.SpiceObject.bytesToStringBE(header.splice(0, 4));
				var version = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
				var type = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
				var width = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
				var height = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
				var stride = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));
				var top_down = wdi.SpiceObject.bytesToInt32BE(header.splice(0,4));

				var palette_id = wdi.SpiceObject.bytesToInt64(data.splice(spliceInit, 8));

				var num_palettes = wdi.SpiceObject.bytesToInt16(data.splice(spliceInit, 2));
				var palette = [];
				
				for (var i = 0; i < num_palettes; i++) {
					var queue = new wdi.Queue();
					queue.setData(data.splice(spliceInit, 4));
					palette.push(new wdi.SpiceColor().demarshall(queue));
				}
				wdi.ImageCache.addPalette(palette_id, palette);
			} else {
				wdi.Debug.error('Unimplemented lz palette top down');
			}
			var palette = wdi.ImageCache.getPalette(palette_id);
		}

		if (type !== this.LZ_IMAGE_TYPE_RGB32 && type !== this.LZ_IMAGE_TYPE_RGBA &&
			type !== this.LZ_IMAGE_TYPE_RGB24 && type !== this.LZ_IMAGE_TYPE_PLT8 &&
			type !== this.LZ_IMAGE_TYPE_PLT1_LE && type !== this.LZ_IMAGE_TYPE_PLT1_BE && 
			type !== this.LZ_IMAGE_TYPE_PLT4_LE && type !== this.LZ_IMAGE_TYPE_PLT4_BE) {
			return false;
		}

		if (palette) {
			var ret = context.createImageData(stride*this.PLT_PIXELS_PER_BYTE[type], height);
			// if (type === this.LZ_IMAGE_TYPE_PLT1_BE) {
				// this.lz_rgb32_plt1_be_decompress(data, ret.data, palette);
			// } else {
				this.lz_rgb32_decompress(data, 0, ret.data, type, type !== this.LZ_IMAGE_TYPE_RGBA, palette);
			// }

			var tmpCanvas = wdi.graphics.getNewTmpCanvas(width, height);
			tmpCanvas.getContext('2d').putImageData(ret, 0, 0, 0, 0, width, height);
			ret = tmpCanvas;
		} else {
			var arr = new ArrayBuffer(data.length+8);
			var u8 = new Uint8Array(arr);
			u8[0] = 1;
			u8[1] = opaque;
			u8[2] = type;
			u8[3] = 0;
			
			var number = ret.data.length;
		
			for (var i = 0;i < 4;i++) {//iterations because of javascript number size 
				u8[4+i] = number & (255);//Get only the last byte
				number = number >> 8;//Remove the last byte
			}
		
			u8.set(data, 8);
			var result = new Uint8ClampedArray(this.lz_rgb32_decompress_rgb(arr));
			ret = new ImageData(result, width, height);
			ret = wdi.graphics.getImageFromData(ret);
		}

		if(!top_down) {
			//TODO: PERFORMANCE:
			ret = wdi.RasterOperation.flip(ret);
		}



		return ret;
	},
    
    demarshall_rgb: function(data) {
        var header = data.splice(0, 32);
        return {
            length: wdi.SpiceObject.bytesToInt32(header.splice(0,4)),
            magic: wdi.SpiceObject.bytesToStringBE(header.splice(0,4)),
            version: wdi.SpiceObject.bytesToInt32BE(header.splice(0,4)),
            type: wdi.SpiceObject.bytesToInt32BE(header.splice(0,4)),
            width: wdi.SpiceObject.bytesToInt32BE(header.splice(0,4)),
            height: wdi.SpiceObject.bytesToInt32BE(header.splice(0,4)),
            stride: wdi.SpiceObject.bytesToInt32BE(header.splice(0,4)),
            top_down: wdi.SpiceObject.bytesToInt32BE(header.splice(0,4))
        }
    },

    lz_rgb32_plt1_be_decompress: function(in_buf, out_buf, palette) {
		var encoder = 0;
		var op = 0;
		var ctrl;
		var out_buf_len = out_buf.length/4;
		var ref, len, ofs, next, ref_4, oct, foreColor, backColor, i;
		var type = this.LZ_IMAGE_TYPE_PLT1_BE;

		var pix_per_byte = this.PLT_PIXELS_PER_BYTE[type];

		var pre_255_24 = 255 << 24;
		var pre_31_8_plus255 = (31 << 8) + 255; //8191 === 13 bits to 1

		for (ctrl = in_buf[encoder++]; op < out_buf_len; ctrl = in_buf[encoder++]) {
			ref = op;
			len = ctrl >> 5;
			ofs = ((ctrl & 31) << 8);

			if (ctrl > 31) {

				if (len === 7) {
					do {
						next = in_buf[encoder++];
						len += next;
					} while (next === 255);
				}

				ofs += in_buf[encoder++];

				if (ofs  === pre_31_8_plus255) {
					ofs += in_buf[encoder++] << 8 + in_buf[encoder++];
				}

				//CAST_PLT_DISTANCE ofs and len
				len = (len + 2) * pix_per_byte;

				ref -= (ofs + 1) * pix_per_byte;
				if (ref === (op - 1)) {
					ref_4 = ref * 4;
					while (len-- !== 0) {
						//COPY_PIXEL
						op_4 = op * 4;

						out_buf[op_4] = out_buf[ref_4];
						out_buf[op_4 + 1] = out_buf[ref_4 + 1];
						out_buf[op_4 + 2] = out_buf[ref_4 + 2];
						out_buf[op_4 + 3] = out_buf[ref_4 + 3];

						op++;
					}
				} else {
					while (len-- !== 0) {
						//COPY_REF_PIXEL
						op_4 = op * 4;
						ref_4 = ref * 4;

						out_buf[op_4] = out_buf[ref_4];
						out_buf[op_4 + 1] = out_buf[ref_4 + 1];
						out_buf[op_4 + 2] = out_buf[ref_4 + 2];
						out_buf[op_4 + 3] = out_buf[ref_4 + 3];

						op++;ref++;
					}
				}
			} else {
				//COPY_COMP_PIXEL
				while (ctrl-- !== -1) {
					//COPY_COMP_PIXEL
					op_4 = op * 4; // faster?

					oct = in_buf[encoder++];
					foreColor = palette[1];
					backColor = palette[0];

					for (i = 7; i >=0; i--) {
						op_4 = op * 4;

						if (oct & this.PLT1_MASK[i]) {
							out_buf[op_4 + 0] = foreColor.r;
							out_buf[op_4 + 1] = foreColor.g;
							out_buf[op_4 + 2] = foreColor.b;
						} else {
							out_buf[op_4 + 0] = backColor.r;
							out_buf[op_4 + 1] = backColor.g;
							out_buf[op_4 + 2] = backColor.b;
						}
						out_buf[(op_4) + 3] = 255;

						op++;
					}
				}
			}
		}
	}
};
