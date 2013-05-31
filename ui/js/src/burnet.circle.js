/*
 * Project Burnet
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwanghl@cn.ibm.com>
 *
 * All Rights Reserved.
 */
(function($) {
    $.fn.circle = function(options) {
        var settings = $.extend({
            color: '#87C004',
            fillColor: '#87C004',
            fontFamily: 'Geneva, sans-serif',
            fontSize: 13,
            radius: 35,
            lineWidth: 20
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
                'boxShadow': shadowSize + 'px ' + shadowSize + 'px ' + shadowSize + 'px #fff, -' + shadowSize + 'px -' + shadowSize + 'px ' + shadowSize + 'px #eaeaea',
                borderRadius: radius + 'px'
            });
            ctx.clearRect(0, 0, width, height);

            ctx.fillStyle = settings['fillColor'];
            ctx.font = 'bold ' + fontSize + 'px ' + settings['fontFamily'];
            ctx.textAlign = 'center';
            var originPos = radius;
            ctx.textBaseline='middle';
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

burnet.circle = function(selector) {
	$(selector).circle();
};
