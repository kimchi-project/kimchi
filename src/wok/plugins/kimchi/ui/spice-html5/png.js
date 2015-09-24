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
**  crc logic from rfc2083 ported to Javascript
**--------------------------------------------------------------------------*/

var rfc2083_crc_table = Array(256);
var rfc2083_crc_table_computed = 0;
/* Make the table for a fast CRC. */
function rfc2083_make_crc_table()
{
    var c;
    var n, k;
    for (n = 0; n < 256; n++)
    {
        c = n;
        for (k = 0; k < 8; k++)
        {
            if (c & 1)
                c = ((0xedb88320 ^ (c >>> 1)) >>> 0) & 0xffffffff;
            else
                c = c >>> 1;
        }
        rfc2083_crc_table[n] = c;
    }

    rfc2083_crc_table_computed = 1;
}

/* Update a running CRC with the bytes buf[0..len-1]--the CRC
     should be initialized to all 1's, and the transmitted value
     is the 1's complement of the final running CRC (see the
     crc() routine below)). */

function rfc2083_update_crc(crc, u8buf, at, len)
{
    var c = crc;
    var n;

    if (!rfc2083_crc_table_computed)
        rfc2083_make_crc_table();

    for (n = 0; n < len; n++)
    {
        c = rfc2083_crc_table[(c ^ u8buf[at + n]) & 0xff] ^ (c >>> 8);
    }

    return c;
}

function rfc2083_crc(u8buf, at, len)
{
    return rfc2083_update_crc(0xffffffff, u8buf, at, len) ^ 0xffffffff;
}

function crc32(mb, at, len)
{
    var u8 = new Uint8Array(mb);
    return rfc2083_crc(u8, at, len);
}

function PngIHDR(width, height)
{
    this.width = width;
    this.height = height;
    this.depth = 8;
    this.type = 6;
    this.compression = 0;
    this.filter = 0;
    this.interlace = 0;
}

PngIHDR.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var orig = at;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.buffer_size() - 12); at += 4;
        dv.setUint8(at, 'I'.charCodeAt(0)); at++;
        dv.setUint8(at, 'H'.charCodeAt(0)); at++;
        dv.setUint8(at, 'D'.charCodeAt(0)); at++;
        dv.setUint8(at, 'R'.charCodeAt(0)); at++;
        dv.setUint32(at, this.width); at += 4;
        dv.setUint32(at, this.height); at += 4;
        dv.setUint8(at, this.depth); at++;
        dv.setUint8(at, this.type); at++;
        dv.setUint8(at, this.compression); at++;
        dv.setUint8(at, this.filter); at++;
        dv.setUint8(at, this.interlace); at++;
        dv.setUint32(at, crc32(a, orig + 4, this.buffer_size() - 8)); at += 4;
        return at;
    },
    buffer_size: function()
    {
        return 12 + 13;
    }
}


function adler()
{
    this.s1 = 1;
    this.s2 = 0;
}

adler.prototype.update = function(b)
{
    this.s1 += b;
    this.s1 %= 65521;
    this.s2 += this.s1;
    this.s2 %= 65521;
}

function PngIDAT(width, height, bytes)
{
    if (bytes.byteLength > 65535)
    {
        throw new Error("Cannot handle more than 64K");
    }
    this.data = bytes;
    this.width = width;
    this.height = height;
}

PngIDAT.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var orig = at;
        var x, y, i, j;
        var dv = new SpiceDataView(a);
        var zsum = new adler();
        dv.setUint32(at, this.buffer_size() - 12); at += 4;
        dv.setUint8(at, 'I'.charCodeAt(0)); at++;
        dv.setUint8(at, 'D'.charCodeAt(0)); at++;
        dv.setUint8(at, 'A'.charCodeAt(0)); at++;
        dv.setUint8(at, 'T'.charCodeAt(0)); at++;

        /* zlib header.  */
        dv.setUint8(at, 0x78); at++;
        dv.setUint8(at, 0x01); at++;

        /* Deflate header.  Specifies uncompressed, final bit */
        dv.setUint8(at, 0x80); at++;
        dv.setUint16(at, this.data.byteLength + this.height); at += 2;
        dv.setUint16(at, ~(this.data.byteLength + this.height)); at += 2;
        var u8 = new Uint8Array(this.data);
        for (i = 0, y = 0; y < this.height; y++)
        {
            /* Filter type 0 - uncompressed */
            dv.setUint8(at, 0); at++;
            zsum.update(0);
            for (x = 0; x < this.width && i < this.data.byteLength; x++)
            {
                zsum.update(u8[i]);
                dv.setUint8(at, u8[i++]); at++;
                zsum.update(u8[i]);
                dv.setUint8(at, u8[i++]); at++;
                zsum.update(u8[i]);
                dv.setUint8(at, u8[i++]); at++;
                zsum.update(u8[i]);
                dv.setUint8(at, u8[i++]); at++;
            }
        }

        /* zlib checksum.   */
        dv.setUint16(at, zsum.s2); at+=2;
        dv.setUint16(at, zsum.s1); at+=2;

        /* FIXME - something is not quite right with the zlib code;
                   you get an error from libpng if you open the image in
                   gimp.  But it works, so it's good enough for now... */

        dv.setUint32(at, crc32(a, orig + 4, this.buffer_size() - 8)); at += 4;
        return at;
    },
    buffer_size: function()
    {
        return 12 + this.data.byteLength + this.height + 4 + 2 + 1 + 2 + 2;
    }
}


function PngIEND()
{
}

PngIEND.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var orig = at;
        var i;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.buffer_size() - 12); at += 4;
        dv.setUint8(at, 'I'.charCodeAt(0)); at++;
        dv.setUint8(at, 'E'.charCodeAt(0)); at++;
        dv.setUint8(at, 'N'.charCodeAt(0)); at++;
        dv.setUint8(at, 'D'.charCodeAt(0)); at++;
        dv.setUint32(at, crc32(a, orig + 4, this.buffer_size() - 8)); at += 4;
        return at;
    },
    buffer_size: function()
    {
        return 12;
    }
}


function create_rgba_png(width, height, bytes)
{
    var i;
    var ihdr = new PngIHDR(width, height);
    var idat = new PngIDAT(width, height, bytes);
    var iend = new PngIEND;

    var mb = new ArrayBuffer(ihdr.buffer_size() + idat.buffer_size() + iend.buffer_size());
    var at = ihdr.to_buffer(mb);
    at = idat.to_buffer(mb, at);
    at = iend.to_buffer(mb, at);

    var u8 = new Uint8Array(mb);
    var str = "";
    for (i = 0; i < at; i++)
    {
        str += "%";
        if (u8[i] < 16)
            str += "0";
        str += u8[i].toString(16);
    }


    return "%89PNG%0D%0A%1A%0A" + str;
}
