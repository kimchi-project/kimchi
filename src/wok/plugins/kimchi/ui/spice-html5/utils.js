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
**  Utility settings and functions for Spice
**--------------------------------------------------------------------------*/
var DEBUG = 0;
var DUMP_DRAWS = false;
var DUMP_CANVASES = false;


/*----------------------------------------------------------------------------
**  combine_array_buffers
**      Combine two array buffers.
**      FIXME - this can't be optimal.  See wire.js about eliminating the need.
**--------------------------------------------------------------------------*/
function combine_array_buffers(a1, a2)
{
    var in1 = new Uint8Array(a1);
    var in2 = new Uint8Array(a2);
    var ret = new ArrayBuffer(a1.byteLength + a2.byteLength);
    var out = new Uint8Array(ret);
    var o = 0;
    var i;
    for (i = 0; i < in1.length; i++)
        out[o++] = in1[i];
    for (i = 0; i < in2.length; i++)
        out[o++] = in2[i];

    return ret;
}

/*----------------------------------------------------------------------------
**  hexdump_buffer
**--------------------------------------------------------------------------*/
function hexdump_buffer(a)
{
    var mg = new Uint8Array(a);
    var hex = "";
    var str = "";
    var last_zeros = 0;
    for (var i = 0; i < mg.length; i++)
    {
        var h = Number(mg[i]).toString(16);
        if (h.length == 1)
            hex += "0";
        hex += h + " ";

        if (mg[i] == 10 || mg[i] == 13 || mg[i] == 8)
            str += ".";
        else
            str += String.fromCharCode(mg[i]);

        if ((i % 16 == 15) || (i == (mg.length - 1)))
        {
            while (i % 16 != 15)
            {
                hex += "   ";
                i++;
            }

            if (last_zeros == 0)
                console.log(hex + " | " + str);

            if (hex == "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ")
            {
                if (last_zeros == 1)
                {
                    console.log(".");
                    last_zeros++;
                }
                else if (last_zeros == 0)
                    last_zeros++;
            }
            else
                last_zeros = 0;

            hex = str = "";
        }
    }
}

/*----------------------------------------------------------------------------
** Converting keycodes to AT scancodes is very hard.
** luckly there are some resources on the web and in the Xorg driver that help
** us figure out what browser depenend keycodes match to what scancodes.
**
** This will most likely not work for non US keyboard and browsers other than
** modern Chrome and FireFox.
**--------------------------------------------------------------------------*/
var common_scanmap = [];
common_scanmap['Q'.charCodeAt(0)]  = KEY_Q;
common_scanmap['W'.charCodeAt(0)]  = KEY_W;
common_scanmap['E'.charCodeAt(0)]  = KEY_E;
common_scanmap['R'.charCodeAt(0)]  = KEY_R;
common_scanmap['T'.charCodeAt(0)]  = KEY_T;
common_scanmap['Y'.charCodeAt(0)]  = KEY_Y;
common_scanmap['U'.charCodeAt(0)]  = KEY_U;
common_scanmap['I'.charCodeAt(0)]  = KEY_I;
common_scanmap['O'.charCodeAt(0)]  = KEY_O;
common_scanmap['P'.charCodeAt(0)]  = KEY_P;
common_scanmap['A'.charCodeAt(0)]  = KEY_A;
common_scanmap['S'.charCodeAt(0)]  = KEY_S;
common_scanmap['D'.charCodeAt(0)]  = KEY_D;
common_scanmap['F'.charCodeAt(0)]  = KEY_F;
common_scanmap['G'.charCodeAt(0)]  = KEY_G;
common_scanmap['H'.charCodeAt(0)]  = KEY_H;
common_scanmap['J'.charCodeAt(0)]  = KEY_J;
common_scanmap['K'.charCodeAt(0)]  = KEY_K;
common_scanmap['L'.charCodeAt(0)]  = KEY_L;
common_scanmap['Z'.charCodeAt(0)]  = KEY_Z;
common_scanmap['X'.charCodeAt(0)]  = KEY_X;
common_scanmap['C'.charCodeAt(0)]  = KEY_C;
common_scanmap['V'.charCodeAt(0)]  = KEY_V;
common_scanmap['B'.charCodeAt(0)]  = KEY_B;
common_scanmap['N'.charCodeAt(0)]  = KEY_N;
common_scanmap['M'.charCodeAt(0)]  = KEY_M;
common_scanmap[' '.charCodeAt(0)]  = KEY_Space;
common_scanmap[13]                 = KEY_Enter;
common_scanmap[27]                 = KEY_Escape;
common_scanmap[8]                  = KEY_BackSpace;
common_scanmap[9]                  = KEY_Tab;
common_scanmap[16]                 = KEY_ShiftL;
common_scanmap[17]                 = KEY_LCtrl;
common_scanmap[18]                 = KEY_Alt;
common_scanmap[20]                 = KEY_CapsLock;
common_scanmap[144]                = KEY_NumLock;
common_scanmap[112]                = KEY_F1;
common_scanmap[113]                = KEY_F2;
common_scanmap[114]                = KEY_F3;
common_scanmap[115]                = KEY_F4;
common_scanmap[116]                = KEY_F5;
common_scanmap[117]                = KEY_F6;
common_scanmap[118]                = KEY_F7;
common_scanmap[119]                = KEY_F8;
common_scanmap[120]                = KEY_F9;
common_scanmap[121]                = KEY_F10;
common_scanmap[122]                = KEY_F11;
common_scanmap[123]                = KEY_F12;

/* These externded scancodes do not line up with values from atKeynames */
common_scanmap[42]                 = 99;
common_scanmap[19]                 = 101;    // Break
common_scanmap[111]                = 0xE035; // KP_Divide
common_scanmap[106]                = 0xE037; // KP_Multiply
common_scanmap[36]                 = 0xE047; // Home
common_scanmap[38]                 = 0xE048; // Up
common_scanmap[33]                 = 0xE049; // PgUp
common_scanmap[37]                 = 0xE04B; // Left
common_scanmap[39]                 = 0xE04D; // Right
common_scanmap[35]                 = 0xE04F; // End
common_scanmap[40]                 = 0xE050; // Down
common_scanmap[34]                 = 0xE051; // PgDown
common_scanmap[45]                 = 0xE052; // Insert
common_scanmap[46]                 = 0xE053; // Delete
common_scanmap[44]                 = 0x2A37; // Print

/* These are not common between ALL browsers but are between Firefox and DOM3 */
common_scanmap['1'.charCodeAt(0)]  = KEY_1;
common_scanmap['2'.charCodeAt(0)]  = KEY_2;
common_scanmap['3'.charCodeAt(0)]  = KEY_3;
common_scanmap['4'.charCodeAt(0)]  = KEY_4;
common_scanmap['5'.charCodeAt(0)]  = KEY_5;
common_scanmap['6'.charCodeAt(0)]  = KEY_6;
common_scanmap['7'.charCodeAt(0)]  = KEY_7;
common_scanmap['8'.charCodeAt(0)]  = KEY_8;
common_scanmap['9'.charCodeAt(0)]  = KEY_9;
common_scanmap['0'.charCodeAt(0)]  = KEY_0;
common_scanmap[145]                = KEY_ScrollLock;
common_scanmap[103]                = KEY_KP_7;
common_scanmap[104]                = KEY_KP_8;
common_scanmap[105]                = KEY_KP_9;
common_scanmap[100]                = KEY_KP_4;
common_scanmap[101]                = KEY_KP_5;
common_scanmap[102]                = KEY_KP_6;
common_scanmap[107]                = KEY_KP_Plus;
common_scanmap[97]                 = KEY_KP_1;
common_scanmap[98]                 = KEY_KP_2;
common_scanmap[99]                 = KEY_KP_3;
common_scanmap[96]                 = KEY_KP_0;
common_scanmap[110]                = KEY_KP_Decimal;
common_scanmap[191]                = KEY_Slash;
common_scanmap[190]                = KEY_Period;
common_scanmap[188]                = KEY_Comma;
common_scanmap[220]                = KEY_BSlash;
common_scanmap[192]                = KEY_Tilde;
common_scanmap[222]                = KEY_Quote;
common_scanmap[219]                = KEY_LBrace;
common_scanmap[221]                = KEY_RBrace;

common_scanmap[91]                 = 0xE05B; //KEY_LMeta
common_scanmap[92]                 = 0xE05C; //KEY_RMeta
common_scanmap[93]                 = 0xE05D; //KEY_Menu

/* Firefox/Mozilla codes */
var firefox_scanmap = [];
firefox_scanmap[173]                = KEY_Minus;
firefox_scanmap[109]                = KEY_Minus;
firefox_scanmap[61]                 = KEY_Equal;
firefox_scanmap[59]                 = KEY_SemiColon;

/* DOM3 codes */
var DOM_scanmap = [];
DOM_scanmap[189]                = KEY_Minus;
DOM_scanmap[187]                = KEY_Equal;
DOM_scanmap[186]                = KEY_SemiColon;

function get_scancode(code)
{
    if (common_scanmap[code] === undefined)
    {
        if (navigator.userAgent.indexOf("Firefox") != -1)
            return firefox_scanmap[code];
        else
            return DOM_scanmap[code];
    }
    else
        return common_scanmap[code];
}

function keycode_to_start_scan(code)
{
    var scancode = get_scancode(code);
    if (scancode === undefined)
    {
        alert('no map for ' + code);
        return 0;
    }

    if (scancode < 0x100) {
        return scancode;
    } else {
        return 0xe0 | ((scancode - 0x100) << 8);
    }
}

function keycode_to_end_scan(code)
{
    var scancode = get_scancode(code);
    if (scancode === undefined)
        return 0;

    if (scancode < 0x100) {
        return scancode | 0x80;
    } else {
        return 0x80e0 | ((scancode - 0x100) << 8);
    }
}
