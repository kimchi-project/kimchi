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
**  SpiceArrayBufferSlice
**    This function is a work around for IE 10, which has no slice()
**    method in it's subclass.
**--------------------------------------------------------------------------*/
function SpiceArrayBufferSlice(start, end)
{
    start = start || 0;
    end = end || this.byteLength;
    if (end < 0)
        end = this.byteLength + end;
    if (start < 0)
        start = this.byteLength + start;
    if (start < 0)
        start = 0;
    if (end < 0)
        end = 0;
    if (end > this.byteLength)
        end = this.byteLength;
    if (start > end)
        start = end;

    var ret = new ArrayBuffer(end - start);
    var in1 = new Uint8Array(this, start, end - start);
    var out = new Uint8Array(ret);
    var i;

    for (i = 0; i < end - start; i++)
        out[i] = in1[i];

    return ret;
}

if (! ArrayBuffer.prototype.slice)
{
    ArrayBuffer.prototype.slice = SpiceArrayBufferSlice;
    console.log("WARNING:  ArrayBuffer.slice() is missing; we are extending ArrayBuffer to compensate");
}
