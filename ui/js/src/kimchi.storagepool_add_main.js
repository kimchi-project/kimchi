/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Mei Na Zhou <zhoumein@linux.vnet.ibm.com>
 *  Pradeep K Surisetty <psuriset@linux.vnet.ibm.com>
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

    kimchi.bindSwitchPages();
    $('#form-pool-add').on('submit', kimchi.addPool);
    $('#form-nfs-pool-add').on('submit', kimchi.addnfsPool);
    $('#pool-doAdd').on('click', kimchi.addPool);
    $('#pool-nfs-doAdd').on('click', kimchi.addnfsPool);
};

kimchi.bindSwitchPages =  function () {
    $('#dir-back').click(function() {
        kimchi.switchPage('storage-type-box', 'storage-dir-box');
    });

    $('#nfs-back').click(function() {
        kimchi.switchPage('storage-type-box', 'storage-nfs-box');
    });

    $('#storage-dir-box-back').click(function() {
        kimchi.switchPage('storage-dir-box', 'storage-type-box', 'right');
    });

    $('#storage-nfs-box-back').click(function() {
        kimchi.switchPage('storage-nfs-box', 'storage-type-box', 'right');
    });
};

kimchi.validatenfsForm = function () {
    var name = $('#nfspoolId').val();
    var nfspath = $('#nfspathId').val();
    var nfsserver = $('#nfsserverId').val();
    var path = $('#localpathId').val('/var/lib/kimchi/nfs_mount/'+ name);

    if ('' === name) {
        kimchi.message.error(i18n['msg.pool.edit.name.blank']);
        return false;
    }

    if ('' === path) {
        kimchi.message.error(i18n['msg.pool.edit.path.blank']);
        return false;
    }

    if ('' === nfsserver) {
        kimchi.message.error(i18n['msg.pool.edit.nfsserver.blank']);
        return false;
    }

    if ('' === nfspath) {
        kimchi.message.error(i18n['msg.pool.edit.nfspath.blank']);
        return false;
    }
    if (!/^(?![0-9]+$)(?!.*-$)(?!-)[a-zA-Z0-9-]{1,63}$/g.test(name)) {
        kimchi.message.error(i18n['msg.validate.pool.edit.name']);
        return false;
    }

    var domain = "([0-9a-z_!~*'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6}"
    var ip = "(\\d{1,3}\.){3}\\d{1,3}"
    regex = new RegExp('^' + domain + '|' + ip + '$')

    if(!regex.test(nfsserver)) {
        kimchi.message.error(i18n['msg.validate.pool.edit.nfsserver']);
        return false;
    }

    if (!/((\/([0-9a-zA-Z-_\.]+)))$/.test(nfspath)) {
        kimchi.message.error(i18n['msg.validate.pool.edit.nfspath']);
        return false;
    }

    return true;
};

kimchi.validateForm = function () {
    var name = $('#poolId').val();
    var path = $('#pathId').val();

    if ('' === name) {
        kimchi.message.error(i18n['msg.pool.edit.name.blank']);
        return false;
    }

    if ('' === path) {
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
};

kimchi.addPool =  function (event) {
    if (kimchi.validateForm()) {
        var formData = $('#form-pool-add').serializeObject();
        kimchi.createStoragePool(formData, function() {
            kimchi.doListStoragePools();
            kimchi.window.close();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    }
};

kimchi.addnfsPool = function (event) {
    if (kimchi.validatenfsForm()) {
        var formData = $('#form-nfs-pool-add').serializeObject();
        kimchi.createStoragePool(formData, function() {
            kimchi.doListStoragePools();
            kimchi.window.close();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    }
};
