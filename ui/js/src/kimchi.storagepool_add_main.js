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

kimchi.storagepool_add_main = function() {
    kimchi.initStorageAddPage();
    $('#form-pool-add').on('submit', kimchi.addPool);
    $('#pool-doAdd').on('click', kimchi.addPool);
};

kimchi.initStorageAddPage = function() {
    kimchi.listHostPartitions(function(data) {
        if (data.length > 0) {
            var deviceHtml = $('#partitionTmpl').html();
            var listHtml = '';
            valid_types = ['part', 'disk', 'mpath'];
            $.each(data, function(index, value) {
                if (valid_types.indexOf(value.type) != -1) {
                    listHtml += kimchi.substitute(deviceHtml, value);
                }
            });
            $('.host-partition', '#form-pool-add').html(listHtml);
        } else {
            $('.host-partition').html(i18n['KCHPOOL6011M']);
            $('.host-partition').addClass('text-help');
        }
    });

    kimchi.getHostPCIDevices(function(data){
        if(data.length>0){
            for(var i=0;i<data.length;i++){
                data[i].label = data[i].name;
                data[i].value = data[i].name;
            }
            $('#scsiAdapter').selectMenu();
            $("input", "#scsiAdapter").val(data[0].name);
            $('#scsiAdapter').selectMenu("setData", data);
        } else {
            $('#scsiAdapter').html(i18n['KCHPOOL6005M']);
            $('#scsiAdapter').addClass('text-help');
        }
    });

    $('#poolTypeId').selectMenu();
    $('#serverComboboxId').combobox();
    $('#targetFilterSelectId').filterselect();
    var options = [ {
        label : "DIR",
        value : "dir"
    }, {
        label : "NFS",
        value : "netfs"
    }, {
        label : "iSCSI",
        value : "iscsi"
    }, {
        label : "LOGICAL",
        value : "logical"
    }, {
        label : i18n.KCHPOOL6004M,
        value : "scsi"
    } ];
    $('#poolTypeId').selectMenu("setData", options);
 
    kimchi.getStorageServers('netfs', function(data) {
        var serverContent = [];
        if (data.length > 0) {
            $.each(data, function(index, value) {
                serverContent.push({
                    label : value.host,
                    value : value.host
                });
            });
        }
        $('#serverComboboxId').combobox("setData", serverContent);
        $('input[name=nfsServerType]').change(function() {
            if ($(this).val() === 'input') {
                $('#nfsServerInputDiv').removeClass('tmpl-html');
                $('#nfsServerChooseDiv').addClass('tmpl-html');
            } else {
                $('#nfsServerInputDiv').addClass('tmpl-html');
                $('#nfsServerChooseDiv').removeClass('tmpl-html');
            }
        });
        $('#nfsserverId').on("change keyup",function() {
            if ($(this).val() !== '' && kimchi.isServer($(this).val())) {
                $('#nfspathId').prop('disabled',false);
                $(this).removeClass("invalid-field");
            } else {
                $(this).addClass("invalid-field");
                $('#nfspathId').prop( "disabled",true);
            }
            $('#targetFilterSelectId').filterselect('clear');
        });
        $('#nfspathId').focus(function() {
            var targetContent = [];
            kimchi.getStorageTargets($('#nfsserverId').val(), 'netfs', function(data) {
                if (data.length > 0) {
                    $.each(data, function(index, value) {
                        targetContent.push({
                            label : value.target,
                            value : value.target
                        });
                    });
                }
                $('#targetFilterSelectId').filterselect("setData", targetContent);
            });
        });
    });

    $('#poolTypeInputId').change(function() {
        var poolObject = {'dir': ".path-section", 'netfs': '.nfs-section',
                          'iscsi': '.iscsi-section', 'scsi': '.scsi-section',
                          'logical': '.logical-section'}
        var selectType = $(this).val();
        $.each(poolObject, function(type, value) {
            if(selectType == type){
                $(value).removeClass('tmpl-html');
            } else {
                $(value).addClass('tmpl-html');
            }
        });
    });
    $('#authId').click(function() {
        if ($(this).prop("checked")) {
            $('.authenticationfield').removeClass('tmpl-html');
        } else {
            $('.authenticationfield').addClass('tmpl-html');
        }
    });
    $('#iscsiportId').keyup(function(event) {
        $(this).toggleClass("invalid-field",!/^[0-9]+$/.test($(this).val()));
    });
};

kimchi.validateForm = function() {
    var name = $('#poolId').val();
    var poolType = $("#poolTypeInputId").val();
    if ('' === name) {
        kimchi.message.error.code('KCHPOOL6001E');
        return false;
    }
    if (name.indexOf("/")!=-1) {
        kimchi.message.error.code('KCHPOOL6004E');
        return false;
    }
    if (poolType === "dir") {
        return kimchi.validateDirForm();
    } else if (poolType === "netfs") {
        return kimchi.validateNfsForm();
    } else if (poolType === "iscsi") {
        return kimchi.validateIscsiForm();
    } else if (poolType === "logical") {
        return kimchi.validateLogicalForm();
    } else {
        return true;
    }
};

kimchi.validateDirForm = function () {
    var path = $('#pathId').val();
    if ('' === path) {
        kimchi.message.error.code('KCHPOOL6002E');
        return false;
    }
    if (!/(^\/.*)$/.test(path)) {
        kimchi.message.error.code('KCHAPI6003E');
        return false;
    }
    return true;
};

kimchi.validateNfsForm = function () {
    var nfspath = $('#nfspathId').val();
    var nfsserver = $('#nfsserverId').val();
    if (!kimchi.validateServer(nfsserver)) {
        return false;
    }
    if ('' === nfspath) {
        kimchi.message.error.code('KCHPOOL6003E');
        return false;
    }
    if (!/((\/([0-9a-zA-Z-_\.]+)))$/.test(nfspath)) {
        kimchi.message.error.code('KCHPOOL6005E');
        return false;
    }
    return true;
};

kimchi.validateIscsiForm = function() {
    var iscsiServer = $('#iscsiserverId').val();
    var iscsiTarget = $('#iscsiTargetId').val();
    if (!kimchi.validateServer(iscsiServer)) {
        return false;
    }
    if ('' === iscsiTarget) {
        kimchi.message.error.code('KCHPOOL6007E');
        return false;
    }
    return true;
};

kimchi.validateServer = function(serverField) {
    if ('' === serverField) {
        kimchi.message.error.code('KCHPOOL6008E');
        return false;
    }
    if(!kimchi.isServer(serverField)) {
        kimchi.message.error.code('KCHPOOL6009E');
        return false;
    }
    return true;
};

kimchi.validateLogicalForm = function () {
    if ($("input[name=devices]:checked").length === 0) {
        kimchi.message.error.code('KCHPOOL6006E');
        return false;
    } else {
        return true;
    }
};

kimchi.addPool = function(event) {
    if (kimchi.validateForm()) {
        var formData = $('#form-pool-add').serializeObject();
        delete formData.authname;
        var poolType = $('#poolTypeId').selectMenu('value');
        if (poolType === 'dir') {
            formData.path = $('#pathId').val();
        } else if (poolType === 'logical') {
            var source = {};
            if (!$.isArray(formData.devices)) {
                var deviceObj = [];
                deviceObj[0] =  formData.devices;
                source.devices = deviceObj;
            } else {
                source.devices = formData.devices;
            }
            delete formData.devices;
            formData.source = source;
        } else if (poolType === 'netfs'){
            var source = {};
            source.path = $('#nfspathId').val();
            source.host = $('#nfsserverId').val();
            formData.source = source;
        } else if (poolType === 'iscsi') {
            var source = {};
            source.target = $('#iscsiTargetId').val();
            source.host = $('#iscsiserverId').val();
            $('#iscsiportId').val() !== '' ? source.port = parseInt($('#iscsiportId').val()): null;
            if ($('#authId').prop("checked")) {
                source.auth = {
                    "username" : $('#usernameId').val(),
                    "password" : $('#passwordId').val()
                };
            }
            formData.source = source;
        } else if (poolType === 'scsi'){
            formData.source = { adapter_name: $('#scsiAdapter').selectMenu('value') };
        }
        if (poolType === 'logical') {
            var settings = {
                title : i18n['KCHAPI6001M'],
                content : i18n['KCHPOOL6003M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            };
            kimchi.confirm(settings, function() {
                kimchi.createStoragePool(formData, function() {
                    kimchi.doListStoragePools();
                    kimchi.window.close();
                }, function(err) {
                    kimchi.message.error(err.responseJSON.reason);
                });
            }, function() {
            });
        } else {
            kimchi.createStoragePool(formData, function() {
                kimchi.doListStoragePools();
                kimchi.window.close();
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            });
        }
    }
};
