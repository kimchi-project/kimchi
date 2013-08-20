/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwanghl@cn.ibm.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function($) {
    $.fn.circle = function(options) {
        var settings = $.extend({
            color : '#87C004',
            fillColor : '#87C004',
            fontFamily : 'Geneva, sans-serif',
            fontSize : 13,
            radius : 35,
            lineWidth : 20
        }, options);

        $(this).each(function() {
            var that = $(this);
            var percentage = parseInt(that.data('value'));
            that.empty();
            var canvas = document.createElement('canvas');
            that.append($(canvas));
            var ctx = canvas.getContext('2d');
            var lineWidth = settings['lineWidth'];
            var radius = settings['radius'];
            var fontSize = settings['fontSize'];
            var shadowSize = 2;
            var width = height = radius * 2;
            $(canvas).attr('height', height);
            $(canvas).attr('width', width);
            $(canvas).css({
                'boxShadow' : shadowSize + 'px ' + shadowSize + 'px ' + shadowSize + 'px #fff, -' + shadowSize + 'px -' + shadowSize + 'px ' + shadowSize + 'px #eaeaea',
                borderRadius : radius + 'px'
            });
            ctx.clearRect(0, 0, width, height);

            ctx.fillStyle = settings['fillColor'];
            ctx.font = 'bold ' + fontSize + 'px ' + settings['fontFamily'];
            ctx.textAlign = 'center';
            var originPos = radius;
            ctx.textBaseline = 'middle';
            ctx.fillText(percentage + '%', originPos, originPos);
            ctx.strokeStyle = settings['color'];
            ctx.lineWidth = lineWidth;
            ctx.beginPath();
            ctx.arc(originPos, originPos, radius, -.5 * Math.PI, (percentage / 50 - .5) * Math.PI);
            ctx.stroke();
        });

        return this;
    };
}(jQuery));

kimchi.circle = function(selector) {
    $(selector).circle();
};
