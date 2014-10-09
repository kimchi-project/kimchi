"use strict";
/*
   Copyright (C) 2014 by Jeremy P. White <jwhite@codeweavers.com>

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
**  SpicePlaybackConn
**      Drive the Spice Playback channel (sound out)
**--------------------------------------------------------------------------*/
function SpicePlaybackConn()
{
    SpiceConn.apply(this, arguments);

    this.queue = new Array();
    this.append_okay = false;
    this.start_time = 0;
    this.skip_until = 0;
    this.gap_time = 0;
}

SpicePlaybackConn.prototype = Object.create(SpiceConn.prototype);
SpicePlaybackConn.prototype.process_channel_message = function(msg)
{
    if (!!!window.MediaSource)
    {
        this.log_err('MediaSource API is not available');
        return false;
    }

    if (msg.type == SPICE_MSG_PLAYBACK_START)
    {
        var start = new SpiceMsgPlaybackStart(msg.data);

        DEBUG > 0 && console.log("PlaybackStart; frequency " + start.frequency);

        if (start.frequency != OPUS_FREQUENCY)
        {
            this.log_err('This player cannot handle frequency ' + start.frequency);
            return false;
        }

        if (start.channels != OPUS_CHANNELS)
        {
            this.log_err('This player cannot handle ' + start.channels + ' channels');
            return false;
        }

        if (start.format != SPICE_AUDIO_FMT_S16)
        {
            this.log_err('This player cannot format ' + start.format);
            return false;
        }

        if (! this.source_buffer)
        {
            this.media_source = new MediaSource();
            this.media_source.spiceconn = this;

            this.audio = document.createElement("audio");
            this.audio.setAttribute('autoplay', true);
            this.audio.src = window.URL.createObjectURL(this.media_source);
            document.getElementById(this.parent.screen_id).appendChild(this.audio);

            this.media_source.addEventListener('sourceopen', handle_source_open, false);
            this.media_source.addEventListener('sourceended', handle_source_ended, false);
            this.media_source.addEventListener('sourceclosed', handle_source_closed, false);

            this.bytes_written = 0;

            return true;
        }
    }

    if (msg.type == SPICE_MSG_PLAYBACK_DATA)
    {
        var data = new SpiceMsgPlaybackData(msg.data);

        // If this packet has the same time as the last, just bump up by one.
        if (this.last_data_time && data.time <= this.last_data_time)
        {
            // FIXME - this is arguably wrong.  But delaying the transmission was worse,
            //          in initial testing.  Could use more research.
            DEBUG > 1 && console.log("Hacking time of " + data.time + " to " + this.last_data_time + 1);
            data.time = this.last_data_time + 1;
        }

        /* Gap detection:  If there has been a delay since our last packet, then audio must
             have paused.  Handling that gets tricky.  In Chrome, you can seek forward,
             but you cannot in Firefox.  And seeking forward in Chrome is nice, as it keeps
             Chrome from being overly cautious in it's buffer strategy.

             So we do two things.  First, we seek forward.  Second, we compute how much of a gap
             there would have been, and essentially eliminate it.
        */
        if (this.last_data_time && data.time >= (this.last_data_time + GAP_DETECTION_THRESHOLD))
        {
            this.skip_until = data.time;
            this.gap_time = (data.time - this.start_time) - 
              (this.source_buffer.buffered.end(this.source_buffer.buffered.end.length - 1) * 1000.0).toFixed(0);
        }

        this.last_data_time = data.time;


        DEBUG > 1 && console.log("PlaybackData; time " + data.time + "; length " + data.data.byteLength);

        if (! this.source_buffer)
            return true;

        if (this.start_time == 0)
            this.start_playback(data);

        else if (data.time - this.cluster_time >= MAX_CLUSTER_TIME || this.skip_until > 0)
            this.new_cluster(data);

        else
            this.simple_block(data, false);

        if (this.skip_until > 0)
        {
            this.audio.currentTime = (this.skip_until - this.start_time - this.gap_time) / 1000.0;
            this.skip_until = 0;
        }

        if (this.audio.paused)
            this.audio.play();

        return true;
    }

    if (msg.type == SPICE_MSG_PLAYBACK_MODE)
    {
        var mode = new SpiceMsgPlaybackMode(msg.data);
        if (mode.mode != SPICE_AUDIO_DATA_MODE_OPUS)
        {
            this.log_err('This player cannot handle mode ' + mode.mode);
            delete this.source_buffer;
        }
        return true;
    }

    if (msg.type == SPICE_MSG_PLAYBACK_STOP)
    {
        return true;
    }

    return false;
}

SpicePlaybackConn.prototype.start_playback = function(data)
{
    this.start_time = data.time;

    var h = new webm_Header();

    var mb = new ArrayBuffer(h.buffer_size())

    this.bytes_written = h.to_buffer(mb);

    this.source_buffer.addEventListener('error', handle_sourcebuffer_error, false);
    this.source_buffer.addEventListener('updateend', handle_append_buffer_done, false);
    playback_append_buffer(this, mb);

    this.new_cluster(data);
}

SpicePlaybackConn.prototype.new_cluster = function(data)
{
    this.cluster_time = data.time;

    var c = new webm_Cluster(data.time - this.start_time - this.gap_time);

    var mb = new ArrayBuffer(c.buffer_size());
    this.bytes_written += c.to_buffer(mb);

    if (this.append_okay)
        playback_append_buffer(this, mb);
    else
        this.queue.push(mb);

    this.simple_block(data, true);
}

SpicePlaybackConn.prototype.simple_block = function(data, keyframe)
{
    var sb = new webm_SimpleBlock(data.time - this.cluster_time, data.data, keyframe);
    var mb = new ArrayBuffer(sb.buffer_size());

    this.bytes_written += sb.to_buffer(mb);

    if (this.append_okay)
        playback_append_buffer(this, mb);
    else
        this.queue.push(mb);
}

function handle_source_open(e)
{
    var p = this.spiceconn;

    if (p.source_buffer)
        return;

    p.source_buffer = this.addSourceBuffer(SPICE_PLAYBACK_CODEC);
    if (! p.source_buffer)
    {
        p.log_err('Codec ' + SPICE_PLAYBACK_CODEC + ' not available.');
        return;
    }
    p.source_buffer.spiceconn = p;
    p.source_buffer.mode = "segments";

    // FIXME - Experimentation with segments and sequences was unsatisfying.
    //         Switching to sequence did not solve our gap problem,
    //         but the browsers didn't fully support the time seek capability
    //         we would expect to gain from 'segments'.
    //         Segments worked at the time of this patch, so segments it is for now.

}

function handle_source_ended(e)
{
    var p = this.spiceconn;
    p.log_err('Audio source unexpectedly ended.');
}

function handle_source_closed(e)
{
    var p = this.spiceconn;
    p.log_err('Audio source unexpectedly closed.');
}

function handle_append_buffer_done(b)
{
    var p = this.spiceconn;
    if (p.queue.length > 0)
    {
        var mb = p.queue.shift();
        playback_append_buffer(p, mb);
    }
    else
        p.append_okay = true;

}

function handle_sourcebuffer_error(e)
{
    var p = this.spiceconn;
    p.log_err('source_buffer error ' + e.message);
}

function playback_append_buffer(p, b)
{
    try
    {
        p.source_buffer.appendBuffer(b);
        p.append_okay = false;
    }
    catch (e)
    {
        p.log_err("Error invoking appendBuffer: " + e.message);
    }
}
