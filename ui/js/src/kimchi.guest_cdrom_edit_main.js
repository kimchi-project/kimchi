/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
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
kimchi.guest_cdrom_edit_main = function() {
    var cdromEditForm = $('#form-vm-cdrom-edit');
    var submitButton = $('#vm-cdrom-button-edit');
    var nameTextbox = $('input[name="dev"]', cdromEditForm);
    var typeTextbox = $('input[name="type"]', cdromEditForm);
    var pathTextbox = $('input[name="path"]', cdromEditForm);
    var errorMessage = $('#cdrom-error-message');
    var originalPath = null;

    kimchi.retrieveVMStorage({
        vm: kimchi.selectedGuest,
        dev: kimchi.selectedGuestStorage
    }, function(storage) {
        for(var prop in storage) {
            $('input[name="' + prop + '"]', cdromEditForm).val(storage[prop]);
        }

        originalPath = storage['path'];
    });

    var submitForm = function(event) {
        if(submitButton.prop('disabled')) {
            return false;
        }

        var path = pathTextbox.val();
        if(!path || path === '') {
            return false;
        }

        $.each([submitButton, nameTextbox, pathTextbox], function(i, c) {
            $(c).prop('disabled', true);
        });
        $(submitButton).addClass('loading').text(i18n['KCHVMCD6005M']);
        $(errorMessage).text('');

        var settings = {
            vm: kimchi.selectedGuest,
            dev: kimchi.selectedGuestStorage,
            path: path
        };

        kimchi.replaceVMStorage(settings, function(result) {
            kimchi.window.close();
            kimchi.topic('kimchi/vmCDROMReplaced').publish({
                result: result
            });
        }, function(result) {
            var errText = result['reason'] ||
                result['responseJSON']['reason'];
            $(errorMessage).text(errText);

            $.each([submitButton, nameTextbox, pathTextbox], function(i, c) {
                $(c).prop('disabled', false);
            });
            $(submitButton).removeClass('loading').text(i18n['KCHVMCD6004M']);
        });

        event.preventDefault();
    };

    cdromEditForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
    pathTextbox.on('input propertychange', function(event) {
        var invalid =
            ($(this).val() === originalPath) ||
            ($(this).val() === '');
        $(submitButton).prop('disabled', invalid);
    });
};
