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
**  lz.js
**      Functions for handling SPICE_IMAGE_TYPE_LZ_RGB
**  Adapted from lz.c .
**--------------------------------------------------------------------------*/
function lz_rgb32_decompress(in_buf, at, out_buf, type, default_alpha)
{
    var encoder = at;
    var op = 0;
    var ctrl;
    var ctr = 0;

    for (ctrl = in_buf[encoder++]; (op * 4) < out_buf.length; ctrl = in_buf[encoder++])
    {
        var ref = op;
        var len = ctrl >> 5;
        var ofs = (ctrl & 31) << 8;

//if (type == LZ_IMAGE_TYPE_RGBA)
//console.log(ctr++ + ": from " + (encoder + 28) + ", ctrl " + ctrl + ", len " + len + ", ofs " + ofs + ", op " + op);
        if (ctrl >= 32) {

            var code;
            len--;

            if (len == 7 - 1) {
                do {
                    code = in_buf[encoder++];
                    len += code;
                } while (code == 255);
            }
            code = in_buf[encoder++];
            ofs += code;


            if (code == 255) {
                if ((ofs - code) == (31 << 8)) {
                    ofs = in_buf[encoder++] << 8;
                    ofs += in_buf[encoder++];
                    ofs += 8191;
                }
            }
            len += 1;
            if (type == LZ_IMAGE_TYPE_RGBA)
                len += 2;

            ofs += 1;

            ref -= ofs;
            if (ref == (op - 1)) {
                var b = ref;
//if (type == LZ_IMAGE_TYPE_RGBA) console.log("alpha " + out_buf[(b*4)+3] + " dupped into pixel " + op + " through pixel " + (op + len));
                for (; len; --len) {
                    if (type == LZ_IMAGE_TYPE_RGBA)
                    {
                        out_buf[(op*4) + 3] = out_buf[(b*4)+3];
                    }
                    else
                    {
                        for (i = 0; i < 4; i++)
                            out_buf[(op*4) + i] = out_buf[(b*4)+i];
                    }
                    op++;
                }
            } else {
//if (type == LZ_IMAGE_TYPE_RGBA) console.log("alpha copied to pixel " + op + " through " + (op + len) + " from " + ref);
                for (; len; --len) {
                    if (type == LZ_IMAGE_TYPE_RGBA)
                    {
                        out_buf[(op*4) + 3] = out_buf[(ref*4)+3];
                    }
                    else
                    {
                        for (i = 0; i < 4; i++)
                            out_buf[(op*4) + i] = out_buf[(ref*4)+i];
                    }
                    op++; ref++;
                }
            }
        } else {
            ctrl++;

            if (type == LZ_IMAGE_TYPE_RGBA)
            {
//console.log("alpha " + in_buf[encoder] + " set into pixel " + op);
                out_buf[(op*4) + 3] = in_buf[encoder++];
            }
            else
            {
                out_buf[(op*4) + 0] = in_buf[encoder + 2];
                out_buf[(op*4) + 1] = in_buf[encoder + 1];
                out_buf[(op*4) + 2] = in_buf[encoder + 0];
                if (default_alpha)
                    out_buf[(op*4) + 3] = 255;
                encoder += 3;
            }
            op++;


            for (--ctrl; ctrl; ctrl--) {
                if (type == LZ_IMAGE_TYPE_RGBA)
                {
//console.log("alpha " + in_buf[encoder] + " set into pixel " + op);
                    out_buf[(op*4) + 3] = in_buf[encoder++];
                }
                else
                {
                    out_buf[(op*4) + 0] = in_buf[encoder + 2];
                    out_buf[(op*4) + 1] = in_buf[encoder + 1];
                    out_buf[(op*4) + 2] = in_buf[encoder + 0];
                    if (default_alpha)
                        out_buf[(op*4) + 3] = 255;
                    encoder += 3;
                }
                op++;
            }
        }

    }
    return encoder - 1;
}

function convert_spice_lz_to_web(context, lz_image)
{
    var at;
    if (lz_image.type === LZ_IMAGE_TYPE_RGB32 || lz_image.type === LZ_IMAGE_TYPE_RGBA)
    {
        var u8 = new Uint8Array(lz_image.data);
        var ret = context.createImageData(lz_image.width, lz_image.height);

        at = lz_rgb32_decompress(u8, 0, ret.data, LZ_IMAGE_TYPE_RGB32, lz_image.type != LZ_IMAGE_TYPE_RGBA);
        if (lz_image.type == LZ_IMAGE_TYPE_RGBA)
            lz_rgb32_decompress(u8, at, ret.data, LZ_IMAGE_TYPE_RGBA, false);
    }
    else if (lz_image.type === LZ_IMAGE_TYPE_XXXA)
    {
        var u8 = new Uint8Array(lz_image.data);
        var ret = context.createImageData(lz_image.width, lz_image.height);
        lz_rgb32_decompress(u8, 0, ret.data, LZ_IMAGE_TYPE_RGBA, false);
    }
    else
        return undefined;

    return ret;
}
