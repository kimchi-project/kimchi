/*
 * Project Wok
 *
 * Copyright IBM, Corp. 2013-2015
 *
 * Code derived from Project Kimchi
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

wok.message = function(msg, level, node) {
    "use strict";
    var container = node || $('#alert-fields');
    if ($(container).size() < 1) {
        container = $('<div id="alert-fields"/>').appendTo($('#alert-container'));
    }
    var message = '<div role="alert" class="alert ' + (level || '') + ' alert-dismissible fade in" style="display: none;">';
    if(!node) {
        message += '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true"><i class="fa fa-times-circle"></i></span></button>';
    }
    message += msg;
    message += '</div>';
    var $message = $(message);
    $(container).show();
    $(container).append($message);
    $message.alert();
    $message.fadeIn(100);

    var timeout = setTimeout(function() {
        $message.delay(2000).fadeOut(100, function() {            
            $message.alert('close');
            $(this).remove();
            if ($(container).children().length < 1) {
                $(container).hide();
            }
        });
    }, 4000);
};

wok.message.warn = function(msg, node) {
    "use strict";
    wok.message(msg, 'alert-warning', node); 
};
wok.message.error = function(msg, node) {
    "use strict";
    wok.message(msg, 'alert-danger', node);
};
wok.message.error.code = function(code) {
    "use strict";
    var msg = code + ": " + i18n[code];
    wok.message(msg, 'alert-danger');
};
wok.message.success = function(msg, node) {
    "use strict";
    wok.message(msg, 'alert-success', node);
};
