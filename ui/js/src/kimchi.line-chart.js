/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2014
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

/**
 * new kimchi.widget.LineChart({
 *   node: 'line-chart-cpu',
 *   id: 'line-chart',
 *   type: 'value'
 * });
 */
kimchi.widget.LineChart = function(params) {
    var container = $('#' + params['node']);
    container.addClass('chart-container');
    var height = container.height();
    var width = container.width();
    var numHLines = 4;
    var linesSpace = height / numHLines;
    var period = params['period'] || 20;
    var xFactor = width / period;
    var yFactor = height / 100;
    var xStart = params['xStart'] || 0;
    var linesOffset = 0;
    var canvasID = params['id'];
    var maxValue = params['maxValue'] || -Infinity;
    var type = params['type'];
    var chartVAxis = null;
    var chartTitle = null;
    var chartLegend = null;
    var seriesMap = {};
    var formatSettings = {};

    var setMaxValue = function(newValue) {
        maxValue = newValue;
    };

    /**
     *
     * settings: {
     *   'class': 'disk-read-rate'
     * }
     */
    var updateUI = function(data) {
        var container = $('#' + params['node']);
        if(!container.length) {
            return;
        }

        if(!$.isArray(data)) {
            data = [data];
        }
        var seriesCount = 0;
        var singleSeries = data.length === 1;
        var firstSeries = data[0];

        // TODO: Multiple axes support.
        if(type === 'value') {
            $.each(data, function(i, series) {
                if(series['max'] > maxValue) {
                    maxValue = series['max'];
                    formatSettings = {
                        base: series['base'],
                        unit: series['unit'],
                        fixed: series['fixed']
                    };
                }
            });
        }

        var canvasNode = $('#' + canvasID);
        canvasNode.length && canvasNode.remove();
        var htmlStr = [
          '<svg id="', canvasID, '" class="line-chart"',
              ' height="', height, '" width="', width, '"',
          '>',
            '<rect height="', height, '" width="', width, '" class="background" />'
        ];

        for(var x = linesOffset; x < width; x += linesSpace) {
            htmlStr.push(
                '<line x1="', x, '" y1="', 0, '" x2="', x, '" y2="', height, '" />'
            );
        }

        linesOffset -= xFactor;
        while(linesOffset < 0) {
            linesOffset = linesSpace + linesOffset;
        }

        for(var y = height - linesSpace; y > 0; y -= linesSpace) {
            htmlStr.push(
                '<line x1="', 0, '" y1="', y, '" x2="', width, '" y2="', y, '" />'
            );
        }

        var maxValueLabel = i18n['KCHHOST6001M'] + ' ' +
            (type === 'value'
                ? kimchi.formatMeasurement(maxValue, formatSettings)
                : '100%');
        if(!chartVAxis) {
            chartVAxis = $('<div class="chart-vaxis-container">' +
                maxValueLabel +
                '</div>'
            );
            container.before(chartVAxis);
        }
        else {
            chartVAxis.text(maxValueLabel);
        }

        seriesNames = [];
        $.each(data, function(i, series) {
            var points = series['points'];
            var className = series['class'];
            var latestPoint = points.slice(-1).pop();
            xStart = latestPoint['x'] - period;

            htmlStr.push('<polyline',
                ' class="series', className ? ' ' + className : '', '"',
                ' points="'
            );
            var first = true;
            $.each(points, function(i, point) {
                if(first) {
                    first = false;
                }
                else {
                    htmlStr.push(' ');
                }

                var x = xFactor * (point['x'] - xStart);
                var y = height - yFactor * (type === 'value' ?
                    point['y'] * 100 / maxValue :
                    point['y']
                );
                htmlStr.push(x, ',', y);
            });
            htmlStr.push('" />');
        });

        htmlStr.push('</svg>');

        var canvasNode = $(htmlStr.join('')).appendTo(container);

        if(!chartLegend) {
            chartLegend = $('<div class="chart-legend-container"></div>');
            container.after(chartLegend);
        }
        else {
            chartLegend.empty();
        }
        $('polyline.series', canvasNode).each(function(i, polyline) {
            var wrapper = $('<div class="legend-wrapper"></div>')
                .appendTo(chartLegend);
            $([
                '<svg class="legend-icon" width="20" height="10">',
                    '<line x1="0" y1="5" x2="20" y2="5"/>',
                '</svg>'
            ].join('')).appendTo(wrapper);
            $('line', wrapper).css({
                stroke: $(polyline).css('stroke'),
                'stroke-width': $(polyline).css('stroke-width')
            });
            var label = data[i]['legend'];
            var base = data[i]['base'];
            $('<label class="legend-label">' + label + '</label>')
                .appendTo(wrapper);
            var latestPoint = data[i]['points'].slice(-1).pop();
            var latestValue = latestPoint['y'];
            if(type === 'value') {
                latestValue = kimchi.formatMeasurement(
                    latestValue,
                    formatSettings
                );
            }
            else {
                latestValue += '%';
            }
            $('<div class="latest-value">' + latestValue + '</div>')
                .appendTo(wrapper);
        });
    };

    return {
        setMaxValue: setMaxValue,
        updateUI: updateUI
    }
};
