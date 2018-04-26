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

wdi.RasterEngine = $.spcExtend(wdi.EventObject.prototype, {
	init: function(c) {
		this.clientGui = c.clientGui;
	},

	drawCanvas: function(spiceMessage) {
		return this.clientGui.drawCanvas(spiceMessage);
	},

	removeCanvas: function(spiceMessage) {
		return this.clientGui.removeCanvas(spiceMessage);
	},

	invalList: function(spiceMessage) {
		var items = spiceMessage.args.items;
		var item = null;
		for(var i in items) {
			item = items[i];
			wdi.ImageCache.delImage(item.id);
		}
	},

	handleStreamCreate: function(spiceMessage) {
		var stream = spiceMessage.args;
		stream.computedBox = wdi.graphics.getBoxFromSrcArea(stream.rect);
		wdi.Stream.addStream(spiceMessage.args.id, stream);
	},

	handleStreamData: function(spiceMessage) {
		var imageData = spiceMessage.args.data; //jpeg string encoded
		var stream = wdi.Stream.getStream(spiceMessage.args.id); //recover the stream
		var context = this.clientGui.getContext(stream.surface_id);
		var img = wdi.GlobalPool.create('Image'); //auto-release pool
		wdi.ExecutionControl.sync = true;
		var url;
		img.onload = function() {
			URL.revokeObjectURL(url);
			var box = stream.computedBox;
			// we only rotate the stream if spice tells us so through the TOP_DOWN flag mask
			if (!stream.flags & wdi.SpiceStreamFlags.SPICE_STREAM_FLAGS_TOP_DOWN) {
				var offsetX = box.x + (this.width/2);
				var offsetY = box.y + (this.height/2);
				context.save();
				context.translate(offsetX, offsetY);
				context.rotate(Math.PI);
				context.scale(-1,1);
				context.drawImage(this, box.x-offsetX, box.y-offsetY, box.width, box.height);
				context.restore();
			} else {
				context.drawImage(this, box.x, box.y, box.width, box.height);
			}
		};

		img.onerror = function() {
			URL.revokeObjectURL(url)
		};

		url = wdi.SpiceObject.bytesToURI(imageData);
		img.src = url;
	},

	handleStreamClip: function(spiceMessage) {
		wdi.Stream.clip(spiceMessage.args.id, spiceMessage.args.clip)
	},

	handleStreamDestroy: function(spiceMessage) {
		wdi.Stream.deleteStream(spiceMessage.args.id);
	},

	drawRop3: function(spiceMessage) {
		var box = wdi.graphics.getBoxFromSrcArea(spiceMessage.args.base.box);
		var context = this.clientGui.getContext(spiceMessage.args.base.surface_id);
		var destImg = context.getImageData(box.x, box.y, box.width, box.height);
		var clientGui = this.clientGui;

		var brush = spiceMessage.args.brush;
		var rop = spiceMessage.args.rop_descriptor;

		var srcArea = wdi.graphics.getBoxFromSrcArea(spiceMessage.args.src_area);
		wdi.graphics.getImageFromSpice(spiceMessage.args.src_image.imageDescriptor, spiceMessage.args.src_image.data, this.clientGui, function (sourceCanvas) {
			if (sourceCanvas) {
				//Get source image data (image coming from the packet)
				var sourceContext = sourceCanvas.getContext('2d');
				var srcImg = sourceContext.getImageData(srcArea.x, srcArea.y, srcArea.width, srcArea.height);
				var srcImgData = srcImg.data; //this

				//Get pattern image data
				//brush
				var tmpcanvas = wdi.graphics.getNewTmpCanvas(box.width, box.height);
				var tmpcontext = tmpcanvas.getContext('2d');
				var brushBox = {
					width: box.width,
					height: box.height,
					x: 0,
					y: 0
				};
				wdi.graphics.setBrush(clientGui, tmpcontext, brush, brushBox, wdi.SpiceRopd.SPICE_ROPD_OP_PUT);//Without alpha?
				var pattern = tmpcontext.getImageData(0, 0, box.width, box.height);
				var patImgData = pattern.data; //this

				//Get dest image data
				var destImgData = destImg.data;

				//Get result image data
				tmpcanvas = wdi.graphics.getNewTmpCanvas(box.width, box.height);
				tmpcontext = tmpcanvas.getContext('2d');
				var result = tmpcontext.createImageData(box.width, box.height);
				var resultData = result.data;

				if ((srcImg.width != pattern.width || srcImg.width != destImg.width) || (srcImg.height != pattern.height || srcImg.height != destImg.height)) {
					//TODO: resize
				}

				//Do the Ternary Raster Operation
				var length = destImgData.length;//Could be anyone
				var func = wdi.Rop3[rop];
				for (var i = 0;i<length;i+=4) {
					resultData[i] = func(patImgData[i], srcImgData[i], destImgData[i]) & 255;
					resultData[i+1] = func(patImgData[i+1], srcImgData[i+1], destImgData[i+1]) & 255;
					resultData[i+2] = func(patImgData[i+2], srcImgData[i+2], destImgData[i+2]) & 255;
					resultData[i+3] = 255;
				}

				tmpcontext.putImageData(result, 0, 0);

				this.drawClip(tmpcanvas, box, context);
			} else {
				wdi.Debug.log('Unable to get image!');
			}
		}, this);
	},

	drawInvers: function(spiceMessage) {
		var drawBase = spiceMessage.args.base;
		var box = wdi.graphics.getBoxFromSrcArea(drawBase.box);

		var surface_id = drawBase.surface_id;

		var context = this.clientGui.getContext(surface_id);

		var destImg = wdi.graphics.getRect(box, context.canvas);
		var imageData = wdi.RasterOperation.process(wdi.SpiceRopd.SPICE_ROPD_OP_INVERS, null, destImg);//this operation modifies destination

		context.drawImage(imageData, box.x, box.y, box.width, box.height);
	},

	drawStroke: function(spiceMessage) {
		var stroke = spiceMessage.args,
			context = this.clientGui.getContext(spiceMessage.args.base.surface_id),
			color = stroke.brush.color.html_color,
			lineWidth = 1,
			pointsLength,
			firstPoint,
			i,
			j,
			length = stroke.path.num_segments,
			seg;

		if (stroke.attr.flags & wdi.SpiceLineFlags.SPICE_LINE_FLAGS_STYLED) {
			wdi.Debug.log('SPICE_LINE_FLAGS_STYLED');
		}

		for (var i = 0;i < length; i++) {
			seg = stroke.path.segments[i];

			if (seg.flags & wdi.SpicePathFlags.SPICE_PATH_BEGIN) {
				context.beginPath();
				context.moveTo(seg.points[0].x, seg.points[0].y);
				context.strokeStyle = color;
				context.lineWidth = lineWidth;
			}
			if (seg.flags & wdi.SpicePathFlags.SPICE_PATH_BEZIER) {
				pointsLength = seg.points.length;
				if (pointsLength % 3 == 0) {
					for (j = 0; j < pointsLength; j += 3) {
						context.bezierCurveTo(
							seg.points[j].x, seg.points[j].y,
							seg.points[j+1].x, seg.points[j+1].y,
							seg.points[j+2].x, seg.points[j+2].y
						);
					}
				}
			} else {
				pointsLength = seg.points.length;

				for (j = 0; j < pointsLength; j++) {
					if (j == 0) firstPoint = seg.points[j];
					context.lineTo(seg.points[j].x + (lineWidth / 2), seg.points[j].y + (lineWidth / 2));
				}
			}
			if (seg.flags & wdi.SpicePathFlags.SPICE_PATH_END) {
				if (seg.flags & wdi.SpicePathFlags.SPICE_PATH_CLOSE) {
					context.lineTo(firstPoint.x + (lineWidth / 2), firstPoint.y + (lineWidth / 2));
				}
				context.stroke();
				context.closePath();
			}
		}
	},

	drawImage: function(spiceMessage) {
		var args = spiceMessage.args;
		var drawBase = args.base;
		var surface_id = drawBase.surface_id;
		var rop = args.rop_descriptor;

		var scale = args.scale_mode;


		//calculate src_area box
		var box_origin = wdi.graphics.getBoxFromSrcArea(args.src_area);

		var box_dest = wdi.graphics.getBoxFromSrcArea(drawBase.box);

		//depending on the rop, we can avoid to get destImg
		if (rop === wdi.SpiceRopd.SPICE_ROPD_OP_PUT) {
			var destImg = null;
		} else {
			//get the destination image, there is a ROP
			var destImg = wdi.graphics.getRect(box_dest, this.clientGui.getCanvas(surface_id));
		}

		if (window.vdiLoadTest && window.firstImage === undefined) {
			window.firstImage = true;
		}

		//get the image in imagedata format
		wdi.graphics.getImageFromSpice(args.image.imageDescriptor, args.image.data, this.clientGui, function(srcImg) {
			//we have image?
			if(srcImg) {
				if (window.firstImage) {
					var data;
					if(srcImg.getContext) {
						data = srcImg.getContext('2d').getImageData(0, 0, srcImg.width, srcImg.height).data.buffer.slice(0)
					} else {
						data = srcImg.data.buffer.slice(0);
					}
					window.firstImageData = data;
					window.firstImage = false;
				}

				//adapt to src_area
				srcImg = wdi.graphics.getRect(box_origin, srcImg);
				if(box_origin.width !== box_dest.width && box_origin.height !== box_dest.height) {
					srcImg = wdi.graphics.getImageFromData(srcImg);
					var newSrcImg = wdi.graphics.getNewTmpCanvas(box_dest.width, box_dest.height);
					var tmpcontext = newSrcImg.getContext('2d');
					tmpcontext.drawImage(srcImg, 0, 0, box_origin.width, box_origin.height, 0, 0, box_dest.width, box_dest.height);
					srcImg = newSrcImg;
				}

				//rop
				srcImg = wdi.RasterOperation.process(rop, srcImg, destImg);

				var context = this.clientGui.getContext(surface_id);

				//TODO: swcanvas do not support clipping
				if(args.base.clip.type === wdi.SpiceClipType.SPICE_CLIP_TYPE_RECTS) {
					srcImg = wdi.graphics.getImageFromData(srcImg);
				}

				if(srcImg instanceof ImageData) {
					context.putImageData(srcImg, box_dest.x, box_dest.y, 0, 0, box_dest.width, box_dest.height);
				} else {
					context.drawImage(srcImg, box_dest.x, box_dest.y, box_dest.width, box_dest.height);
				}

			} else {
				//failed to get image, cache error?
				wdi.Debug.log('Unable to get image!');
			}
		}, this, {'opaque':true, 'brush': args.brush, 'raw': false});
	},

	drawClip: function(srcImg, box, context) {
		context.drawImage(srcImg, box.x, box.y, box.width, box.height);
	},

	drawFill: function(spiceMessage) {
		var args = spiceMessage.args;
		var context = this.clientGui.getContext(args.base.surface_id);
		var box = wdi.graphics.getBoxFromSrcArea(args.base.box);
		var brush = args.brush;
		var ropd = args.rop_descriptor;

		wdi.graphics.setBrush(this.clientGui, context, brush, box, ropd);
	},

	drawCopyBits: function(spiceMessage) {
		var drawBase = spiceMessage.args.base;
		var surface_id = drawBase.surface_id;
		var src_position = spiceMessage.args.src_position;
		var context = this.clientGui.getContext(surface_id);
		var box = drawBase.box;

		var width = box.right - box.left;
		var height = box.bottom - box.top;

		context.drawImage(context.canvas, src_position.x, src_position.y, width,
			height, drawBase.box.left, drawBase.box.top, width, height);
	},

	drawBlend: function(spiceMessage) {
		//TODO: alpha_flags
		//TODO: resize
		var descriptor = spiceMessage.args.image.imageDescriptor;
		var drawBase = spiceMessage.args.base;
		var imgData = spiceMessage.args.image.data;
		var surface_id = spiceMessage.args.base.surface_id;
		var rop_desc = spiceMessage.args.rop_descriptor;
		var flags = spiceMessage.args.flags;

		wdi.graphics.getImageFromSpice(descriptor, imgData, this.clientGui, function(srcImg) {
			if (!srcImg) {
				wdi.Debug.log('There is no image on Blend');
				return;
			}

			//get box from src area
			var box = wdi.graphics.getBoxFromSrcArea(spiceMessage.args.src_area);

			//adapt to src_area
			srcImg = wdi.graphics.getRect(box, srcImg);

			//destination box
			var dest_box = wdi.graphics.getBoxFromSrcArea(drawBase.box);
			var destImg = wdi.graphics.getRect(dest_box, this.clientGui.getCanvas(surface_id));

			var result = wdi.RasterOperation.process(rop_desc, srcImg, destImg);

			this.clientGui.getCanvas(surface_id).getContext('2d').drawImage(result, dest_box.x, dest_box.y, dest_box.width, dest_box.height);
		}, this);
	},

	drawAlphaBlend: function(spiceMessage) {

		//TODO: alpha_flags
		//TODO: resize

		var descriptor = spiceMessage.args.image.imageDescriptor;
		var drawBase = spiceMessage.args.base;
		var imgData = spiceMessage.args.image.data;
		var surface_id = spiceMessage.args.base.surface_id;
		var flags = spiceMessage.args.alpha_flags;
		var alpha = spiceMessage.args.alpha;

		wdi.graphics.getImageFromSpice(descriptor, imgData, this.clientGui, function(srcImg) {
			if (!srcImg) {
				wdi.Debug.log('There is no image on drawAlphaBlend');
			}

			var box = wdi.graphics.getBoxFromSrcArea(spiceMessage.args.src_area);

			//adapt to src_area
			srcImg = wdi.graphics.getRect(box, srcImg);


			//destination box
			var box_dest = wdi.graphics.getBoxFromSrcArea(drawBase.box);
			var destImg = wdi.graphics.getRect(box_dest, this.clientGui.getCanvas(surface_id));

			if(box.width !== box_dest.width && box.height !== box_dest.height) {
				var tmpcanvas = wdi.graphics.getNewTmpCanvas(box_dest.width, box_dest.height);
				var tmpcontext = tmpcanvas.getContext('2d');
				tmpcontext.drawImage(srcImg, 0, 0, box.width, box.height, 0, 0, box_dest.width, box_dest.height);
				srcImg = tmpcanvas;
			}

			var src = wdi.graphics.getDataFromImage(srcImg).data;
			var dst = wdi.graphics.getDataFromImage(destImg).data;

			var length = src.length-1;

			//create a new imagedata to store result
			var imageResult = wdi.graphics.getNewTmpCanvas(box_dest.width, box_dest.height);
			var context = imageResult.getContext('2d');

			var resultImageData = context.createImageData(box_dest.width, box_dest.height);
			var result = resultImageData.data;

			var rS, rD;
			var gS, gD;
			var bS, bD;
			var aS;

			for (var px=0;px<length;px+=4) {
				rS = src[px];
				gS = src[px+1];
				bS = src[px+2];

				if(flags || alpha === 255) {
					aS = src[px+3];
				} else {
					aS = alpha;
				}

				rD = dst[px];
				gD = dst[px+1];
				bD = dst[px+2];

				if(aS > 30 && alpha === 255) {
					//formula from reactos, this is premultiplied alpha values
					result[px] = ((rD * (255 - aS)) / 255 + rS) & 0xff;
					result[px+1] = ((gD * (255 - aS)) / 255 + gS) & 0xff;
					result[px+2] = ((bD * (255 - aS)) / 255 + bS) & 0xff;
				} else {
					//homemade blend function, this is the typical blend function simplified
					result[px] = (( (rS*aS)+(rD*(255-aS)) ) / 255) & 0xff;
					result[px+1] = (( (gS*aS)+(gD*(255-aS)) ) / 255) & 0xff;
					result[px+2] = (( (bS*aS)+(bD*(255-aS)) ) / 255) & 0xff;
				}

				result[px+3] = 255;
			}
			imageResult.getContext('2d').putImageData(resultImageData, 0, 0);

			this.drawClip(imageResult, box_dest, this.clientGui.getContext(surface_id));
		}, this);
	},

	drawWhiteness: function(spiceMessage) {
		//TODO: mask
		var base = spiceMessage.args.base;
		var context = this.clientGui.getContext(base.surface_id);
		var box = wdi.graphics.getBoxFromSrcArea(base.box);
		context.fillStyle = "white";
		context.fillRect(box.x, box.y, box.width, box.height);
	},

	drawBlackness: function(spiceMessage) {
		//TODO: mask
		var base = spiceMessage.args.base;
		var context = this.clientGui.getContext(base.surface_id);
		var box = wdi.graphics.getBoxFromSrcArea(base.box);
		context.fillStyle = "black";
		context.fillRect(box.x, box.y, box.width, box.height);
	},

	drawTransparent: function(spiceMessage) {
		var drawBase = spiceMessage.args.base;
		var surface_id = drawBase.surface_id;

		//calculate src_area box
		var box = wdi.graphics.getBoxFromSrcArea(spiceMessage.args.src_area);
		var dest_box = wdi.graphics.getBoxFromSrcArea(drawBase.box);

		//get destination iamge, in imagedata format because is what we need
		var destImg = this.clientGui.getContext(surface_id).getImageData(dest_box.x, dest_box.y,
			dest_box.width, dest_box.height);

		wdi.graphics.getImageFromSpice(spiceMessage.args.image.imageDescriptor, spiceMessage.args.image.data, this.clientGui, function(srcImg) {
			if(srcImg) {
				//adapt to src_area
				srcImg = wdi.graphics.getRect(box, srcImg);

				var source = wdi.graphics.getDataFromImage(srcImg).data;
				var dest = destImg.data;

				var length = source.length-1;
				var resultImageData = this.clientGui.getContext(surface_id).createImageData(dest_box.width, dest_box.height);

				var color = spiceMessage.args.transparent_true_color;
				while(length>0) {
					resultImageData.data[length] = 255; //alpha
					if(source[length-1] === color.b && source[length-2] === color.g
						&& source[length-3] === color.r) {
						resultImageData.data[length-1] = dest[length-1]; //b
						resultImageData.data[length-2] = dest[length-2]; //g
						resultImageData.data[length-3] = dest[length-3]; //r
					} else {
						resultImageData.data[length-1] = source[length-1]; //b
						resultImageData.data[length-2] = source[length-2]; //g
						resultImageData.data[length-3] = source[length-3]; //r
					}

					length-=4;
				}
				var resultImage = wdi.graphics.getImageFromData(resultImageData);
				this.drawClip(resultImage, dest_box, this.clientGui.getContext(surface_id));
			} else {
				//failed to get image, cache error?
				wdi.Debug.log('Unable to get image!');
			}
		}, this);
	},

	drawText: function(spiceMessage) {
		var context = this.clientGui.getContext(spiceMessage.args.base.surface_id);
		var bbox = spiceMessage.args.base.box;
		var clip = spiceMessage.args.base.clip;
		var text = spiceMessage.args;
		var string = text.glyph_string;
		var bpp = string.flags === 1 ? 1 : string.flags * 2;

		if (text.back_mode !== 0) {
			wdi.graphics.drawBackText(this.clientGui, context, text);
		}

		wdi.graphics.drawString(context, string, bpp, text.fore_brush, clip.type, this);
	},

	/**
	 * Clears all color palettes
	 * @param spiceMessage
	 * @param app
	 */
	invalPalettes: function(spiceMessage) {
		wdi.ImageCache.clearPalettes();
	}
});
