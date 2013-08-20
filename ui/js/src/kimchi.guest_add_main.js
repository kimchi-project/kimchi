/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwanghl@cn.ibm.com>
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
kimchi.guest_add_main = function() {
    kimchi.listTemplates(function(result) {
        if (result && result.length) {
            var html = '';
            var tmpl = $('#tmpl-template').html();
            $.each(result, function(index, value) {
                html += kimchi.template(tmpl, value);
            });
            $('#templateTile').html(html);
        }
    }, function() {
        kimchi.message.error(i18n['temp.msg.fail.list']);
    });

    function validateForm() {
        if (!$('input[name=template]:checked', '#templateTile').val()) {
            return false;
        }
        return true;
    }

    $('#form-vm-add').change(function() {
        if (validateForm()) {
            $('#vm-doAdd').removeAttr('disabled');
        }
    });

    var addGuest = function(event) {
        var formData = $('#form-vm-add').serializeObject();

        kimchi.createVM(formData, function() {
            kimchi.listVmsAuto();
            kimchi.window.close();
        }, function() {
            kimchi.message.error(i18n['vm.msg.fail.create.vm']);
        });

        return false;
    };

    $('#form-vm-add').on('submit', addGuest);
    $('#vm-doAdd').on('click', addGuest);
};
