/*
 * Project Wok
 *
 * Copyright IBM, Corp. 2015
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
wok.confirm = function(settings, confirmCallback, cancelCallback) {
    "use strict";
    var modalStr = '<div id="wok-confirm-modal" class="modal fade host-modal" tabindex="-1" role="dialog" aria-labelledby="confirmModalLabel" aria-hidden="true"></div>';
    if ($('#wok-confirm-modal ').size() < 1 && $('#modalWindow').size() < 1 ) {
        $(document.body).append(modalStr);
    } else if ($('#wok-confirm-modal ').size() < 1) {
        $('#modalWindow').after(modalStr);
    }

    var confirmboxHeader = [
                '<div class="modal-header', (settings.title === '' || typeof settings.title === 'undefined' ? ' icon' : '' ) ,'">',
                    '<h4 class="modal-title"><i class="fa fa-exclamation-triangle"></i>'+(settings.title || '')+'</h4>',
                '</div>'
    ].join('');

    var confirmboxHtml = [
        '<div class="modal-dialog  modal-sm">',
            '<div class="modal-content">',
                confirmboxHeader,
                '<div class="modal-body">',
                    settings.content,
                '</div>',
                '<div class="modal-footer">',
                    '<button id="button-confirm" class="btn btn-default">' + (settings.confirm || i18n['WOKAPI6004M']) + '</button>',
                    '<button id="button-cancel" class="btn btn-default">' + (settings.cancel || i18n['WOKAPI6003M']) + '</button>',
                '</div>',
            '</div>',
        '</div>'
    ].join('');
    var confirmboxNode = $(confirmboxHtml);
    $('#wok-confirm-modal').append(confirmboxNode);
    $('#wok-confirm-modal').modal('show');
    $('#wok-confirm-modal').on("click", "#button-confirm", function(e) {
        if (confirmCallback) {
            confirmCallback();
        }
        $('#wok-confirm-modal').modal('hide');
    });
    $('#wok-confirm-modal').on("click", "#button-cancel", function(e) {
        if (cancelCallback) {
            cancelCallback();
        }
        $('#wok-confirm-modal').modal('hide');
    });

    $('#wok-confirm-modal').on('hidden.bs.modal', function () {
        close();
    });

    var close = function(){
        "use strict";
        $('#wok-confirm-modal').removeData('bs.modal');
        $('#wok-confirm-modal').remove();
    };

};