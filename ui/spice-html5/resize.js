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
**  resize.js
**      This bit of Javascript is a set of logic to help with window
**  resizing, using the agent channel to request screen resizes.
**
**  It's a bit tricky, as we want to wait for resizing to settle down
**  before sending a size.  Further, while horizontal resizing to use the whole
**  browser width is fairly easy to arrange with css, resizing an element to use
**  the whole vertical space (or to force a middle div to consume the bulk of the browser
**  window size) is tricky, and the consensus seems to be that Javascript is
**  the only right way to do it.
**--------------------------------------------------------------------------*/
function resize_helper(sc)
{
    var w = document.getElementById(sc.screen_id).clientWidth;
    var h = document.getElementById(sc.screen_id).clientHeight;

    var m = document.getElementById(sc.message_id);

    /* Resize vertically; basically we leave a 20 pixel margin
         at the bottom, and use the position of the message window
         to figure out how to resize */
    var hd = window.innerHeight - m.offsetHeight - m.offsetTop - 20;

    /* Xorg requires height be a multiple of 8; round up */
    h = h + hd;
    if (h % 8 > 0)
        h += (8 - (h % 8));

    /* Xorg requires width be a multiple of 8; round up */
    if (w % 8 > 0)
        w += (8 - (w % 8));


    sc.resize_window(0, w, h, 32, 0, 0);
    sc.spice_resize_timer = undefined;
}

function handle_resize(e)
{
    var sc = window.spice_connection;

    if (sc && sc.spice_resize_timer)
    {
        window.clearTimeout(sc.spice_resize_timer);
        sc.spice_resize_timer = undefined;
    }

    sc.spice_resize_timer = window.setTimeout(resize_helper, 200, sc);
}
