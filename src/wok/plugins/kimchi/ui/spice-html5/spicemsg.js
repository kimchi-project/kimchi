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
**  Spice messages
**      This file contains classes for passing messages to and from
**  a spice server.  This file should arguably be generated from 
**  spice.proto, but it was instead put together by hand.
**--------------------------------------------------------------------------*/
function SpiceLinkHeader(a, at)
{
    this.magic = SPICE_MAGIC;
    this.major_version = SPICE_VERSION_MAJOR;
    this.minor_version = SPICE_VERSION_MINOR;
    this.size = 0;
    if (a !== undefined)
        this.from_buffer(a, at);
}

SpiceLinkHeader.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.magic = "";
        for (var i = 0; i < 4; i++)
            this.magic += String.fromCharCode(dv.getUint8(at + i));
        at += 4;

        this.major_version = dv.getUint32(at, true); at += 4;
        this.minor_version = dv.getUint32(at, true); at += 4;
        this.size = dv.getUint32(at, true); at += 4;
    },

    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        for (var i = 0; i < 4; i++)
            dv.setUint8(at + i, this.magic.charCodeAt(i));
        at += 4;

        dv.setUint32(at, this.major_version, true); at += 4;
        dv.setUint32(at, this.minor_version, true); at += 4;
        dv.setUint32(at, this.size, true); at += 4;
    },
    buffer_size: function()
    { 
        return 16;
    },
}

function SpiceLinkMess(a, at)
{
    this.connection_id = 0;
    this.channel_type = 0;
    this.channel_id = 0;
    this.common_caps = [];
    this.channel_caps = [];

    if (a !== undefined)
        this.from_buffer(a, at);
}

SpiceLinkMess.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var i;
        var orig_at = at;
        var dv = new SpiceDataView(a);
        this.connection_id = dv.getUint32(at, true); at += 4;
        this.channel_type = dv.getUint8(at, true); at++;
        this.channel_id = dv.getUint8(at, true); at++;
        var num_common_caps = dv.getUint32(at, true); at += 4;
        var num_channel_caps  = dv.getUint32(at, true); at += 4;
        var caps_offset = dv.getUint32(at, true); at += 4;

        at = orig_at + caps_offset;
        this.common_caps = [];
        for (i = 0; i < num_common_caps; i++)
        {
            this.common_caps.unshift(dv.getUint32(at, true)); at += 4;
        }

        this.channel_caps = [];
        for (i = 0; i < num_channel_caps; i++)
        {
            this.channel_caps.unshift(dv.getUint32(at, true)); at += 4;
        }
    },

    to_buffer: function(a, at)
    {
        at = at || 0;
        var orig_at = at;
        var i;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.connection_id, true); at += 4;
        dv.setUint8(at, this.channel_type, true); at++;
        dv.setUint8(at, this.channel_id, true); at++;
        dv.setUint32(at, this.common_caps.length, true); at += 4;
        dv.setUint32(at, this.channel_caps.length, true); at += 4;
        dv.setUint32(at, (at - orig_at) + 4, true); at += 4;

        for (i = 0; i < this.common_caps.length; i++)
        {
            dv.setUint32(at, this.common_caps[i], true); at += 4;
        }

        for (i = 0; i < this.channel_caps.length; i++)
        {
            dv.setUint32(at, this.channel_caps[i], true); at += 4;
        }
    },
    buffer_size: function()
    {
        return 18 + (4 * this.common_caps.length) + (4 * this.channel_caps.length);
    }
}

function SpiceLinkReply(a, at)
{
    this.error = 0;
    this.pub_key = undefined;
    this.common_caps = [];
    this.channel_caps = [];

    if (a !== undefined)
        this.from_buffer(a, at);
}

SpiceLinkReply.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var i;
        var orig_at = at;
        var dv = new SpiceDataView(a);
        this.error = dv.getUint32(at, true); at += 4;

        this.pub_key = create_rsa_from_mb(a, at);
        at += SPICE_TICKET_PUBKEY_BYTES;

        var num_common_caps = dv.getUint32(at, true); at += 4;
        var num_channel_caps  = dv.getUint32(at, true); at += 4;
        var caps_offset = dv.getUint32(at, true); at += 4;

        at = orig_at + caps_offset;
        this.common_caps = [];
        for (i = 0; i < num_common_caps; i++)
        {
            this.common_caps.unshift(dv.getUint32(at, true)); at += 4;
        }

        this.channel_caps = [];
        for (i = 0; i < num_channel_caps; i++)
        {
            this.channel_caps.unshift(dv.getUint32(at, true)); at += 4;
        }
    },
}

function SpiceLinkAuthTicket(a, at)
{
    this.auth_mechanism = 0;
    this.encrypted_data = undefined;
}

SpiceLinkAuthTicket.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var i;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.auth_mechanism, true); at += 4;
        for (i = 0; i < SPICE_TICKET_KEY_PAIR_LENGTH / 8; i++)
        {
            if (this.encrypted_data && i < this.encrypted_data.length)
                dv.setUint8(at, this.encrypted_data[i], true);
            else
                dv.setUint8(at, 0, true);
            at++;
        }
    },
    buffer_size: function()
    {
        return 4 + (SPICE_TICKET_KEY_PAIR_LENGTH / 8);
    }
}

function SpiceLinkAuthReply(a, at)
{
    this.auth_code = 0;
    if (a !== undefined)
        this.from_buffer(a, at);
}

SpiceLinkAuthReply.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.auth_code = dv.getUint32(at, true); at += 4;
    },
    buffer_size: function()
    {
        return 4;
    }
}

function SpiceMiniData(a, at)
{
    this.type = 0;
    this.size = 0;
    this.data = undefined;
    if (a !== undefined)
        this.from_buffer(a, at);
}

SpiceMiniData.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var i;
        var dv = new SpiceDataView(a);
        this.type = dv.getUint16(at, true); at += 2;
        this.size = dv.getUint32(at, true); at += 4;
        if (a.byteLength > at)
        {
            this.data = a.slice(at);
            at += this.data.byteLength;
        }
    },
    to_buffer : function(a, at)
    {
        at = at || 0;
        var i;
        var dv = new SpiceDataView(a);
        dv.setUint16(at, this.type, true); at += 2;
        dv.setUint32(at, this.data ? this.data.byteLength : 0, true); at += 4;
        if (this.data && this.data.byteLength > 0)
        {
            var u8arr = new Uint8Array(this.data);
            for (i = 0; i < u8arr.length; i++, at++)
                dv.setUint8(at, u8arr[i], true);
        }
    },
    build_msg : function(in_type,  extra)
    {
        this.type = in_type;
        this.size = extra.buffer_size();
        this.data = new ArrayBuffer(this.size);
        extra.to_buffer(this.data);
    },
    buffer_size: function()
    {
        if (this.data)
            return 6 + this.data.byteLength;
        else
            return 6;
    },
}

function SpiceMsgChannels(a, at)
{
    this.num_of_channels = 0;
    this.channels = [];
    if (a !== undefined)
        this.from_buffer(a, at);
}

SpiceMsgChannels.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var i;
        var dv = new SpiceDataView(a);
        this.num_of_channels = dv.getUint32(at, true); at += 4;
        for (i = 0; i < this.num_of_channels; i++)
        {
            var chan = new SpiceChannelId();
            at = chan.from_dv(dv, at, a);
            this.channels.push(chan);
        }
    },
}

function SpiceMsgMainInit(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgMainInit.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.session_id = dv.getUint32(at, true); at += 4;
        this.display_channels_hint = dv.getUint32(at, true); at += 4;
        this.supported_mouse_modes = dv.getUint32(at, true); at += 4;
        this.current_mouse_mode = dv.getUint32(at, true); at += 4;
        this.agent_connected = dv.getUint32(at, true); at += 4;
        this.agent_tokens = dv.getUint32(at, true); at += 4;
        this.multi_media_time = dv.getUint32(at, true); at += 4;
        this.ram_hint = dv.getUint32(at, true); at += 4;
    },
}

function SpiceMsgMainMouseMode(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgMainMouseMode.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.supported_modes = dv.getUint16(at, true); at += 2;
        this.current_mode = dv.getUint16(at, true); at += 2;
    },
}

function SpiceMsgSetAck(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgSetAck.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.generation = dv.getUint32(at, true); at += 4;
        this.window = dv.getUint32(at, true); at += 4;
    },
}

function SpiceMsgcAckSync(ack)
{
    this.generation = ack.generation;
}

SpiceMsgcAckSync.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.generation, true); at += 4;
    },
    buffer_size: function()
    {
        return 4;
    }
}

function SpiceMsgcMainMouseModeRequest(mode)
{
    this.mode = mode;
}

SpiceMsgcMainMouseModeRequest.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint16(at, this.mode, true); at += 2;
    },
    buffer_size: function()
    {
        return 2;
    }
}

function SpiceMsgcMainAgentStart(num_tokens)
{
    this.num_tokens = num_tokens;
}

SpiceMsgcMainAgentStart.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.num_tokens, true); at += 4;
    },
    buffer_size: function()
    {
        return 4;
    }
}

function SpiceMsgcMainAgentData(type, data)
{
    this.protocol = VD_AGENT_PROTOCOL;
    this.type = type;
    this.opaque = 0;
    this.size = data.buffer_size();
    this.data = data;
}

SpiceMsgcMainAgentData.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.protocol, true); at += 4;
        dv.setUint32(at, this.type, true); at += 4;
        dv.setUint64(at, this.opaque, true); at += 8;
        dv.setUint32(at, this.size, true); at += 4;
        this.data.to_buffer(a, at);
    },
    buffer_size: function()
    {
        return 4 + 4 + 8 + 4 + this.data.buffer_size();
    }
}

function VDAgentMonitorsConfig(flags, width, height, depth, x, y)
{
    this.num_mon = 1;
    this.flags = flags;
    this.width = width;
    this.height = height;
    this.depth = depth;
    this.x = x;
    this.y = y;
}

VDAgentMonitorsConfig.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.num_mon, true); at += 4;
        dv.setUint32(at, this.flags, true); at += 4;
        dv.setUint32(at, this.height, true); at += 4;
        dv.setUint32(at, this.width, true); at += 4;
        dv.setUint32(at, this.depth, true); at += 4;
        dv.setUint32(at, this.x, true); at += 4;
        dv.setUint32(at, this.y, true); at += 4;
    },
    buffer_size: function()
    {
        return 28;
    }
}

function SpiceMsgNotify(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgNotify.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var i;
        var dv = new SpiceDataView(a);
        this.time_stamp = dv.getUint64(at, true); at += 8;
        this.severity = dv.getUint32(at, true); at += 4;
        this.visibility = dv.getUint32(at, true); at += 4;
        this.what = dv.getUint32(at, true); at += 4;
        this.message_len = dv.getUint32(at, true); at += 4;
        this.message = "";
        for (i = 0; i < this.message_len; i++)
        {
            var c = dv.getUint8(at, true); at++;
            this.message += String.fromCharCode(c);
        }
    },
}

function SpiceMsgcDisplayInit()
{
    this.pixmap_cache_id = 1;
    this.glz_dictionary_id = 0;
    this.pixmap_cache_size = 10 * 1024 * 1024;
    this.glz_dictionary_window_size = 0;
}

SpiceMsgcDisplayInit.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint8(at, this.pixmap_cache_id, true); at++;
        dv.setUint64(at, this.pixmap_cache_size, true); at += 8;
        dv.setUint8(at, this.glz_dictionary_id, true); at++;
        dv.setUint32(at, this.glz_dictionary_window_size, true); at += 4;
    },
    buffer_size: function()
    {
        return 14;
    }
}

function SpiceMsgDisplayBase()
{
}

SpiceMsgDisplayBase.prototype =
{
    from_dv : function(dv, at, mb)
    {
        this.surface_id = dv.getUint32(at, true); at += 4;
        this.box = new SpiceRect;
        at = this.box.from_dv(dv, at, mb);
        this.clip = new SpiceClip;
        return this.clip.from_dv(dv, at, mb);
    },
}

function SpiceMsgDisplayDrawCopy(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgDisplayDrawCopy.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.base = new SpiceMsgDisplayBase;
        at = this.base.from_dv(dv, at, a);
        this.data = new SpiceCopy;
        return this.data.from_dv(dv, at, a);
    },
}

function SpiceMsgDisplayDrawFill(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgDisplayDrawFill.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.base = new SpiceMsgDisplayBase;
        at = this.base.from_dv(dv, at, a);
        this.data = new SpiceFill;
        return this.data.from_dv(dv, at, a);
    },
}

function SpiceMsgDisplayCopyBits(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgDisplayCopyBits.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.base = new SpiceMsgDisplayBase;
        at = this.base.from_dv(dv, at, a);
        this.src_pos = new SpicePoint;
        return this.src_pos.from_dv(dv, at, a);
    },
}


function SpiceMsgSurfaceCreate(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgSurfaceCreate.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.surface = new SpiceSurface;
        return this.surface.from_dv(dv, at, a);
    },
}

function SpiceMsgSurfaceDestroy(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgSurfaceDestroy.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.surface_id = dv.getUint32(at, true); at += 4;
    },
}

function SpiceMsgInputsInit(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgInputsInit.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.keyboard_modifiers = dv.getUint16(at, true); at += 2;
        return at;
    },
}

function SpiceMsgInputsKeyModifiers(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgInputsKeyModifiers.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.keyboard_modifiers = dv.getUint16(at, true); at += 2;
        return at;
    },
}

function SpiceMsgCursorInit(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgCursorInit.prototype =
{
    from_buffer: function(a, at, mb)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.position = new SpicePoint16;
        at = this.position.from_dv(dv, at, mb);
        this.trail_length = dv.getUint16(at, true); at += 2;
        this.trail_frequency = dv.getUint16(at, true); at += 2;
        this.visible = dv.getUint8(at, true); at ++;
        this.cursor = new SpiceCursor;
        return this.cursor.from_dv(dv, at, a);
    },
}

function SpiceMsgPlaybackData(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgPlaybackData.prototype =
{
    from_buffer: function(a, at, mb)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.time = dv.getUint32(at, true); at += 4;
        if (a.byteLength > at)
        {
            this.data = a.slice(at);
            at += this.data.byteLength;
        }
        return at;
    },
}

function SpiceMsgPlaybackMode(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgPlaybackMode.prototype =
{
    from_buffer: function(a, at, mb)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.time = dv.getUint32(at, true); at += 4;
        this.mode = dv.getUint16(at, true); at += 2;
        if (a.byteLength > at)
        {
            this.data = a.slice(at);
            at += this.data.byteLength;
        }
        return at;
    },
}

function SpiceMsgPlaybackStart(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgPlaybackStart.prototype =
{
    from_buffer: function(a, at, mb)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.channels = dv.getUint32(at, true); at += 4;
        this.format = dv.getUint16(at, true); at += 2;
        this.frequency = dv.getUint32(at, true); at += 4;
        this.time = dv.getUint32(at, true); at += 4;
        return at;
    },
}



function SpiceMsgCursorSet(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgCursorSet.prototype =
{
    from_buffer: function(a, at, mb)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.position = new SpicePoint16;
        at = this.position.from_dv(dv, at, mb);
        this.visible = dv.getUint8(at, true); at ++;
        this.cursor = new SpiceCursor;
        return this.cursor.from_dv(dv, at, a);
    },
}


function SpiceMsgcMousePosition(sc, e)
{
    // FIXME - figure out how to correctly compute display_id
    this.display_id = 0;
    this.buttons_state = sc.buttons_state;
    if (e)
    {
        var scrollTop = document.body.scrollTop || document.documentElement.scrollTop;
        var scrollLeft = document.body.scrollLeft || document.documentElement.scrollLeft;

        this.x = e.clientX - sc.display.surfaces[sc.display.primary_surface].canvas.offsetLeft + scrollLeft;
        this.y = e.clientY - sc.display.surfaces[sc.display.primary_surface].canvas.offsetTop + scrollTop;
        sc.mousex = this.x;
        sc.mousey = this.y; 
    }
    else
    {
        this.x = this.y = this.buttons_state = 0;
    }
}

SpiceMsgcMousePosition.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.x, true); at += 4;
        dv.setUint32(at, this.y, true); at += 4;
        dv.setUint16(at, this.buttons_state, true); at += 2;
        dv.setUint8(at, this.display_id, true); at += 1;
        return at;
    },
    buffer_size: function()
    {
        return 11;
    }
}

function SpiceMsgcMouseMotion(sc, e)
{
    // FIXME - figure out how to correctly compute display_id
    this.display_id = 0;
    this.buttons_state = sc.buttons_state;
    if (e)
    {
        this.x = e.clientX - sc.display.surfaces[sc.display.primary_surface].canvas.offsetLeft;
        this.y = e.clientY - sc.display.surfaces[sc.display.primary_surface].canvas.offsetTop;

        if (sc.mousex !== undefined)
        {
            this.x -= sc.mousex;
            this.y -= sc.mousey;
        }
        sc.mousex = e.clientX - sc.display.surfaces[sc.display.primary_surface].canvas.offsetLeft;
        sc.mousey = e.clientY - sc.display.surfaces[sc.display.primary_surface].canvas.offsetTop;
    }
    else
    {
        this.x = this.y = this.buttons_state = 0;
    }
}

/* Use the same functions as for MousePosition */
SpiceMsgcMouseMotion.prototype.to_buffer = SpiceMsgcMousePosition.prototype.to_buffer;
SpiceMsgcMouseMotion.prototype.buffer_size = SpiceMsgcMousePosition.prototype.buffer_size;

function SpiceMsgcMousePress(sc, e)
{
    if (e)
    {
        this.button = e.button + 1;
        this.buttons_state = 1 << e.button;
        sc.buttons_state = this.buttons_state;
    }
    else
    {
        this.button = SPICE_MOUSE_BUTTON_LEFT;
        this.buttons_state = SPICE_MOUSE_BUTTON_MASK_LEFT;
    }
}

SpiceMsgcMousePress.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint8(at, this.button, true); at ++;
        dv.setUint16(at, this.buttons_state, true); at += 2;
        return at;
    },
    buffer_size: function()
    {
        return 3;
    }
}

function SpiceMsgcMouseRelease(sc, e)
{
    if (e)
    {
        this.button = e.button + 1;
        this.buttons_state = 0;
        sc.buttons_state = this.buttons_state;
    }
    else
    {
        this.button = SPICE_MOUSE_BUTTON_LEFT;
        this.buttons_state = 0;
    }
}

/* Use the same functions as for MousePress */
SpiceMsgcMouseRelease.prototype.to_buffer = SpiceMsgcMousePress.prototype.to_buffer;
SpiceMsgcMouseRelease.prototype.buffer_size = SpiceMsgcMousePress.prototype.buffer_size;


function SpiceMsgcKeyDown(e)
{
    if (e)
    {
        this.code = keycode_to_start_scan(e.keyCode);
    }
    else
    {
        this.code = 0;
    }
}

SpiceMsgcKeyDown.prototype =
{
    to_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        dv.setUint32(at, this.code, true); at += 4;
        return at;
    },
    buffer_size: function()
    {
        return 4;
    }
}

function SpiceMsgcKeyUp(e)
{
    if (e)
    {
        this.code = keycode_to_end_scan(e.keyCode);
    }
    else
    {
        this.code = 0;
    }
}

/* Use the same functions as for KeyDown */
SpiceMsgcKeyUp.prototype.to_buffer = SpiceMsgcKeyDown.prototype.to_buffer;
SpiceMsgcKeyUp.prototype.buffer_size = SpiceMsgcKeyDown.prototype.buffer_size;

function SpiceMsgDisplayStreamCreate(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgDisplayStreamCreate.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.surface_id = dv.getUint32(at, true); at += 4;
        this.id = dv.getUint32(at, true); at += 4;
        this.flags = dv.getUint8(at, true); at += 1;
        this.codec_type = dv.getUint8(at, true); at += 1;
        this.stamp = dv.getUint64(at, true); at += 8;
        this.stream_width = dv.getUint32(at, true); at += 4;
        this.stream_height = dv.getUint32(at, true); at += 4;
        this.src_width = dv.getUint32(at, true); at += 4;
        this.src_height = dv.getUint32(at, true); at += 4;

        this.dest = new SpiceRect;
        at = this.dest.from_dv(dv, at, a);
        this.clip = new SpiceClip;
        this.clip.from_dv(dv, at, a);
    },
}

function SpiceStreamDataHeader(a, at)
{
}

SpiceStreamDataHeader.prototype =
{
    from_dv : function(dv, at, mb)
    {
        this.id = dv.getUint32(at, true); at += 4;
        this.multi_media_time = dv.getUint32(at, true); at += 4;
        return at;
    },
}

function SpiceMsgDisplayStreamData(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgDisplayStreamData.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.base = new SpiceStreamDataHeader;
        at = this.base.from_dv(dv, at, a);
        this.data_size = dv.getUint32(at, true); at += 4;
        this.data = dv.u8.subarray(at, at + this.data_size);
    },
}

function SpiceMsgDisplayStreamClip(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgDisplayStreamClip.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.id = dv.getUint32(at, true); at += 4;
        this.clip = new SpiceClip;
        this.clip.from_dv(dv, at, a);
    },
}

function SpiceMsgDisplayStreamDestroy(a, at)
{
    this.from_buffer(a, at);
}

SpiceMsgDisplayStreamDestroy.prototype =
{
    from_buffer: function(a, at)
    {
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.id = dv.getUint32(at, true); at += 4;
    },
}

function SpiceMsgDisplayInvalList(a, at)
{
    this.count = 0;
    this.resources = [];
    this.from_buffer(a,at);
}

SpiceMsgDisplayInvalList.prototype =
{
    from_buffer: function (a, at)
    {
        var i;
        at = at || 0;
        var dv = new SpiceDataView(a);
        this.count = dv.getUint16(at, true); at += 2;
        for (i = 0; i < this.count; i++)
        {
            this.resources[i] = {};
            this.resources[i].type = dv.getUint8(at, true); at++;
            this.resources[i].id = dv.getUint64(at, true); at += 8;
        }
    },
}
