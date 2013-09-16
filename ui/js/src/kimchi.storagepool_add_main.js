/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Mei Na Zhou <zhoumein@linux.vnet.ibm.com>
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
kimchi.storagepool_add_main = function() {
    function validateForm() {
        var name = $('#poolId').val();
        var path = $('#pathId').val();

        if (name === '') {
            kimchi.message.error(i18n['msg.pool.edit.name.blank']);
            return false;
        }

        if (path === '') {
            kimchi.message.error(i18n['msg.pool.edit.path.blank']);
            return false;
        }
        if (!/^[\w-]+$/.test(name)) {
            kimchi.message.error(i18n['msg.validate.pool.edit.name']);
            return false;
        }
        if (!/((\/([0-9a-zA-Z-_\.]+)))$/.test(path)) {
            kimchi.message.error(i18n['msg.validate.pool.edit.path']);
            return false;
        }
        return true;
    }
    function addPool(event) {
        if (validateForm()) {
            var formData = $('#form-pool-add').serializeObject();
            kimchi.createStoragePool(formData, function() {
                kimchi.doListStoragePools();
                kimchi.window.close();
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            });
        }

    }
    $('#form-pool-add').on('submit', addPool);
    $('#pool-doAdd').on('click', addPool);
};
