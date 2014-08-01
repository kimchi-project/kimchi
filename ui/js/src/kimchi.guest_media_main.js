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
kimchi.guest_media_main = function() {

    var refreshCDROMs = function() {
        kimchi.listVMStorages({
            vm: kimchi.selectedGuest,
            storageType: 'cdrom'
        }, function(storages) {
            var rowHTML = $('#cdrom-row-tmpl').html();
            var container = $('#guest-edit-cdrom-row-container');
            $(container).empty();

            $.each(storages, function(index, storage) {
                storage['vm'] = kimchi.selectedGuest;
                var templated = kimchi.substitute(rowHTML, storage);
                container.append(templated);
            });

            var replaceCDROM = function(event) {
                event.preventDefault();
                kimchi.selectedGuestStorage = $(this).data('dev');
                kimchi.window.open("guest-cdrom-edit.html");
            };

            $('input[type="text"][name="cdrom"]', container).on('click', replaceCDROM);
            $('.replace', container).on('click', replaceCDROM);
        });
    };

    refreshCDROMs();

    var onReplaced = function(params) {
        refreshCDROMs();
    };
    kimchi.topic('kimchi/vmCDROMReplaced').subscribe(onReplaced);

    kimchi.clearGuestMedia = function() {
        kimchi.topic('kimchi/vmCDROMReplaced').unsubscribe(onReplaced);
    };
};
