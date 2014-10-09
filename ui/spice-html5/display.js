"use strict";
/*
   Copyright (C) 2012 by Jeremy P. White <jwhite@codeweavers.com>

   This file is part of spice-html5.

   spice-html5 is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   spice-html5 is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with spice-html5.  If not, see <http://www.gnu.org/licenses/>.
*/


/*----------------------------------------------------------------------------
**  FIXME: putImageData  does not support Alpha blending
**           or compositing.  So if we have data in an ImageData
**           format, we have to draw it onto a context,
**           and then use drawImage to put it onto the target,
**           as drawImage does alpha.
**--------------------------------------------------------------------------*/
function putImageDataWithAlpha(context, d, x, y)
{
    var c = document.createElement("canvas");
    var t = c.getContext("2d");
    c.setAttribute('width', d.width);
    c.setAttribute('height', d.height);
    t.putImageData(d, 0, 0);
    context.drawImage(c, x, y, d.width, d.height);
}

/*----------------------------------------------------------------------------
**  FIXME: Spice will send an image with '0' alpha when it is intended to
**           go on a surface w/no alpha.  So in that case, we have to strip
**           out the alpha.  The test case for this was flux box; in a Xspice
**           server, right click on the desktop to get the menu; the top bar
**           doesn't paint/highlight correctly w/out this change.
**--------------------------------------------------------------------------*/
function stripAlpha(d)
{
    var i;
    for (i = 0; i < (d.width * d.height * 4); i += 4)
        d.data[i + 3] = 255;
}

/*----------------------------------------------------------------------------
**  SpiceDisplayConn
**      Drive the Spice Display Channel
**--------------------------------------------------------------------------*/
function SpiceDisplayConn()
{
    SpiceConn.apply(this, arguments);
}

SpiceDisplayConn.prototype = Object.create(SpiceConn.prototype);
SpiceDisplayConn.prototype.process_channel_message = function(msg)
{
    if (msg.type == SPICE_MSG_DISPLAY_MARK)
    {
        // FIXME - DISPLAY_MARK not implemented (may be hard or impossible)
        this.known_unimplemented(msg.type, "Display Mark");
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_RESET)
    {
        DEBUG > 2 && console.log("Display reset");
        this.surfaces[this.primary_surface].canvas.context.restore();
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_DRAW_COPY)
    {
        var draw_copy = new SpiceMsgDisplayDrawCopy(msg.data);

        DEBUG > 1 && this.log_draw("DrawCopy", draw_copy);

        if (! draw_copy.base.box.is_same_size(draw_copy.data.src_area))
            this.log_warn("FIXME: DrawCopy src_area is a different size than base.box; we do not handle that yet.");
        if (draw_copy.base.clip.type != SPICE_CLIP_TYPE_NONE)
            this.log_warn("FIXME: DrawCopy we don't handle clipping yet");
        if (draw_copy.data.rop_descriptor != SPICE_ROPD_OP_PUT)
            this.log_warn("FIXME: DrawCopy we don't handle ropd type: " + draw_copy.data.rop_descriptor);
        if (draw_copy.data.mask.flags)
            this.log_warn("FIXME: DrawCopy we don't handle mask flag: " + draw_copy.data.mask.flags);
        if (draw_copy.data.mask.bitmap)
            this.log_warn("FIXME: DrawCopy we don't handle mask");

        if (draw_copy.data && draw_copy.data.src_bitmap)
        {
            if (draw_copy.data.src_bitmap.descriptor.flags &&
                draw_copy.data.src_bitmap.descriptor.flags != SPICE_IMAGE_FLAGS_CACHE_ME &&
                draw_copy.data.src_bitmap.descriptor.flags != SPICE_IMAGE_FLAGS_HIGH_BITS_SET)
            {
                this.log_warn("FIXME: DrawCopy unhandled image flags: " + draw_copy.data.src_bitmap.descriptor.flags);
                DEBUG <= 1 && this.log_draw("DrawCopy", draw_copy);
            }

            if (draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_QUIC)
            {
                var canvas = this.surfaces[draw_copy.base.surface_id].canvas;
                if (! draw_copy.data.src_bitmap.quic)
                {
                    this.log_warn("FIXME: DrawCopy could not handle this QUIC file.");
                    return false;
                }
                var source_img = convert_spice_quic_to_web(canvas.context,
                                        draw_copy.data.src_bitmap.quic);

                return this.draw_copy_helper(
                    { base: draw_copy.base,
                      src_area: draw_copy.data.src_area,
                      image_data: source_img,
                      tag: "copyquic." + draw_copy.data.src_bitmap.quic.type,
                      has_alpha: (draw_copy.data.src_bitmap.quic.type == QUIC_IMAGE_TYPE_RGBA ? true : false) ,
                      descriptor : draw_copy.data.src_bitmap.descriptor
                    });
            }
            else if (draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_FROM_CACHE ||
                    draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_FROM_CACHE_LOSSLESS)
            {
                if (! this.cache || ! this.cache[draw_copy.data.src_bitmap.descriptor.id])
                {
                    this.log_warn("FIXME: DrawCopy did not find image id " + draw_copy.data.src_bitmap.descriptor.id + " in cache.");
                    return false;
                }

                return this.draw_copy_helper(
                    { base: draw_copy.base,
                      src_area: draw_copy.data.src_area,
                      image_data: this.cache[draw_copy.data.src_bitmap.descriptor.id],
                      tag: "copycache." + draw_copy.data.src_bitmap.descriptor.id, 
                      has_alpha: true, /* FIXME - may want this to be false... */
                      descriptor : draw_copy.data.src_bitmap.descriptor
                    });

                /* FIXME - LOSSLESS CACHE ramifications not understood or handled */
            }
            else if (draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_SURFACE)
            {
                var source_context = this.surfaces[draw_copy.data.src_bitmap.surface_id].canvas.context;
                var target_context = this.surfaces[draw_copy.base.surface_id].canvas.context;

                var source_img = source_context.getImageData(
                        draw_copy.data.src_area.left, draw_copy.data.src_area.top,
                        draw_copy.data.src_area.right - draw_copy.data.src_area.left,
                        draw_copy.data.src_area.bottom - draw_copy.data.src_area.top);
                var computed_src_area = new SpiceRect;
                computed_src_area.top = computed_src_area.left = 0;
                computed_src_area.right = source_img.width;
                computed_src_area.bottom = source_img.height;

                /* FIXME - there is a potential optimization here.
                           That is, if the surface is from 0,0, and
                           both surfaces are alpha surfaces, you should
                           be able to just do a drawImage, which should
                           save time.  */

                return this.draw_copy_helper(
                    { base: draw_copy.base,
                      src_area: computed_src_area,
                      image_data: source_img,
                      tag: "copysurf." + draw_copy.data.src_bitmap.surface_id,
                      has_alpha: this.surfaces[draw_copy.data.src_bitmap.surface_id].format == SPICE_SURFACE_FMT_32_xRGB ? false : true,
                      descriptor : draw_copy.data.src_bitmap.descriptor
                    });

                return true;
            }
            else if (draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_JPEG)
            {
                if (! draw_copy.data.src_bitmap.jpeg)
                {
                    this.log_warn("FIXME: DrawCopy could not handle this JPEG file.");
                    return false;
                }

                // FIXME - how lame is this.  Be have it in binary format, and we have
                //         to put it into string to get it back into jpeg.  Blech.
                var tmpstr = "data:image/jpeg,";
                var img = new Image;
                var i;
                var qdv = new Uint8Array(draw_copy.data.src_bitmap.jpeg.data);
                for (i = 0; i < qdv.length; i++)
                {
                    tmpstr +=  '%';
                    if (qdv[i] < 16)
                        tmpstr += '0';
                    tmpstr += qdv[i].toString(16);
                }

                img.o = 
                    { base: draw_copy.base,
                      tag: "jpeg." + draw_copy.data.src_bitmap.surface_id,
                      descriptor : draw_copy.data.src_bitmap.descriptor,
                      sc : this,
                    };
                img.onload = handle_draw_jpeg_onload;
                img.src = tmpstr;

                return true;
            }
            else if (draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_JPEG_ALPHA)
            {
                if (! draw_copy.data.src_bitmap.jpeg_alpha)
                {
                    this.log_warn("FIXME: DrawCopy could not handle this JPEG ALPHA file.");
                    return false;
                }

                // FIXME - how lame is this.  Be have it in binary format, and we have
                //         to put it into string to get it back into jpeg.  Blech.
                var tmpstr = "data:image/jpeg,";
                var img = new Image;
                var i;
                var qdv = new Uint8Array(draw_copy.data.src_bitmap.jpeg_alpha.data);
                for (i = 0; i < qdv.length; i++)
                {
                    tmpstr +=  '%';
                    if (qdv[i] < 16)
                        tmpstr += '0';
                    tmpstr += qdv[i].toString(16);
                }

                img.o = 
                    { base: draw_copy.base,
                      tag: "jpeg." + draw_copy.data.src_bitmap.surface_id,
                      descriptor : draw_copy.data.src_bitmap.descriptor,
                      sc : this,
                    };

                if (this.surfaces[draw_copy.base.surface_id].format == SPICE_SURFACE_FMT_32_ARGB)
                {

                    var canvas = this.surfaces[draw_copy.base.surface_id].canvas;
                    img.alpha_img = convert_spice_lz_to_web(canvas.context,
                                            draw_copy.data.src_bitmap.jpeg_alpha.alpha);
                }
                img.onload = handle_draw_jpeg_onload;
                img.src = tmpstr;

                return true;
            }
            else if (draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_BITMAP)
            {
                var canvas = this.surfaces[draw_copy.base.surface_id].canvas;
                if (! draw_copy.data.src_bitmap.bitmap)
                {
                    this.log_err("null bitmap");
                    return false;
                }

                var source_img = convert_spice_bitmap_to_web(canvas.context,
                                        draw_copy.data.src_bitmap.bitmap);
                if (! source_img)
                {
                    this.log_warn("FIXME: Unable to interpret bitmap of format: " + 
                        draw_copy.data.src_bitmap.bitmap.format);
                    return false;
                }

                return this.draw_copy_helper(
                    { base: draw_copy.base,
                      src_area: draw_copy.data.src_area,
                      image_data: source_img,
                      tag: "bitmap." + draw_copy.data.src_bitmap.bitmap.format,
                      has_alpha: draw_copy.data.src_bitmap.bitmap == SPICE_BITMAP_FMT_32BIT ? false : true,
                      descriptor : draw_copy.data.src_bitmap.descriptor
                    });
            }
            else if (draw_copy.data.src_bitmap.descriptor.type == SPICE_IMAGE_TYPE_LZ_RGB)
            {
                var canvas = this.surfaces[draw_copy.base.surface_id].canvas;
                if (! draw_copy.data.src_bitmap.lz_rgb)
                {
                    this.log_err("null lz_rgb ");
                    return false;
                }

                if (draw_copy.data.src_bitmap.lz_rgb.top_down != 1)
                    this.log_warn("FIXME: Implement non top down support for lz_rgb");

                var source_img = convert_spice_lz_to_web(canvas.context,
                                            draw_copy.data.src_bitmap.lz_rgb);
                if (! source_img)
                {
                    this.log_warn("FIXME: Unable to interpret bitmap of type: " + 
                        draw_copy.data.src_bitmap.lz_rgb.type);
                    return false;
                }

                return this.draw_copy_helper(
                    { base: draw_copy.base,
                      src_area: draw_copy.data.src_area,
                      image_data: source_img,
                      tag: "lz_rgb." + draw_copy.data.src_bitmap.lz_rgb.type,
                      has_alpha: draw_copy.data.src_bitmap.lz_rgb.type == LZ_IMAGE_TYPE_RGBA ? true : false ,
                      descriptor : draw_copy.data.src_bitmap.descriptor
                    });
            }
            else
            {
                this.log_warn("FIXME: DrawCopy unhandled image type: " + draw_copy.data.src_bitmap.descriptor.type);
                this.log_draw("DrawCopy", draw_copy);
                return false;
            }
        }

        this.log_warn("FIXME: DrawCopy no src_bitmap.");
        return false;
    }

    if (msg.type == SPICE_MSG_DISPLAY_DRAW_FILL)
    {
        var draw_fill = new SpiceMsgDisplayDrawFill(msg.data);

        DEBUG > 1 && this.log_draw("DrawFill", draw_fill);

        if (draw_fill.data.rop_descriptor != SPICE_ROPD_OP_PUT)
            this.log_warn("FIXME: DrawFill we don't handle ropd type: " + draw_fill.data.rop_descriptor);
        if (draw_fill.data.mask.flags)
            this.log_warn("FIXME: DrawFill we don't handle mask flag: " + draw_fill.data.mask.flags);
        if (draw_fill.data.mask.bitmap)
            this.log_warn("FIXME: DrawFill we don't handle mask");

        if (draw_fill.data.brush.type == SPICE_BRUSH_TYPE_SOLID)
        {
            // FIXME - do brushes ever have alpha?
            var color = draw_fill.data.brush.color & 0xffffff;
            var color_str = "rgb(" + (color >> 16) + ", " + ((color >> 8) & 0xff) + ", " + (color & 0xff) + ")";
            this.surfaces[draw_fill.base.surface_id].canvas.context.fillStyle = color_str;

            this.surfaces[draw_fill.base.surface_id].canvas.context.fillRect(
                draw_fill.base.box.left, draw_fill.base.box.top,
                draw_fill.base.box.right - draw_fill.base.box.left,
                draw_fill.base.box.bottom - draw_fill.base.box.top);

            if (DUMP_DRAWS && this.parent.dump_id)
            {
                var debug_canvas = document.createElement("canvas");
                debug_canvas.setAttribute('width', this.surfaces[draw_fill.base.surface_id].canvas.width);
                debug_canvas.setAttribute('height', this.surfaces[draw_fill.base.surface_id].canvas.height);
                debug_canvas.setAttribute('id', "fillbrush." + draw_fill.base.surface_id + "." + this.surfaces[draw_fill.base.surface_id].draw_count);
                debug_canvas.getContext("2d").fillStyle = color_str;
                debug_canvas.getContext("2d").fillRect(
                    draw_fill.base.box.left, draw_fill.base.box.top,
                    draw_fill.base.box.right - draw_fill.base.box.left,
                    draw_fill.base.box.bottom - draw_fill.base.box.top);
                document.getElementById(this.parent.dump_id).appendChild(debug_canvas);
            }
                
            this.surfaces[draw_fill.base.surface_id].draw_count++;

        }
        else
        {
            this.log_warn("FIXME: DrawFill can't handle brush type: " + draw_fill.data.brush.type);
        }
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_COPY_BITS)
    {
        var copy_bits = new SpiceMsgDisplayCopyBits(msg.data);

        DEBUG > 1 && this.log_draw("CopyBits", copy_bits);

        var source_canvas = this.surfaces[copy_bits.base.surface_id].canvas;
        var source_context = source_canvas.context;

        var width = source_canvas.width - copy_bits.src_pos.x;
        var height = source_canvas.height - copy_bits.src_pos.y;
        if (width > (copy_bits.base.box.right - copy_bits.base.box.left))
            width = copy_bits.base.box.right - copy_bits.base.box.left;
        if (height > (copy_bits.base.box.bottom - copy_bits.base.box.top))
            height = copy_bits.base.box.bottom - copy_bits.base.box.top;

        var source_img = source_context.getImageData(
                copy_bits.src_pos.x, copy_bits.src_pos.y, width, height);
        //source_context.putImageData(source_img, copy_bits.base.box.left, copy_bits.base.box.top);
        putImageDataWithAlpha(source_context, source_img, copy_bits.base.box.left, copy_bits.base.box.top);

        if (DUMP_DRAWS && this.parent.dump_id)
        {
            var debug_canvas = document.createElement("canvas");
            debug_canvas.setAttribute('width', width);
            debug_canvas.setAttribute('height', height);
            debug_canvas.setAttribute('id', "copybits" + copy_bits.base.surface_id + "." + this.surfaces[copy_bits.base.surface_id].draw_count);
            debug_canvas.getContext("2d").putImageData(source_img, 0, 0);
            document.getElementById(this.parent.dump_id).appendChild(debug_canvas);
        }


        this.surfaces[copy_bits.base.surface_id].draw_count++;
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_INVAL_ALL_PALETTES)
    {
        this.known_unimplemented(msg.type, "Inval All Palettes");
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_SURFACE_CREATE)
    {
        if (! ("surfaces" in this))
            this.surfaces = [];

        var m = new SpiceMsgSurfaceCreate(msg.data);
        DEBUG > 1 && console.log(this.type + ": MsgSurfaceCreate id " + m.surface.surface_id 
                                    + "; " + m.surface.width + "x" + m.surface.height
                                    + "; format " + m.surface.format 
                                    + "; flags " + m.surface.flags);
        if (m.surface.format != SPICE_SURFACE_FMT_32_xRGB &&
            m.surface.format != SPICE_SURFACE_FMT_32_ARGB)
        {
            this.log_warn("FIXME: cannot handle surface format " + m.surface.format + " yet.");
            return false;
        }

        var canvas = document.createElement("canvas");
        canvas.setAttribute('width', m.surface.width);
        canvas.setAttribute('height', m.surface.height);
        canvas.setAttribute('id', "spice_surface_" + m.surface.surface_id);
        canvas.setAttribute('tabindex', m.surface.surface_id);
        canvas.context = canvas.getContext("2d");

        if (DUMP_CANVASES && this.parent.dump_id)
            document.getElementById(this.parent.dump_id).appendChild(canvas);

        m.surface.canvas = canvas;
        m.surface.draw_count = 0;
        this.surfaces[m.surface.surface_id] = m.surface;

        if (m.surface.flags & SPICE_SURFACE_FLAGS_PRIMARY)
        {
            this.primary_surface = m.surface.surface_id;

            /* This .save() is done entirely to enable SPICE_MSG_DISPLAY_RESET */
            canvas.context.save();
            document.getElementById(this.parent.screen_id).appendChild(canvas);

            /* We're going to leave width dynamic, but correctly set the height */
            document.getElementById(this.parent.screen_id).style.height = m.surface.height + "px";
            this.hook_events();
        }
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_SURFACE_DESTROY)
    {
        var m = new SpiceMsgSurfaceDestroy(msg.data);
        DEBUG > 1 && console.log(this.type + ": MsgSurfaceDestroy id " + m.surface_id);
        this.delete_surface(m.surface_id);
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_STREAM_CREATE)
    {
        var m = new SpiceMsgDisplayStreamCreate(msg.data);
        DEBUG > 1 && console.log(this.type + ": MsgStreamCreate id" + m.id);
        if (!this.streams)
            this.streams = new Array();
        if (this.streams[m.id])
            console.log("Stream already exists");
        else
            this.streams[m.id] = m;
        if (m.codec_type != SPICE_VIDEO_CODEC_TYPE_MJPEG)
            console.log("Unhandled stream codec: "+m.codec_type);
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_STREAM_DATA)
    {
        var m = new SpiceMsgDisplayStreamData(msg.data);
        if (!this.streams[m.base.id])
        {
            console.log("no stream for data");
            return false;
        }
        if (this.streams[m.base.id].codec_type === SPICE_VIDEO_CODEC_TYPE_MJPEG)
        {
            var tmpstr = "data:image/jpeg,";
            var img = new Image;
            var i;
            for (i = 0; i < m.data.length; i++)
            {
                tmpstr +=  '%';
                if (m.data[i] < 16)
                tmpstr += '0';
                tmpstr += m.data[i].toString(16);
            }
            var strm_base = new SpiceMsgDisplayBase();
            strm_base.surface_id = this.streams[m.base.id].surface_id;
            strm_base.box = this.streams[m.base.id].dest;
            strm_base.clip = this.streams[m.base.id].clip;
            img.o =
                { base: strm_base,
                  tag: "mjpeg." + m.base.id,
                  descriptor: null,
                  sc : this,
                };
            img.onload = handle_draw_jpeg_onload;
            img.src = tmpstr;
        }
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_STREAM_CLIP)
    {
        var m = new SpiceMsgDisplayStreamClip(msg.data);
        DEBUG > 1 && console.log(this.type + ": MsgStreamClip id" + m.id);
        this.streams[m.id].clip = m.clip;
        return true;
    }

    if (msg.type == SPICE_MSG_DISPLAY_STREAM_DESTROY)
    {
        var m = new SpiceMsgDisplayStreamDestroy(msg.data);
        DEBUG > 1 && console.log(this.type + ": MsgStreamDestroy id" + m.id);
        this.streams[m.id] = undefined;
        return true;
    }
    if (msg.type == SPICE_MSG_DISPLAY_INVAL_LIST)
    {
        var m = new SpiceMsgDisplayInvalList(msg.data);
        var i;
        DEBUG > 1 && console.log(this.type + ": MsgInvalList " + m.count + " items");
        for (i = 0; i < m.count; i++)
            if (this.cache[m.resources[i].id] != undefined)
                delete this.cache[m.resources[i].id];
        return true;
    }

    return false;
}

SpiceDisplayConn.prototype.delete_surface = function(surface_id)
{
    var canvas = document.getElementById("spice_surface_" + surface_id);
    if (DUMP_CANVASES && this.parent.dump_id)
        document.getElementById(this.parent.dump_id).removeChild(canvas);
    if (this.primary_surface == surface_id)
    {
        this.unhook_events();
        this.primary_surface = undefined;
        document.getElementById(this.parent.screen_id).removeChild(canvas);
    }

    delete this.surfaces[surface_id];
}


SpiceDisplayConn.prototype.draw_copy_helper = function(o)
{

    var canvas = this.surfaces[o.base.surface_id].canvas;
    if (o.has_alpha)
    {
        /* FIXME - This is based on trial + error, not a serious thoughtful
                   analysis of what Spice requires.  See display.js for more. */
        if (this.surfaces[o.base.surface_id].format == SPICE_SURFACE_FMT_32_xRGB)
        {
            stripAlpha(o.image_data);
            canvas.context.putImageData(o.image_data, o.base.box.left, o.base.box.top);
        }
        else
            putImageDataWithAlpha(canvas.context, o.image_data,
                    o.base.box.left, o.base.box.top);
    }
    else
        canvas.context.putImageData(o.image_data, o.base.box.left, o.base.box.top);

    if (o.src_area.left > 0 || o.src_area.top > 0)
    {
        this.log_warn("FIXME: DrawCopy not shifting draw copies just yet...");
    }

    if (o.descriptor && (o.descriptor.flags & SPICE_IMAGE_FLAGS_CACHE_ME))
    {
        if (! ("cache" in this))
            this.cache = {};
        this.cache[o.descriptor.id] = o.image_data;
    }

    if (DUMP_DRAWS && this.parent.dump_id)
    {
        var debug_canvas = document.createElement("canvas");
        debug_canvas.setAttribute('width', o.image_data.width);
        debug_canvas.setAttribute('height', o.image_data.height);
        debug_canvas.setAttribute('id', o.tag + "." +
            this.surfaces[o.base.surface_id].draw_count + "." +
            o.base.surface_id + "@" + o.base.box.left + "x" +  o.base.box.top);
        debug_canvas.getContext("2d").putImageData(o.image_data, 0, 0);
        document.getElementById(this.parent.dump_id).appendChild(debug_canvas);
    }

    this.surfaces[o.base.surface_id].draw_count++;

    return true;
}


SpiceDisplayConn.prototype.log_draw = function(prefix, draw)
{
    var str = prefix + "." + draw.base.surface_id + "." + this.surfaces[draw.base.surface_id].draw_count + ": ";
    str += "base.box " + draw.base.box.left + ", " + draw.base.box.top + " to " + 
                           draw.base.box.right + ", " + draw.base.box.bottom;
    str += "; clip.type " + draw.base.clip.type;

    if (draw.data)
    {
        if (draw.data.src_area)
            str += "; src_area " + draw.data.src_area.left + ", " + draw.data.src_area.top + " to "
                                 + draw.data.src_area.right + ", " + draw.data.src_area.bottom;

        if (draw.data.src_bitmap && draw.data.src_bitmap != null)
        {
            str += "; src_bitmap id: " + draw.data.src_bitmap.descriptor.id;
            str += "; src_bitmap width " + draw.data.src_bitmap.descriptor.width + ", height " + draw.data.src_bitmap.descriptor.height;
            str += "; src_bitmap type " + draw.data.src_bitmap.descriptor.type + ", flags " + draw.data.src_bitmap.descriptor.flags;
            if (draw.data.src_bitmap.surface_id !== undefined)
                str += "; src_bitmap surface_id " + draw.data.src_bitmap.surface_id;
            if (draw.data.src_bitmap.quic)
                str += "; QUIC type " + draw.data.src_bitmap.quic.type + 
                        "; width " + draw.data.src_bitmap.quic.width + 
                        "; height " + draw.data.src_bitmap.quic.height ;
            if (draw.data.src_bitmap.lz_rgb)
                str += "; LZ_RGB length " + draw.data.src_bitmap.lz_rgb.length +
                       "; magic " + draw.data.src_bitmap.lz_rgb.magic + 
                       "; version 0x" + draw.data.src_bitmap.lz_rgb.version.toString(16) +
                       "; type " + draw.data.src_bitmap.lz_rgb.type +
                       "; width " + draw.data.src_bitmap.lz_rgb.width +
                       "; height " + draw.data.src_bitmap.lz_rgb.height +
                       "; stride " + draw.data.src_bitmap.lz_rgb.stride +
                       "; top down " + draw.data.src_bitmap.lz_rgb.top_down;
        }
        else
            str += "; src_bitmap is null";

        if (draw.data.brush)
        {
            if (draw.data.brush.type == SPICE_BRUSH_TYPE_SOLID)
                str += "; brush.color 0x" + draw.data.brush.color.toString(16);
            if (draw.data.brush.type == SPICE_BRUSH_TYPE_PATTERN)
            {
                str += "; brush.pat ";
                if (draw.data.brush.pattern.pat != null)
                    str += "[SpiceImage]";
                else
                    str += "[null]";
                str += " at " + draw.data.brush.pattern.pos.x + ", " + draw.data.brush.pattern.pos.y;
            }
        }

        str += "; rop_descriptor " + draw.data.rop_descriptor;
        if (draw.data.scale_mode !== undefined)
            str += "; scale_mode " + draw.data.scale_mode;
        str += "; mask.flags " + draw.data.mask.flags;
        str += "; mask.pos " + draw.data.mask.pos.x + ", " + draw.data.mask.pos.y;
        if (draw.data.mask.bitmap != null)
        {
            str += "; mask.bitmap width " + draw.data.mask.bitmap.descriptor.width + ", height " + draw.data.mask.bitmap.descriptor.height;
            str += "; mask.bitmap type " + draw.data.mask.bitmap.descriptor.type + ", flags " + draw.data.mask.bitmap.descriptor.flags;
        }
        else
            str += "; mask.bitmap is null";
    }

    console.log(str);
}

SpiceDisplayConn.prototype.hook_events = function()
{
    if (this.primary_surface !== undefined)
    {
        var canvas = this.surfaces[this.primary_surface].canvas;
        canvas.sc = this.parent;
        canvas.addEventListener('mousemove', handle_mousemove);
        canvas.addEventListener('mousedown', handle_mousedown);
        canvas.addEventListener('contextmenu', handle_contextmenu);
        canvas.addEventListener('mouseup', handle_mouseup);
        canvas.addEventListener('keydown', handle_keydown);
        canvas.addEventListener('keyup', handle_keyup);
        canvas.addEventListener('mouseout', handle_mouseout);
        canvas.addEventListener('mouseover', handle_mouseover);
        canvas.addEventListener('mousewheel', handle_mousewheel);
        canvas.focus();
    }
}

SpiceDisplayConn.prototype.unhook_events = function()
{
    if (this.primary_surface !== undefined)
    {
        var canvas = this.surfaces[this.primary_surface].canvas;
        canvas.removeEventListener('mousemove', handle_mousemove);
        canvas.removeEventListener('mousedown', handle_mousedown);
        canvas.removeEventListener('contextmenu', handle_contextmenu);
        canvas.removeEventListener('mouseup', handle_mouseup);
        canvas.removeEventListener('keydown', handle_keydown);
        canvas.removeEventListener('keyup', handle_keyup);
        canvas.removeEventListener('mouseout', handle_mouseout);
        canvas.removeEventListener('mouseover', handle_mouseover);
        canvas.removeEventListener('mousewheel', handle_mousewheel);
    }
}


SpiceDisplayConn.prototype.destroy_surfaces = function()
{
    for (var s in this.surfaces)
    {
        this.delete_surface(this.surfaces[s].surface_id);
    }

    this.surfaces = undefined;
}


function handle_mouseover(e)
{
    this.focus();
}

function handle_mouseout(e)
{
    if (this.sc && this.sc.cursor && this.sc.cursor.spice_simulated_cursor)
        this.sc.cursor.spice_simulated_cursor.style.display = 'none';
    this.blur();
}

function handle_draw_jpeg_onload()
{
    var temp_canvas = null;
    var context;

    /*------------------------------------------------------------
    ** FIXME:
    **  The helper should be extended to be able to handle actual HtmlImageElements
    **  ...and the cache should be modified to do so as well
    **----------------------------------------------------------*/
    if (this.o.sc.surfaces[this.o.base.surface_id] === undefined)
    {
        // This can happen; if the jpeg image loads after our surface
        //  has been destroyed (e.g. open a menu, close it quickly),
        //  we'll find we have no surface.  
        DEBUG > 2 && this.o.sc.log_info("Discarding jpeg; presumed lost surface " + this.o.base.surface_id);
        temp_canvas = document.createElement("canvas");
        temp_canvas.setAttribute('width', this.o.base.box.right);
        temp_canvas.setAttribute('height', this.o.base.box.bottom);
        context = temp_canvas.getContext("2d");
    }
    else
        context = this.o.sc.surfaces[this.o.base.surface_id].canvas.context;

    if (this.alpha_img)
    {
        var c = document.createElement("canvas");
        var t = c.getContext("2d");
        c.setAttribute('width', this.alpha_img.width);
        c.setAttribute('height', this.alpha_img.height);
        t.putImageData(this.alpha_img, 0, 0);
        t.globalCompositeOperation = 'source-in';
        t.drawImage(this, 0, 0);
     
        context.drawImage(c, this.o.base.box.left, this.o.base.box.top);

        if (this.o.descriptor && 
            (this.o.descriptor.flags & SPICE_IMAGE_FLAGS_CACHE_ME))
        {
            if (! ("cache" in this.o.sc))
                this.o.sc.cache = {};

            this.o.sc.cache[this.o.descriptor.id] = 
                t.getImageData(0, 0,
                    this.alpha_img.width,
                    this.alpha_img.height);
        }
    }
    else
    {
        context.drawImage(this, this.o.base.box.left, this.o.base.box.top);

        // Give the Garbage collector a clue to recycle this; avoids
        //  fairly massive memory leaks during video playback
        this.src = null;

        if (this.o.descriptor && 
            (this.o.descriptor.flags & SPICE_IMAGE_FLAGS_CACHE_ME))
        {
            if (! ("cache" in this.o.sc))
                this.o.sc.cache = {};

            this.o.sc.cache[this.o.descriptor.id] = 
                context.getImageData(this.o.base.box.left, this.o.base.box.top,
                    this.o.base.box.right - this.o.base.box.left,
                    this.o.base.box.bottom - this.o.base.box.top);
        }
    }

    if (temp_canvas == null)
    {
        if (DUMP_DRAWS && this.o.sc.parent.dump_id)
        {
            var debug_canvas = document.createElement("canvas");
            debug_canvas.setAttribute('id', this.o.tag + "." +
                this.o.sc.surfaces[this.o.base.surface_id].draw_count + "." +
                this.o.base.surface_id + "@" + this.o.base.box.left + "x" +  this.o.base.box.top);
            debug_canvas.getContext("2d").drawImage(this, 0, 0);
            document.getElementById(this.o.sc.parent.dump_id).appendChild(debug_canvas);
        }

        this.o.sc.surfaces[this.o.base.surface_id].draw_count++;
    }
}
