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
kimchi.message = function(msg, level, node) {
    var container = node || $('#messageField');
    if ($(container).size() < 1) {
        container = $('<div id="messageField"/>').appendTo(document.body);
    }
    var message = '<div class="message ' + (level || '') + '" style="display: none;">';
    if(!node) {
        message += '<div class="close">X</div>';
    }
    message += '<div class="content">' + msg + '</div>';
    message += '</div>';
    var $message = $(message);
    $(container).append($message);
    $message.fadeIn(100);

    setTimeout(function() {
        $message.fadeOut(2000, function() {
            $(this).remove();
        });
    }, 4000);

    $(container).on("click", ".close", function(e) {
        $(this).parent().fadeOut(200, function() {
            $(this).remove();
        });
    });
};

/**
 * A public function of confirm box.
 *
 * @param msg
 *            type:[object]
 * @param msg.title
 *            The title of the confirm box.
 * @param msg.content
 *            The main text of the confirm box.
 * @param msg.confirm
 *            The text of the confirm button.
 * @param msg.cancel
 *            the text of the cancel button.
 * @param confirmCallback
 *            the callback function of click the confirm button.
 * @param cancelCallback
 *            The callback function of click the cancel and X button.
 */
kimchi.confirm = function(settings, confirmCallback, cancelCallback) {
    if ($('#confirmbox-container ').size() < 1) {
        $(document.body).append('<div id="confirmbox-container" class="bgmask"></div>');
    }
    var confirmboxHtml = '<div class="confirmbox">';
    confirmboxHtml += '<header>';
    confirmboxHtml += '<h4 class="title">' + (settings.title || '') + '</h4>';
    confirmboxHtml += '<div class="close cancel">X</div>';
    confirmboxHtml += '</header>';
    confirmboxHtml += '<div class="content">';
    confirmboxHtml += settings.content + '</div>';
    confirmboxHtml += '<footer>';
    confirmboxHtml += '<div class="btn-group">';
    confirmboxHtml += '<button id="button-confirm" class="btn-small"><span class="text">' + (settings.confirm || i18n['KCHAPI6004M']) + '</span></button>';
    confirmboxHtml += '<button id="button-cancel" class="btn-small cancel"><span class="text">' + (settings.cancel || i18n['KCHAPI6003M']) + '</span></button>';
    confirmboxHtml += '</div>';
    confirmboxHtml += '</footer>';
    confirmboxHtml += '</div>';
    var confirmboxNode = $(confirmboxHtml);
    $('#confirmbox-container').append(confirmboxNode);
    confirmboxNode.fadeIn();

    $('#confirmbox-container').on("click", "#button-confirm", function(e) {
        if (confirmCallback) {
            confirmCallback();
        }
        confirmboxNode.fadeOut(1, function() {
            $('#confirmbox-container').remove();
        });
    });
    $('#confirmbox-container').on("click", ".cancel", function(e) {
        if (cancelCallback) {
            cancelCallback();
        }
        confirmboxNode.fadeOut(1, function() {
            $('#confirmbox-container').remove();
        });
    });
};

kimchi.message.warn = function(msg, node) {
    kimchi.message(msg, 'warn', node);
};
kimchi.message.error = function(msg, node) {
    kimchi.message(msg, 'error', node);
};
kimchi.message.error.code = function(code) {
    msg = code + ": " + i18n[code]
    kimchi.message(msg, 'error');
};
kimchi.message.success = function(msg, node) {
    kimchi.message(msg, 'success', node);
};
