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
**  SpiceMainConn
**      This is the master Javascript class for establishing and
**  managing a connection to a Spice Server.
**
**      Invocation:  You must pass an object with properties as follows:
**          uri         (required)  Uri of a WebSocket listener that is
**                                  connected to a spice server.
**          password    (required)  Password to send to the spice server
**          message_id  (optional)  Identifier of an element in the DOM
**                                  where SpiceConn will write messages.
**                                  It will use classes spice-messages-x,
**                                  where x is one of info, warning, or error.
**          screen_id   (optional)  Identifier of an element in the DOM
**                                  where SpiceConn will create any new
**                                  client screens.  This is the main UI.
**          dump_id     (optional)  If given, an element to use for
**                                  dumping every single image + canvas drawn.
**                                  Sometimes useful for debugging.
**          onerror     (optional)  If given, a function to receive async
**                                  errors.  Note that you should also catch
**                                  errors for ones that occur inline
**
**  Throws error if there are troubles.  Requires a modern (by 2012 standards)
**      browser, including WebSocket and WebSocket.binaryType == arraybuffer
**
**--------------------------------------------------------------------------*/
function SpiceMainConn()
{
    if (typeof WebSocket === "undefined")
        throw new Error("WebSocket unavailable.  You need to use a different browser.");

    SpiceConn.apply(this, arguments);

}

SpiceMainConn.prototype = Object.create(SpiceConn.prototype);
SpiceMainConn.prototype.process_channel_message = function(msg)
{
    if (msg.type == SPICE_MSG_MAIN_INIT)
    {
        this.log_info("Connected to " + this.ws.url);
        this.main_init = new SpiceMsgMainInit(msg.data);
        this.connection_id = this.main_init.session_id;

        if (DEBUG > 0)
        {
            // FIXME - there is a lot here we don't handle; mouse modes, agent,
            //          ram_hint, multi_media_time
            this.log_info("session id "                 + this.main_init.session_id +
                          " ; display_channels_hint "   + this.main_init.display_channels_hint +
                          " ; supported_mouse_modes "   + this.main_init.supported_mouse_modes +
                          " ; current_mouse_mode "      + this.main_init.current_mouse_mode +
                          " ; agent_connected "         + this.main_init.agent_connected +
                          " ; agent_tokens "            + this.main_init.agent_tokens +
                          " ; multi_media_time "        + this.main_init.multi_media_time +
                          " ; ram_hint "                + this.main_init.ram_hint);
        }

        this.mouse_mode = this.main_init.current_mouse_mode;
        if (this.main_init.current_mouse_mode != SPICE_MOUSE_MODE_CLIENT &&
            (this.main_init.supported_mouse_modes & SPICE_MOUSE_MODE_CLIENT))
        {
            var mode_request = new SpiceMsgcMainMouseModeRequest(SPICE_MOUSE_MODE_CLIENT);
            var mr = new SpiceMiniData();
            mr.build_msg(SPICE_MSGC_MAIN_MOUSE_MODE_REQUEST, mode_request);
            this.send_msg(mr);
        }

        var attach = new SpiceMiniData;
        attach.type = SPICE_MSGC_MAIN_ATTACH_CHANNELS;
        attach.size = attach.buffer_size();
        this.send_msg(attach);
        return true;
    }

    if (msg.type == SPICE_MSG_MAIN_MOUSE_MODE)
    {
        var mode = new SpiceMsgMainMouseMode(msg.data);
        DEBUG > 0 && this.log_info("Mouse supported modes " + mode.supported_modes + "; current " + mode.current_mode);
        this.mouse_mode = mode.current_mode;
        if (this.inputs)
            this.inputs.mouse_mode = mode.current_mode;
        return true;
    }

    if (msg.type == SPICE_MSG_MAIN_CHANNELS_LIST)
    {
        var i;
        var chans;
        DEBUG > 0 && console.log("channels");
        chans = new SpiceMsgChannels(msg.data);
        for (i = 0; i < chans.channels.length; i++)
        {
            var conn = {
                        uri: this.ws.url,
                        parent: this,
                        connection_id : this.connection_id,
                        type : chans.channels[i].type,
                        chan_id : chans.channels[i].id
                    };
            if (chans.channels[i].type == SPICE_CHANNEL_DISPLAY)
                this.display = new SpiceDisplayConn(conn);
            else if (chans.channels[i].type == SPICE_CHANNEL_INPUTS)
            {
                this.inputs = new SpiceInputsConn(conn);
                this.inputs.mouse_mode = this.mouse_mode;
            }
            else if (chans.channels[i].type == SPICE_CHANNEL_CURSOR)
                this.cursor = new SpiceCursorConn(conn);
            else
            {
                this.log_err("Channel type " + chans.channels[i].type + " unknown.");
                if (! ("extra_channels" in this))
                    this.extra_channels = [];
                this.extra_channels[i] = new SpiceConn(conn);
            }

        }

        return true;
    }

    return false;
}

SpiceMainConn.prototype.stop = function(msg)
{
    this.state = "closing";

    if (this.inputs)
    {
        this.inputs.cleanup();
        this.inputs = undefined;
    }

    if (this.cursor)
    {
        this.cursor.cleanup();
        this.cursor = undefined;
    }

    if (this.display)
    {
        this.display.cleanup();
        this.display.destroy_surfaces();
        this.display = undefined;
    }

    this.cleanup();

    if ("extra_channels" in this)
        for (var e in this.extra_channels)
            this.extra_channels[e].cleanup();
    this.extra_channels = undefined;
}
