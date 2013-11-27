/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Xin Ding <xinding@linux.vnet.ibm.com>
 *  Hongliang Wang <hlwanghl@linux.vnet.ibm.com>
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
kimchi.window = (function() {
    var _windows = [];
    var open = function(settings) {
        var settings = jQuery.type(settings) === 'object' ? settings : {
            url: settings
        };

        if (_windows.length) {
            var lastZIndex = parseInt($('#' + _windows[_windows.length - 1]).css('zIndex'));
            if (settings['style']) {
                settings['style']['zIndex'] = lastZIndex + 1;
            }
            else {
                settings['style'] = {
                    zIndex: lastZIndex + 1
                };
            }
        }

        var windowID = settings['id'] || 'window-' + _windows.length;

        if ($('#' + windowID).length) {
            $('#' + windowID).remove();
        }

        _windows.push(windowID);
        var windowNode = $('<div></div>', {
            id: windowID,
            'class': settings['class'] ? settings['class'] + ' bgmask' : 'bgmask'
        });

        $(windowNode).css(settings['style'] || '');

        $(windowNode).appendTo('body').on('click', '.window .close', function() {
            if (settings.close) {
                settings.close();
            }
            kimchi.window.close();
        });

        if (settings['url']) {
            $(windowNode).load(settings['url']).fadeIn(100);
            return;
        }

        settings['content'] && $(windowNode).html(settings['content']);
    };

    var close = function() {
        $('#' + _windows.pop()).fadeOut(100, function() {
            $(this).remove();
        });
    };

    return {
        open: open,
        close: close
    };
})();
