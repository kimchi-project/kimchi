/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014
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
    $.widget('kimchi.circleGauge', {

        options : {
            color : '#87C004',
            fillColor : '#87C004',
            lineWidth : 20,
            shadowSize : '2px',
            font : 'bold 13px Geneva, sans-serif',
            textAlign : 'center',
            radius : 35,
            peakRate : 100,
            display : 0,
            circle : 0,
            label : ''
        },

        _create : function() {
            //valuesAttr="{" + this.element.data('value')+ "}";
            //console.info(valuesAttr);
            //values=eval("(" + valuesAttr + ")");
            //$.extend(this.options, values);
            this.options.display=this.element.data('display');
            this.options.percentage=this.element.data('percentage');
            this._fixupPeakRate();
            this._draw();
        },

        setValues : function(values) {
            $.extend(this.options, values);
            this._fixupPeakRate();
            this._draw();
        },

        _fixupPeakRate : function() {
            if (this.options.circle>this.options.peakRate) {
                this.options.peakRate=this.options.circle;
            }
        },

        _draw : function() {
            this.element.empty();
            var canvas = document.createElement('canvas');
            //this.element.append($(canvas));  //I don't quite understand this line so trying the one below...
            this.element.append(canvas);

            var ctx = canvas.getContext('2d');
            var radius = this.options.radius;

            var shadowSize = 2;
            var width = height = radius * 2;
            $(canvas).attr('height', height);
            $(canvas).attr('width', width);

            $(canvas).css({
                'boxShadow' : shadowSize + 'px ' + shadowSize + 'px ' + shadowSize + 'px #fff, -' + shadowSize + 'px -' + shadowSize + 'px ' + shadowSize + 'px #eaeaea',
                borderRadius : radius + 'px'
            });

            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = this.options.fillColor;
            ctx.font = this.options.font;
            ctx.textAlign = 'center';
            var originPos = radius;
            ctx.textBaseline = 'middle';
            ctx.fillText(this.options.display, originPos, originPos);
            ctx.strokeStyle = this.options.color;
            ctx.lineWidth = this.options.lineWidth;
            ctx.beginPath();
            ctx.arc(originPos, originPos, radius, -.5 * Math.PI, (this.options.percentage / 50 - .5) * Math.PI);
            ctx.stroke();
        },

        destroy : function() {
            this.element.empty();
            $.Widget.prototype.destroy.call(this);
        }
    });
}(jQuery));

kimchi.circleGauge = function(selector) {
    $(selector).circleGauge();
};
