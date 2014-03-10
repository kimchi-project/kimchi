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
kimchi.guest_storage_add_main = function() {
    var types = [{
        label: 'cdrom',
        value: 'cdrom'
    }];
    kimchi.select('guest-storage-type-list', types);

    var storageAddForm = $('#form-guest-storage-add');
    var submitButton = $('#guest-storage-button-add');
    var nameTextbox = $('input[name="dev"]', storageAddForm);
    var typeTextbox = $('input[name="type"]', storageAddForm);
    var pathTextbox = $('input[name="path"]', storageAddForm);
    var errorMessage = $('#storage-error-message');

    var submitForm = function(event) {
        if(submitButton.prop('disabled')) {
            return false;
        }

        var dev = nameTextbox.val();
        var type = typeTextbox.val();
        var path = pathTextbox.val();
        if(!path || path === '') {
            return false;
        }

        var formData = storageAddForm.serializeObject();
        $.each([submitButton, nameTextbox, pathTextbox], function(i, c) {
            $(c).prop('disabled', true);
        });
        $(submitButton).addClass('loading').text(i18n['KCHVMCD6003M']);
        $(errorMessage).text('');

        var settings = {
            vm: kimchi.selectedGuest,
            type: type,
            path: path
        };

        if(dev && dev !== '') {
            settings['dev'] = dev;
        }

        kimchi.addVMStorage(settings, function(result) {
            kimchi.window.close();
            kimchi.topic('kimchi/vmCDROMAttached').publish({
                result: result
            });
        }, function(result) {
            var errText = result['reason'] ||
                result['responseJSON']['reason'];
            $(errorMessage).text(errText);

            $.each([submitButton, nameTextbox, pathTextbox], function(i, c) {
                $(c).prop('disabled', false);
            });
            $(submitButton).removeClass('loading').text(i18n['KCHVMCD6002M']);
        });

        event.preventDefault();
    };

    storageAddForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
    pathTextbox.on('input propertychange', function(event) {
        $(submitButton).prop('disabled', $(this).val() === '');
    });
};
