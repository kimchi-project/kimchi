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
 ** Modifier Keystates
 **     These need to be tracked because focus in and out can get the keyboard
 **     out of sync.
 **------------------------------------------------------------------------*/
var Shift_state = -1;
var Ctrl_state = -1;
var Alt_state = -1;
var Meta_state = -1;

/*----------------------------------------------------------------------------
**  SpiceInputsConn
**      Drive the Spice Inputs channel (e.g. mouse + keyboard)
**--------------------------------------------------------------------------*/
function SpiceInputsConn()
{
    SpiceConn.apply(this, arguments);

    this.mousex = undefined;
    this.mousey = undefined;
    this.button_state = 0;
    this.waiting_for_ack = 0;
}

SpiceInputsConn.prototype = Object.create(SpiceConn.prototype);
SpiceInputsConn.prototype.process_channel_message = function(msg)
{
    if (msg.type == SPICE_MSG_INPUTS_INIT)
    {
        var inputs_init = new SpiceMsgInputsInit(msg.data);
        this.keyboard_modifiers = inputs_init.keyboard_modifiers;
        DEBUG > 1 && console.log("MsgInputsInit - modifier " + this.keyboard_modifiers);
        // FIXME - We don't do anything with the keyboard modifiers...
        return true;
    }
    if (msg.type == SPICE_MSG_INPUTS_KEY_MODIFIERS)
    {
        var key = new SpiceMsgInputsKeyModifiers(msg.data);
        this.keyboard_modifiers = key.keyboard_modifiers;
        DEBUG > 1 && console.log("MsgInputsKeyModifiers - modifier " + this.keyboard_modifiers);
        // FIXME - We don't do anything with the keyboard modifiers...
        return true;
    }
    if (msg.type == SPICE_MSG_INPUTS_MOUSE_MOTION_ACK)
    {
        DEBUG > 1 && console.log("mouse motion ack");
        this.waiting_for_ack -= SPICE_INPUT_MOTION_ACK_BUNCH;
        return true;
    }
    return false;
}



function handle_mousemove(e)
{
    var msg = new SpiceMiniData();
    var move;
    if (this.sc.mouse_mode == SPICE_MOUSE_MODE_CLIENT)
    {
        move = new SpiceMsgcMousePosition(this.sc, e)
        msg.build_msg(SPICE_MSGC_INPUTS_MOUSE_POSITION, move);
    }
    else
    {
        move = new SpiceMsgcMouseMotion(this.sc, e)
        msg.build_msg(SPICE_MSGC_INPUTS_MOUSE_MOTION, move);
    }
    if (this.sc && this.sc.inputs && this.sc.inputs.state === "ready")
    {
        if (this.sc.inputs.waiting_for_ack < (2 * SPICE_INPUT_MOTION_ACK_BUNCH))
        {
            this.sc.inputs.send_msg(msg);
            this.sc.inputs.waiting_for_ack++;
        }
        else
        {
            DEBUG > 0 && this.sc.log_info("Discarding mouse motion");
        }
    }

    if (this.sc && this.sc.cursor && this.sc.cursor.spice_simulated_cursor)
    {
        this.sc.cursor.spice_simulated_cursor.style.display = 'block';
        this.sc.cursor.spice_simulated_cursor.style.left = e.pageX - this.sc.cursor.spice_simulated_cursor.spice_hot_x + 'px';
        this.sc.cursor.spice_simulated_cursor.style.top = e.pageY - this.sc.cursor.spice_simulated_cursor.spice_hot_y + 'px';
        e.preventDefault();
    }

}

function handle_mousedown(e)
{
    var press = new SpiceMsgcMousePress(this.sc, e)
    var msg = new SpiceMiniData();
    msg.build_msg(SPICE_MSGC_INPUTS_MOUSE_PRESS, press);
    if (this.sc && this.sc.inputs && this.sc.inputs.state === "ready")
        this.sc.inputs.send_msg(msg);

    e.preventDefault();
}

function handle_contextmenu(e)
{
    e.preventDefault();
    return false;
}

function handle_mouseup(e)
{
    var release = new SpiceMsgcMouseRelease(this.sc, e)
    var msg = new SpiceMiniData();
    msg.build_msg(SPICE_MSGC_INPUTS_MOUSE_RELEASE, release);
    if (this.sc && this.sc.inputs && this.sc.inputs.state === "ready")
        this.sc.inputs.send_msg(msg);

    e.preventDefault();
}

function handle_mousewheel(e)
{
    var press = new SpiceMsgcMousePress;
    var release = new SpiceMsgcMouseRelease;
    if (e.wheelDelta > 0)
        press.button = release.button = SPICE_MOUSE_BUTTON_UP;
    else
        press.button = release.button = SPICE_MOUSE_BUTTON_DOWN;
    press.buttons_state = 0;
    release.buttons_state = 0;

    var msg = new SpiceMiniData();
    msg.build_msg(SPICE_MSGC_INPUTS_MOUSE_PRESS, press);
    if (this.sc && this.sc.inputs && this.sc.inputs.state === "ready")
        this.sc.inputs.send_msg(msg);

    msg.build_msg(SPICE_MSGC_INPUTS_MOUSE_RELEASE, release);
    if (this.sc && this.sc.inputs && this.sc.inputs.state === "ready")
        this.sc.inputs.send_msg(msg);

    e.preventDefault();
}

function handle_keydown(e)
{
    var key = new SpiceMsgcKeyDown(e)
    var msg = new SpiceMiniData();
    check_and_update_modifiers(e, key.code, this.sc);
    msg.build_msg(SPICE_MSGC_INPUTS_KEY_DOWN, key);
    if (this.sc && this.sc.inputs && this.sc.inputs.state === "ready")
        this.sc.inputs.send_msg(msg);

    e.preventDefault();
}

function handle_keyup(e)
{
    var key = new SpiceMsgcKeyUp(e)
    var msg = new SpiceMiniData();
    check_and_update_modifiers(e, key.code, this.sc);
    msg.build_msg(SPICE_MSGC_INPUTS_KEY_UP, key);
    if (this.sc && this.sc.inputs && this.sc.inputs.state === "ready")
        this.sc.inputs.send_msg(msg);

    e.preventDefault();
}

function sendCtrlAltDel()
{
    if (sc && sc.inputs && sc.inputs.state === "ready"){
        var key = new SpiceMsgcKeyDown();
        var msg = new SpiceMiniData();

        update_modifier(true, KEY_LCtrl, sc);
        update_modifier(true, KEY_Alt, sc);

        key.code = KEY_KP_Decimal;
        msg.build_msg(SPICE_MSGC_INPUTS_KEY_DOWN, key);
        sc.inputs.send_msg(msg);
        msg.build_msg(SPICE_MSGC_INPUTS_KEY_UP, key);
        sc.inputs.send_msg(msg);

        if(Ctrl_state == false) update_modifier(false, KEY_LCtrl, sc);
        if(Alt_state == false) update_modifier(false, KEY_Alt, sc);
    }
}

function update_modifier(state, code, sc)
{
    var msg = new SpiceMiniData();
    if (!state)
    {
        var key = new SpiceMsgcKeyUp()
        key.code =(0x80|code);
        msg.build_msg(SPICE_MSGC_INPUTS_KEY_UP, key);
    }
    else
    {
        var key = new SpiceMsgcKeyDown()
        key.code = code;
        msg.build_msg(SPICE_MSGC_INPUTS_KEY_DOWN, key);
    }

    sc.inputs.send_msg(msg);
}

function check_and_update_modifiers(e, code, sc)
{
    if (Shift_state === -1)
    {
        Shift_state = e.shiftKey;
        Ctrl_state = e.ctrlKey;
        Alt_state = e.altKey;
        Meta_state = e.metaKey;
    }

    if (code === KEY_ShiftL)
        Shift_state = true;
    else if (code === KEY_Alt)
        Alt_state = true;
    else if (code === KEY_LCtrl)
        Ctrl_state = true;
    else if (code === 0xE0B5)
        Meta_state = true;
    else if (code === (0x80|KEY_ShiftL))
        Shift_state = false;
    else if (code === (0x80|KEY_Alt))
        Alt_state = false;
    else if (code === (0x80|KEY_LCtrl))
        Ctrl_state = false;
    else if (code === (0x80|0xE0B5))
        Meta_state = false;

    if (sc && sc.inputs && sc.inputs.state === "ready")
    {
        if (Shift_state != e.shiftKey)
        {
            console.log("Shift state out of sync");
            update_modifier(e.shiftKey, KEY_ShiftL, sc);
            Shift_state = e.shiftKey;
        }
        if (Alt_state != e.altKey)
        {
            console.log("Alt state out of sync");
            update_modifier(e.altKey, KEY_Alt, sc);
            Alt_state = e.altKey;
        }
        if (Ctrl_state != e.ctrlKey)
        {
            console.log("Ctrl state out of sync");
            update_modifier(e.ctrlKey, KEY_LCtrl, sc);
            Ctrl_state = e.ctrlKey;
        }
        if (Meta_state != e.metaKey)
        {
            console.log("Meta state out of sync");
            update_modifier(e.metaKey, 0xE0B5, sc);
            Meta_state = e.metaKey;
        }
    }
}
