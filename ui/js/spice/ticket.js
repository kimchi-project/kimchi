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

var SHA_DIGEST_LENGTH = 20;

/*----------------------------------------------------------------------------
**  General ticket RSA encryption functions - just good enough to
**      support what we need to send back an encrypted ticket.
**--------------------------------------------------------------------------*/


/*----------------------------------------------------------------------------
**  OAEP padding functions.  Inspired by the OpenSSL implementation.
**--------------------------------------------------------------------------*/
function MGF1(mask, seed)
{
    var i, j, outlen;
    for (i = 0, outlen = 0; outlen < mask.length; i++)
    {
        var combo_buf = new String;

        for (j = 0; j < seed.length; j++)
            combo_buf += String.fromCharCode(seed[j]);
        combo_buf += String.fromCharCode((i >> 24) & 255);
        combo_buf += String.fromCharCode((i >> 16) & 255);
        combo_buf += String.fromCharCode((i >> 8)  & 255);
        combo_buf += String.fromCharCode((i)       & 255);

        var combo_hash = rstr_sha1(combo_buf);
        for (j = 0; j < combo_hash.length && outlen < mask.length; j++, outlen++)
        {
            mask[outlen] = combo_hash.charCodeAt(j);
        }
    }
}


function RSA_padding_add_PKCS1_OAEP(tolen, from, param)
{
    var seed = new Array(SHA_DIGEST_LENGTH);
    var rand = new SecureRandom();
    rand.nextBytes(seed);

    var dblen = tolen - 1 - seed.length;
    var db = new Array(dblen);
    var padlen = dblen - from.length - 1;
    var i;

    if (param === undefined)
        param = "";

    if (padlen < SHA_DIGEST_LENGTH)
    {
        console.log("Error - data too large for key size.");
        return null;
    }

    for (i = 0; i < padlen; i++)
        db[i] = 0;

    var param_hash = rstr_sha1(param);
    for (i = 0; i < param_hash.length; i++)
        db[i] = param_hash.charCodeAt(i);

    db[padlen] = 1;
    for (i = 0; i < from.length; i++)
        db[i + padlen + 1] = from.charCodeAt(i);

    var dbmask = new Array(dblen);
    if (MGF1(dbmask, seed) < 0)
            return null;

    for (i = 0; i < dbmask.length; i++)
        db[i] ^= dbmask[i];


    var seedmask = Array(SHA_DIGEST_LENGTH);
    if (MGF1(seedmask, db) < 0)
            return null;

    for (i = 0; i < seedmask.length; i++)
        seed[i] ^= seedmask[i];

    var ret = new String;
    ret += String.fromCharCode(0);
    for (i = 0; i < seed.length; i++)
        ret += String.fromCharCode(seed[i]);
    for (i = 0; i < db.length; i++)
        ret += String.fromCharCode(db[i]);
    return ret;
}


function asn_get_length(u8, at)
{
    var len = u8[at++];
    if (len > 0x80)
    {
        if (len != 0x81)
        {
            console.log("Error:  we lazily don't support keys bigger than 255 bytes.  It'd be easy to fix.");
            return null;
        }
        len = u8[at++];
    }

    return [ at, len];
}

function find_sequence(u8, at)
{
    var lenblock;
    at = at || 0;
    if (u8[at++] != 0x30)
    {
        console.log("Error:  public key should start with a sequence flag.");
        return null;
    }

    lenblock = asn_get_length(u8, at);
    if (! lenblock)
        return null;
    return lenblock;
}

/*----------------------------------------------------------------------------
**  Extract an RSA key from a memory buffer
**--------------------------------------------------------------------------*/
function create_rsa_from_mb(mb, at)
{
    var u8 = new Uint8Array(mb);
    var lenblock;
    var seq;
    var ba;
    var i;
    var ret;

    /* We have a sequence which contains a sequence followed by a bit string */
    seq = find_sequence(u8, at);
    if (! seq)
        return null;

    at = seq[0];
    seq = find_sequence(u8, at);
    if (! seq)
        return null;

    /* Skip over the contained sequence */
    at = seq[0] + seq[1];
    if (u8[at++] != 0x3)
    {
        console.log("Error: expecting bit string next.");
        return null;
    }

    /* Get the bit string, which is *itself* a sequence.  Having fun yet? */
    lenblock = asn_get_length(u8, at);
    if (! lenblock)
        return null;

    at = lenblock[0];
    if (u8[at] != 0 && u8[at + 1] != 0x30)
    {
        console.log("Error: unexpected values in bit string.");
        return null;
    }

    /* Okay, now we have a sequence of two binary values, we hope. */
    seq = find_sequence(u8, at + 1);
    if (! seq)
        return null;

    at = seq[0];
    if (u8[at++] != 0x02)
    {
        console.log("Error: expecting integer n next.");
        return null;
    }
    lenblock = asn_get_length(u8, at);
    if (! lenblock)
        return null;
    at = lenblock[0];

    ba = new Array(lenblock[1]);
    for (i = 0; i < lenblock[1]; i++)
        ba[i] = u8[at + i];

    ret = new RSAKey();
    ret.n = new BigInteger(ba);

    at += lenblock[1];

    if (u8[at++] != 0x02)
    {
        console.log("Error: expecting integer e next.");
        return null;
    }
    lenblock = asn_get_length(u8, at);
    if (! lenblock)
        return null;
    at = lenblock[0];

    ret.e = u8[at++];
    for (i = 1; i < lenblock[1]; i++)
    {
        ret.e <<= 8;
        ret.e |= u8[at++];
    }

    return ret;
}

function rsa_encrypt(rsa, str)
{
    var i;
    var ret = [];
    var oaep = RSA_padding_add_PKCS1_OAEP((rsa.n.bitLength()+7)>>3, str);
    if (! oaep)
        return null;

    var ba = new Array(oaep.length);

    for (i = 0; i < oaep.length; i++)
        ba[i] = oaep.charCodeAt(i);
    var bigint = new BigInteger(ba);
    var enc = rsa.doPublic(bigint);
    var h = enc.toString(16);
    if ((h.length & 1) != 0)
        h = "0" + h;
    for (i = 0; i < h.length; i += 2)
        ret[i / 2] = parseInt(h.substring(i, i + 2), 16);
    return ret;
}
