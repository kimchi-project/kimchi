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
**  SpiceConn
**      This is the base Javascript class for establishing and
**  managing a connection to a Spice Server.
**  It is used to provide core functionality to the Spice main,
**  display, inputs, and cursor channels.  See main.js for 
**  usage.
**--------------------------------------------------------------------------*/
function SpiceConn(o)
{
    if (o === undefined || o.uri === undefined || ! o.uri)
        throw new Error("You must specify a uri");

    this.ws = new WebSocket(o.uri, 'binary');

    if (! this.ws.binaryType)
        throw new Error("WebSocket doesn't support binaryType.  Try a different browser.");

    this.connection_id = o.connection_id !== undefined ? o.connection_id : 0;
    this.type = o.type !== undefined ? o.type : SPICE_CHANNEL_MAIN;
    this.chan_id = o.chan_id !== undefined ? o.chan_id : 0;
    if (o.parent !== undefined)
    {
        this.parent = o.parent;
        this.message_id = o.parent.message_id;
        this.password = o.parent.password;
    }
    if (o.screen_id !== undefined)
        this.screen_id = o.screen_id;
    if (o.dump_id !== undefined)
        this.dump_id = o.dump_id;
    if (o.message_id !== undefined)
        this.message_id = o.message_id;
    if (o.password !== undefined)
        this.password = o.password;
    if (o.onerror !== undefined)
        this.onerror = o.onerror;
    if (o.onsuccess !== undefined)
        this.onsuccess = o.onsuccess;
    if (o.onagent !== undefined)
        this.onagent = o.onagent;

    this.state = "connecting";
    this.ws.parent = this;
    this.wire_reader = new SpiceWireReader(this, this.process_inbound);
    this.messages_sent = 0;
    this.warnings = [];

    this.ws.addEventListener('open', function(e) {
        DEBUG > 0 && console.log(">> WebSockets.onopen");
        DEBUG > 0 && console.log("id " + this.parent.connection_id +"; type " + this.parent.type);

        /***********************************************************************
        **          WHERE IT ALL REALLY BEGINS
        ***********************************************************************/
        this.parent.send_hdr();
        this.parent.wire_reader.request(SpiceLinkHeader.prototype.buffer_size());
        this.parent.state = "start";
    });
    this.ws.addEventListener('error', function(e) {
        this.parent.log_err(">> WebSockets.onerror" + e.toString());
        this.parent.report_error(e);
    });
    this.ws.addEventListener('close', function(e) {
        DEBUG > 0 && console.log(">> WebSockets.onclose");
        DEBUG > 0 && console.log("id " + this.parent.connection_id +"; type " + this.parent.type);
        DEBUG > 0 && console.log(e);
        if (this.parent.state != "closing" && this.parent.state != "error" && this.parent.onerror !== undefined)
        {
            var e;
            if (this.parent.state == "connecting")
                e = new Error("Connection refused.");
            else if (this.parent.state == "start" || this.parent.state == "link")
                e = new Error("Unexpected protocol mismatch.");
            else if (this.parent.state == "ticket")
                e = new Error("Bad password.");
            else
                e = new Error("Unexpected close while " + this.parent.state);

            this.parent.onerror(e);
            this.parent.log_err(e.toString());
        }
    });

    if (this.ws.readyState == 2 || this.ws.readyState == 3)
        throw new Error("Unable to connect to " + o.uri);

    this.timeout = window.setTimeout(spiceconn_timeout, SPICE_CONNECT_TIMEOUT, this);
}

SpiceConn.prototype =
{
    send_hdr : function ()
    {
        var hdr = new SpiceLinkHeader;
        var msg = new SpiceLinkMess;

        msg.connection_id = this.connection_id;
        msg.channel_type = this.type;
        // FIXME - we're not setting a channel_id...
        msg.common_caps.push(
            (1 << SPICE_COMMON_CAP_PROTOCOL_AUTH_SELECTION) |
            (1 << SPICE_COMMON_CAP_MINI_HEADER)
            );

        if (msg.channel_type == SPICE_CHANNEL_PLAYBACK)
            msg.channel_caps.push(
                (1 << SPICE_PLAYBACK_CAP_OPUS)
            );

        hdr.size = msg.buffer_size();

        var mb = new ArrayBuffer(hdr.buffer_size() + msg.buffer_size());
        hdr.to_buffer(mb);
        msg.to_buffer(mb, hdr.buffer_size());

        DEBUG > 1 && console.log("Sending header:");
        DEBUG > 2 && hexdump_buffer(mb);
        this.ws.send(mb);
    },

    send_ticket: function(ticket)
    {
        var hdr = new SpiceLinkAuthTicket();
        hdr.auth_mechanism = SPICE_COMMON_CAP_AUTH_SPICE;
        // FIXME - we need to implement RSA to make this work right
        hdr.encrypted_data = ticket;
        var mb = new ArrayBuffer(hdr.buffer_size());

        hdr.to_buffer(mb);
        DEBUG > 1 && console.log("Sending ticket:");
        DEBUG > 2 && hexdump_buffer(mb);
        this.ws.send(mb);
    },

    send_msg: function(msg)
    {
        var mb = new ArrayBuffer(msg.buffer_size());
        msg.to_buffer(mb);
        this.messages_sent++;
        DEBUG > 0 && console.log(">> hdr " + this.channel_type() + " type " + msg.type + " size " + mb.byteLength);
        DEBUG > 2 && hexdump_buffer(mb);
        this.ws.send(mb);
    },

    process_inbound: function(mb, saved_header)
    {
        DEBUG > 2 && console.log(this.type + ": processing message of size " + mb.byteLength + "; state is " + this.state);
        if (this.state == "ready")
        {
            if (saved_header == undefined)
            {
                var msg = new SpiceMiniData(mb);

                if (msg.type > 500)
                {
                    alert("Something has gone very wrong; we think we have message of type " + msg.type);
                    debugger;
                }

                if (msg.size == 0)
                {
                    this.process_message(msg);
                    this.wire_reader.request(SpiceMiniData.prototype.buffer_size());
                }
                else
                {
                    this.wire_reader.request(msg.size);
                    this.wire_reader.save_header(msg);
                }
            }
            else
            {
                saved_header.data = mb;
                this.process_message(saved_header);
                this.wire_reader.request(SpiceMiniData.prototype.buffer_size());
                this.wire_reader.save_header(undefined);
            }
        }

        else if (this.state == "start")
        {
            this.reply_hdr = new SpiceLinkHeader(mb);
            if (this.reply_hdr.magic != SPICE_MAGIC)
            {
                this.state = "error";
                var e = new Error('Error: magic mismatch: ' + this.reply_hdr.magic);
                this.report_error(e);
            }
            else
            {
                // FIXME - Determine major/minor version requirements
                this.wire_reader.request(this.reply_hdr.size);
                this.state = "link";
            }
        }

        else if (this.state == "link")
        {
            this.reply_link = new SpiceLinkReply(mb);
             // FIXME - Screen the caps - require minihdr at least, right?
            if (this.reply_link.error)
            {
                this.state = "error";
                var e = new Error('Error: reply link error ' + this.reply_link.error);
                this.report_error(e);
            }
            else
            {
                this.send_ticket(rsa_encrypt(this.reply_link.pub_key, this.password + String.fromCharCode(0)));
                this.state = "ticket";
                this.wire_reader.request(SpiceLinkAuthReply.prototype.buffer_size());
            }
        }

        else if (this.state == "ticket")
        {
            this.auth_reply = new SpiceLinkAuthReply(mb);
            if (this.auth_reply.auth_code == SPICE_LINK_ERR_OK)
            {
                DEBUG > 0 && console.log(this.type + ': Connected');

                if (this.type == SPICE_CHANNEL_DISPLAY)
                {
                    // FIXME - pixmap and glz dictionary config info?
                    var dinit = new SpiceMsgcDisplayInit();
                    var reply = new SpiceMiniData();
                    reply.build_msg(SPICE_MSGC_DISPLAY_INIT, dinit);
                    DEBUG > 0 && console.log("Request display init");
                    this.send_msg(reply);
                }
                this.state = "ready";
                this.wire_reader.request(SpiceMiniData.prototype.buffer_size());
                if (this.timeout)
                {
                    window.clearTimeout(this.timeout);
                    delete this.timeout;
                }
            }
            else
            {
                this.state = "error";
                if (this.auth_reply.auth_code == SPICE_LINK_ERR_PERMISSION_DENIED)
                {
                    var e = new Error("Permission denied.");
                }
                else
                {
                    var e = new Error("Unexpected link error " + this.auth_reply.auth_code);
                }
                this.report_error(e);
            }
        }
    },

    process_common_messages : function(msg)
    {
        if (msg.type == SPICE_MSG_SET_ACK)
        {
            var ack = new SpiceMsgSetAck(msg.data);
            // FIXME - what to do with generation?
            this.ack_window = ack.window;
            DEBUG > 1 && console.log(this.type + ": set ack to " + ack.window);
            this.msgs_until_ack = this.ack_window;
            var ackack = new SpiceMsgcAckSync(ack);
            var reply = new SpiceMiniData();
            reply.build_msg(SPICE_MSGC_ACK_SYNC, ackack);
            this.send_msg(reply);
            return true;
        }

        if (msg.type == SPICE_MSG_PING)
        {
            DEBUG > 1 && console.log("ping!");
            var pong = new SpiceMiniData;
            pong.type = SPICE_MSGC_PONG;
            if (msg.data)
            {
                pong.data = msg.data.slice(0, 12);
            }
            pong.size = pong.buffer_size();
            this.send_msg(pong);
            return true;
        }

        if (msg.type == SPICE_MSG_NOTIFY)
        {
            // FIXME - Visibility + what
            var notify = new SpiceMsgNotify(msg.data);
            if (notify.severity == SPICE_NOTIFY_SEVERITY_ERROR)
                this.log_err(notify.message);
            else if (notify.severity == SPICE_NOTIFY_SEVERITY_WARN )
                this.log_warn(notify.message);
            else
                this.log_info(notify.message);
            return true;
        }

        return false;

    },

    process_message: function(msg)
    {
        var rc;
        DEBUG > 0 && console.log("<< hdr " + this.channel_type() + " type " + msg.type + " size " + (msg.data && msg.data.byteLength));
        rc = this.process_common_messages(msg);
        if (! rc)
        {
            if (this.process_channel_message)
            {
                rc = this.process_channel_message(msg);
                if (! rc)
                    this.log_warn(this.type + ": Unknown message type " + msg.type + "!");
            }
            else
                this.log_err(this.type + ": No message handlers for this channel; message " + msg.type);
        }

        if (this.msgs_until_ack !== undefined && this.ack_window)
        {
            this.msgs_until_ack--;
            if (this.msgs_until_ack <= 0)
            {
                this.msgs_until_ack = this.ack_window;
                var ack = new SpiceMiniData();
                ack.type = SPICE_MSGC_ACK;
                this.send_msg(ack);
                DEBUG > 1 && console.log(this.type + ": sent ack");
            }
        }

        return rc;
    },

    channel_type: function()
    {
        if (this.type == SPICE_CHANNEL_MAIN)
            return "main";
        else if (this.type == SPICE_CHANNEL_DISPLAY)
            return "display";
        else if (this.type == SPICE_CHANNEL_INPUTS)
            return "inputs";
        else if (this.type == SPICE_CHANNEL_CURSOR)
            return "cursor";
        return "unknown-" + this.type;

    },

    log_info: function()
    {
        var msg = Array.prototype.join.call(arguments, " ");
        console.log(msg);
        if (this.message_id)
        {
            var p = document.createElement("p");
            p.appendChild(document.createTextNode(msg));
            p.className += "spice-message-info";
            document.getElementById(this.message_id).appendChild(p);
        }
    },

    log_warn: function()
    {
        var msg = Array.prototype.join.call(arguments, " ");
        console.log("WARNING: " + msg);
        if (this.message_id)
        {
            var p = document.createElement("p");
            p.appendChild(document.createTextNode(msg));
            p.className += "spice-message-warning";
            document.getElementById(this.message_id).appendChild(p);
        }
    },

    log_err: function()
    {
        var msg = Array.prototype.join.call(arguments, " ");
        console.log("ERROR: " + msg);
        if (this.message_id)
        {
            var p = document.createElement("p");
            p.appendChild(document.createTextNode(msg));
            p.className += "spice-message-error";
            document.getElementById(this.message_id).appendChild(p);
        }
    },

    known_unimplemented: function(type, msg)
    {
        if ( (!this.warnings[type]) || DEBUG > 1)
        {
            var str = "";
            if (DEBUG <= 1)
                str = " [ further notices suppressed ]";
            this.log_warn("Unimplemented function " + type + "(" + msg + ")" + str);
            this.warnings[type] = true;
        }
    },

    report_error: function(e)
    {
        this.log_err(e.toString());
        if (this.onerror != undefined)
            this.onerror(e);
        else
            throw(e);
    },

    report_success: function(m)
    {
        if (this.onsuccess != undefined)
            this.onsuccess(m);
    },

    cleanup: function()
    {
        if (this.timeout)
        {
            window.clearTimeout(this.timeout);
            delete this.timeout;
        }
        if (this.ws)
        {
            this.ws.close();
            this.ws = undefined;
        }
    },

    handle_timeout: function()
    {
        var e = new Error("Connection timed out.");
        this.report_error(e);
    },
}

function spiceconn_timeout(sc)
{
    SpiceConn.prototype.handle_timeout.call(sc);
}
