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
**  bitmap.js
**      Handle SPICE_IMAGE_TYPE_BITMAP
**--------------------------------------------------------------------------*/
function convert_spice_bitmap_to_web(context, spice_bitmap)
{
    var ret;
    var offset, x;
    var u8 = new Uint8Array(spice_bitmap.data);
    if (spice_bitmap.format != SPICE_BITMAP_FMT_32BIT &&
        spice_bitmap.format != SPICE_BITMAP_FMT_RGBA)
        return undefined;

    ret = context.createImageData(spice_bitmap.x, spice_bitmap.y);
    for (offset = 0; offset < (spice_bitmap.y * spice_bitmap.stride); )
        for (x = 0; x < spice_bitmap.x; x++, offset += 4)
        {
            ret.data[offset + 0 ] = u8[offset + 2];
            ret.data[offset + 1 ] = u8[offset + 1];
            ret.data[offset + 2 ] = u8[offset + 0];

            // FIXME - We effectively treat all images as having SPICE_IMAGE_FLAGS_HIGH_BITS_SET
            if (spice_bitmap.format == SPICE_BITMAP_FMT_32BIT)
                ret.data[offset + 3] = 255;
            else
                ret.data[offset + 3] = u8[offset];
        }

    return ret;
}
