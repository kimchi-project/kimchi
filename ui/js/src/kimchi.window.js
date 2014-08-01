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
kimchi.window = (function() {
    var _windows = [];
    var _listeners = {};
    var open = function(settings) {
        var settings = jQuery.type(settings) === 'object' ? settings : {
            url: settings
        };

        var windowID = settings['id'] || 'window-' + _windows.length;

        if ($('#' + windowID).length) {
            $('#' + windowID).remove();
        }

        _windows.push(windowID);
        _listeners[windowID] = settings['close'];
        var windowNode = $('<div></div>', {
            id: windowID,
            'class': settings['class'] ? settings['class'] + ' bgmask remove-when-logged-off' : 'bgmask remove-when-logged-off'
        });

        $(windowNode).css(settings['style'] || '');

        $(windowNode).appendTo('body').on('click', '.window .close', function() {
            kimchi.window.close();
        });

        if (settings['url']) {
            $(windowNode).load(settings['url']).fadeIn(100);
            return;
        }

        settings['content'] && $(windowNode).html(settings['content']);
    };

    var close = function() {
        var windowID = _windows.pop();
        if(_listeners[windowID]) {
            _listeners[windowID]();
            _listeners[windowID] = null;
        }
        delete _listeners[windowID];

        $('#' + windowID).fadeOut(100, function() {
            $(this).remove();
        });
    };

    return {
        open: open,
        close: close
    };
})();
