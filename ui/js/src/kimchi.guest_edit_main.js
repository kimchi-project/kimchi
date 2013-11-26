/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwang@linux.vnet.ibm.com>
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
kimchi.guest_edit_main = function() {
    var guestEditForm = $('#form-guest-edit');
    var saveButton = $('#guest-edit-button-save');
    kimchi.retrieveVM(kimchi.selectedGuest, function(guest) {
        guest['icon'] = guest['icon'] || 'images/icon-vm.png';
        for ( var prop in guest) {
            $('input[name="' + prop + '"]', guestEditForm).val(guest[prop]);
        }
    });

    $('#guest-edit-button-cancel').on('click', function() {
        kimchi.window.close();
    });

    var submitForm = function(event) {
        $(saveButton).prop('disabled', true);
        var editableFields = [ 'name' ];
        var data = {};
        $.each(editableFields, function(i, field) {
            data[field] = $('#form-guest-edit [name="' + field + '"]').val();
        });
        kimchi.updateVM(kimchi.selectedGuest, data, function() {
            kimchi.listVmsAuto();
            kimchi.window.close();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
        event.preventDefault();
    };

    $(guestEditForm).on('submit', submitForm);
    $(saveButton).on('click', submitForm);
};
