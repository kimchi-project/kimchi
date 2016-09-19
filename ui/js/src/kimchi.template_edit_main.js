/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2013-2016
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
kimchi.template_edit_main = function() {
    var templateEditMain = $('#edit-template-tabs');
    var origDisks;
    var origNetworks;
    var origInterfaces;
    var origmacvtapNetworks;
    var origovsNetworks;
    var templateDiskSize;
    var baseImageTemplate;
    var s390xArch = 's390x';

    $('#template-name', templateEditMain).val(kimchi.selectedTemplate);
    $('#edit-template-tabs a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
        $('.tab-content').css('overflow', 'hidden');
        var target = $(this).attr('href');
        $(target).css('left', '-' + $(window).width() + 'px');
        var left = $(target).offset().left;
        $(target).css({
            left: left
        }).animate({
            "left": "0px"
        }, 400, function() {
            $('.tab-content').css('overflow', 'visible');
        });
    });

    $('#template-show-max-memory').on('click', function(e) {
        e.preventDefault;
        $('.max-memory-field').slideToggle();
        var text = $('#template-show-max-memory span.text').text();
        $('#template-show-max-memory span.text').text(text == i18n['KCHVMED6008M'] ? i18n['KCHVMED6009M'] : i18n['KCHVMED6008M']);
        $('#template-show-max-memory i.fa').toggleClass('fa-plus-circle fa-minus-circle');
    });

    var initTemplate = function(template) {
        origDisks = template.disks;
        origNetworks = template.networks;
        origInterfaces = template.interfaces;
        for (var i = 0; i < template.disks.length; i++) {
            if (template.disks[i].base) {
                template["vm-image"] = template.disks[i].base;
                $('.templ-edit-cdrom').addClass('hide');
                $('.templ-edit-vm-image').removeClass('hide');
                break;
            }
        }
        for (var prop in template) {
            var value = template[prop];
            if (prop == 'graphics') {
                value = value["type"];
            }
            $('input[name="' + prop + '"]', templateEditMain).val(value);
        }
        if(kimchi.hostarch == s390xArch){
            $('.graphics', templateEditMain).hide();
            $('.console', templateEditMain).show();
            var consoleData = template.console ? template.console : '';
            $('#template-edit-console', templateEditMain).val(consoleData);
            $('#template-edit-console').selectpicker();
        }

        $('#template-edit-memory-textbox').val(template.memory.current);
        $('#template-edit-max-memory-textbox').val(template.memory.maxmemory);

        if (template.graphics.type == 'vnc') {
            $('#template-edit-graphics').append('<option value="vnc" selected="selected">VNC</option>');
        } else {
            $('#template-edit-graphics').append('<option value="vnc">VNC</option>');
        }
        var enableSpice = function() {
            if (kimchi.capabilities == undefined) {
                setTimeout(enableSpice, 2000);
                return;
            }
            if (kimchi.capabilities.qemu_spice == true) {
                if (template.graphics.type == 'spice') {
                    $('#template-edit-graphics').append('<option value="spice" selected="selected">Spice</option>');
                } else {
                    $('#template-edit-graphics').append('<option value="spice">Spice</option>');
                }
            }
        };
        var isImageBasedTemplate = function() {
            if (template["vm-image"] && typeof template["vm-image"] == "string") {
                return true;
            }
            return false;
        }
        baseImageTemplate = isImageBasedTemplate();
        enableSpice();
        $('#template-edit-graphics').selectpicker();

        var initStorage = function(result) {
            // Gather storagepools data
            var storagePoolsInfo = new Object();
            $.each(result, function(index, pool) {
                if (pool.state === 'active' && pool.type != 'kimchi-iso') {
                    if (pool.type === 'iscsi' || pool.type === 'scsi') {
                        volumes = new Object();
                        kimchi.listStorageVolumes(pool.name, function(vols) {
                            $.each(vols, function(i, vol) {
                                storagePoolsInfo[pool.name + "/" + vol.name] = {
                                    'type': pool.type,
                                    'volSize': vol.capacity / Math.pow(1024, 3)
                                };
                            });
                        }, null, true);
                    } else {
                        storagePoolsInfo[pool.name] = { 'type': pool.type };
                    }
                }
            });

            var addStorageItem = function(storageData) {
                var thisName = storageData.storageName;
                // Compatibility with old versions
                if (storageData.storageVolume) {
                    storageData.storageDisk = storagePoolsInfo[thisName].volSize;
                }
                if (!storageData.storageType) {
                    storageData.storageType = storagePoolsInfo[thisName].type;
                }

                var nodeStorage = $.parseHTML(wok.substitute($('#template-storage-pool-tmpl').html(), storageData));
                $('.template-tab-body', '#form-template-storage').append(nodeStorage);
                var storageRow = '#storageRow' + storageData.storageIndex;

                var storageOptions = '';
                $.each(storagePoolsInfo, function(poolName, value) {
                    storageOptions += '<option value="' + poolName + '">' + poolName + '</option>';
                });

                $(storageRow + ' .selectStorageName').append(storageOptions);
                if (!$(storageRow + ' .selectStorageName option[value="' + storageData.storageName + '"]').length) {
                    var invalidOption = '<option disabled="disabled" selected="selected" value="' + storageData.storageName + '">' + storageData.storageName + '</option>';
                    $(storageRow + ' .selectStorageName').prepend(invalidOption);
                    $(storageRow + ' .selectStorageName').parent().addClass('has-error')
                }
                $(storageRow + ' .selectStorageName').val(storageData.storageName);
                $(storageRow + ' .selectStorageName').selectpicker();

                if (storageData.storageType === 'iscsi' || storageData.storageType === 'scsi') {
                    $(storageRow + ' .template-storage-disk').attr('readonly', true).prop('disabled', true);
                    $(storageRow + ' #diskFormat').val('raw');
                    $(storageRow + ' #diskFormat').prop('disabled', true).change();
                } else if (storageData.storageType === 'logical') {
                    $(storageRow + ' #diskFormat').val('raw');
                    $(storageRow + ' #diskFormat').prop('disabled', true).change();
                }

                // Set disk format
                if (isImageBasedTemplate()) {
                    $(storageRow + ' #diskFormat').val('qcow2');
                    $(storageRow + ' #diskFormat').prop('disabled', 'disabled');
                } else {
                    $(storageRow + ' #diskFormat').val(storageData.storageDiskFormat);
                    $(storageRow + ' #diskFormat').on('change', function() {
                        $(storageRow + ' .template-storage-disk-format').val($(this).val());
                    });
                }
                $(storageRow + ' #diskFormat').selectpicker();

                $('.delete', '#form-template-storage').on("click", function(event) {
                    event.preventDefault();
                    $(this).parent().parent().remove();
                });

                $(storageRow + ' select.selectStorageName').change(function() {
                    $(this).parent().parent().removeClass('has-error');
                    var poolType = storagePoolsInfo[$(this).val()].type;
                    $(storageRow + ' .template-storage-name').val($(this).val());
                    $(storageRow + ' .template-storage-type').val(poolType);
                    if (poolType === 'iscsi' || poolType === 'scsi') {
                        $(storageRow + ' .template-storage-disk').attr('readonly', true).prop('disabled', true).val(storagePoolsInfo[$(this).val()].volSize);
                        if (!isImageBasedTemplate()) {
                            $(storageRow + ' #diskFormat').val('raw').prop('disabled', true).change();
                        }
                    } else if (poolType === 'logical') {
                        $(storageRow + ' .template-storage-disk').attr('readonly', false).prop('disabled', false);
                        if (!isImageBasedTemplate()) {
                            $(storageRow + ' #diskFormat').val('raw').prop('disabled', true).change();
                        }
                    } else {
                        $(storageRow + ' .template-storage-disk').attr('readonly', false).prop('disabled', false);
                        if ($(storageRow + ' #diskFormat').prop('disabled') == true && !isImageBasedTemplate()) {
                            $(storageRow + ' #diskFormat').val('qcow2').prop('disabled', false).change();
                        }
                    }
                    $(storageRow + ' #diskFormat').selectpicker('refresh');
                });
            }; // End of addStorageItem funtion

            if (origDisks && origDisks.length) {
                origDisks.sort(function(a, b) {
                    return a.index - b.index });
                $.each(origDisks, function(index, diskEntities) {
                    var defaultPool = diskEntities.pool.name.split('/').pop()
                    var storageNodeData = {
                        storageIndex: diskEntities.index,
                        storageName: diskEntities.volume ? defaultPool + '/' + diskEntities.volume : defaultPool,
                        storageType: diskEntities.pool.type,
                        storageDisk: diskEntities.size,
                        storageDiskFormat: diskEntities.format ? diskEntities.format : 'qcow2',
                        storageVolume: diskEntities.volume
                    }
                    addStorageItem(storageNodeData);
                });
            }

            var storageID = origDisks.length - 1;
            $('#template-edit-storage-add-button').on("click", function(event) {
                event.preventDefault();
                storageID = storageID + 1;
                var storageNodeData = {
                    storageName: 'default',
                    storageType: 'dir',
                    storageDisk: '10',
                    storageDiskFormat: 'qcow2',
                    storageIndex: storageID
                }
                addStorageItem(storageNodeData);
            });
        };

        var initStorage_s390 = function(result) {
            // Gather storage data
            var storagePoolsInfo = new Object();
            $.each(result, function(index, pool) {
                if (pool.state === 'active' && pool.type != 'kimchi-iso') {
                    if (pool.type === 'iscsi' || pool.type === 'scsi') {
                        volumes = new Object();
                        kimchi.listStorageVolumes(pool.name, function(vols) {
                            $.each(vols, function(i, vol) {
                                storagePoolsInfo[pool.name + "/" + vol.name] = {
                                    'type': pool.type,
                                    'volSize': vol.capacity / Math.pow(1024, 3)
                                };
                            });
                        }, null, true);
                    } else {
                        storagePoolsInfo[pool.name] = {
                            'type': pool.type
                        };
                    }
                }
            });

            var addStorageItem = function(storageData) {
                if (storageData.storageSource == 'pool') {
                    var thisName = storageData.storageName;
                    // Compatibility with old versions
                    if (storageData.storageVolume) {
                        storageData.storageDisk = storagePoolsInfo[thisName].volSize;
                    }
                    if (!storageData.storageType) {
                        storageData.storageType = storagePoolsInfo[thisName].type;
                    }
                }

                var nodeStorage = $.parseHTML(wok.substitute($('#template-storage-pool-tmpl').html(), storageData));
                $('.template-tab-body', '#form-template-storage').append(nodeStorage);
                var storageRow = '#storageRow' + storageData.storageIndex;

                var storageOptions = '';
                $.each(storagePoolsInfo, function(poolName, value) {
                    storageOptions += '<option value="' + poolName + '">' + poolName + '</option>';
                });

                $(storageRow + ' .selectStorageName').append(storageOptions);
                if (storageData.storageSource == 'pool') {
                    if (!$(storageRow + ' .selectStorageName option[value="' + storageData.storageName + '"]').length) {
                        var invalidOption = '<option disabled="disabled" selected="selected" value="' + storageData.storageName + '">' + storageData.storageName + '</option>';
                        $(storageRow + ' .selectStorageName').prepend(invalidOption);
                        $(storageRow + ' .selectStorageName').parent().addClass('has-error')
                    }
                    $(storageRow + ' .selectStorageName').val(storageData.storageName);
                    $(storageRow + ' span.storage-pool').show();
                    $(storageRow + ' span.storage-path').hide();
                } else {
                    $(storageRow + ' span.storage-pool').hide();
                    $(storageRow + ' span.storage-path').show();
                }

                $(storageRow + ' .selectStorageName').selectpicker();
                if (storageData.storageType === 'iscsi' || storageData.storageType === 'scsi') {
                    $(storageRow + ' .template-storage-disk').attr('readonly', true).prop('disabled', true);
                    $(storageRow + ' #diskFormat').val('raw');
                    $(storageRow + ' #diskFormat').prop('disabled', true).change();
                } else if (storageData.storageType === 'logical') {
                    $(storageRow + ' #diskFormat').val('raw');
                    $(storageRow + ' #diskFormat').prop('disabled', true).change();
                }

                //set source
                $('#form-template-storage span.source').show();
                $(storageRow + ' #source').val(storageData.storageSource);
                $(storageRow + ' #source').on('change', function() {
                    var source = $(this).val();
                    $(storageRow + ' .template-storage-source').val(source);
                    if (source == 'path') {
                        $(storageRow + ' span.storage-pool').hide();
                        $(storageRow + ' span.storage-path').show();
                    } else {
                        $(storageRow + ' span.storage-pool').show();
                        $(storageRow + ' span.storage-path').hide();
                    }
                });

                $(storageRow + ' #source').selectpicker();

                // Set disk format
                if (isImageBasedTemplate()) {
                    $(storageRow + ' #diskFormat').val('qcow2');
                    $(storageRow + ' #diskFormat').prop('disabled', 'disabled');
                } else {
                    $(storageRow + ' #diskFormat').val(storageData.storageDiskFormat);
                    $(storageRow + ' #diskFormat').on('change', function() {
                        $(storageRow + ' .template-storage-disk-format').val($(this).val());
                    });
                }
                $(storageRow + ' #diskFormat').selectpicker();

                $('.delete', '#form-template-storage').on("click", function(event) {
                    event.preventDefault();
                    $(this).parent().parent().remove();
                });

                $(storageRow + ' select.selectStorageName').change(function() {
                    $(this).parent().parent().removeClass('has-error');
                    var poolType = storagePoolsInfo[$(this).val()].type;
                    $(storageRow + ' .template-storage-name').val($(this).val());
                    $(storageRow + ' .template-storage-type').val(poolType);
                    if (poolType === 'iscsi' || poolType === 'scsi') {
                        $(storageRow + ' .template-storage-disk').attr('readonly', true).prop('disabled', true).val(storagePoolsInfo[$(this).val()].volSize);
                        if (!isImageBasedTemplate()) {
                            $(storageRow + ' #diskFormat').val('raw').prop('disabled', true).change();
                        }
                    } else if (poolType === 'logical') {
                        $(storageRow + ' .template-storage-disk').attr('readonly', false).prop('disabled', false);
                        if (!isImageBasedTemplate()) {
                            $(storageRow + ' #diskFormat').val('raw').prop('disabled', true).change();
                        }
                    } else {
                        $(storageRow + ' .template-storage-disk').attr('readonly', false).prop('disabled', false);
                        if ($(storageRow + ' #diskFormat').prop('disabled') == true && !isImageBasedTemplate()) {
                            $(storageRow + ' #diskFormat').val('qcow2').prop('disabled', false).change();
                        }
                    }
                    $(storageRow + ' #diskFormat').selectpicker('refresh');
                });
            }; // End of addStorageItem funtion

            if (origDisks && origDisks.length) {
                origDisks.sort(function(a, b) {
                    return a.index - b.index
                });
                $.each(origDisks, function(index, diskEntities) {
                    if (typeof diskEntities.pool !== 'undefined') {
                        var defaultPool = diskEntities.pool.name.split('/').pop()
                        var storageNodeData = {
                            storageSource: 'pool',
                            storageName: diskEntities.volume ? defaultPool + '/' + diskEntities.volume : defaultPool,
                            storageType: diskEntities.pool.type,
                            storageIndex: diskEntities.index,
                            storageDisk: diskEntities.size,
                            storageDiskFormat: diskEntities.format ? diskEntities.format : 'qcow2',
                            storageVolume: diskEntities.volume
                        }
                    } else {
                        var storageNodeData = {
                            storageSource: 'path',
                            storagePath: diskEntities.path,
                            storageType: 'dir',
                            storageIndex: diskEntities.index,
                            storageDisk: diskEntities.size,
                            storageDiskFormat: diskEntities.format ? diskEntities.format : 'qcow2',
                            storageVolume: diskEntities.volume
                        }
                    }
                    addStorageItem(storageNodeData);
                });
            }

            var storageID = origDisks.length - 1;
            $('#template-edit-storage-add-button').on("click", function(event) {
                event.preventDefault();
                storageID = storageID + 1;
                var storageNodeData = {
                    storageSource: 'pool',
                    storageName: 'default',
                    storageType: 'dir',
                    storageDisk: '10',
                    storageDiskFormat: 'qcow2',
                    storageIndex: storageID
                }
                addStorageItem(storageNodeData);
            });
        };

        var initInterface = function(result) {
            var networkItemNum = 0;
            var addInterfaceItem = function(networkData) {
                var networkName = networkData.networkV;
                var nodeInterface = $.parseHTML(wok.substitute($('#template-interface-tmpl').html(), networkData));
                $('.template-tab-body', '#form-template-interface').append(nodeInterface);
                $('.delete', '#form-template-interface').on("click", function(event) {
                    event.preventDefault();
                    $(this).parent().parent().remove();
                });
                var networkOptions = '';
                for (var i = 0; i < result.length; i++) {
                    if (networkName === result[i].name) {
                        networkOptions += '<option selected="selected">' + result[i].name + '</option>';
                    }
                    if (result[i].state === "active" && networkName !== result[i].name) {
                        networkOptions += '<option>' + result[i].name + '</option>';
                    }
                }
                $('select', '#form-template-interface #networkID' + networkItemNum).append(networkOptions);
                $('select', '#form-template-interface #networkID' + networkItemNum).selectpicker();
                networkItemNum += 1;
            };
            if (result && result.length > 0) {
                for (var i = 0; i < origNetworks.length; i++) {
                    addInterfaceItem({
                        networkID: 'networkID' + networkItemNum,
                        networkV: origNetworks[i],
                        type: 'network'
                    });
                }
            }
            $('#template-edit-interface-add-button').on("click", function(event) {
                event.preventDefault();
                addInterfaceItem({
                    networkID: 'networkID' + networkItemNum,
                    networkV: 'default',
                    type: 'network'
                });
            });
        };

        var initInterface_s390x = function(result) {
            $('#form-template-interface-s390x').show();
            $('#form-template-interface').hide();
            var networkItemNum = 0;
            var addInterfaceItem = function(networkData) {
                var networkName = networkData.networkV;
                var nodeInterface = $.parseHTML(wok.substitute($('#template-interface-s390x-tmpl').html(), networkData));
                $('.template-tab-body', '#form-template-interface-s390x').append(nodeInterface);
                $('.delete', '#form-template-interface-s390x').on("click", function(event) {
                    event.preventDefault();
                    $(this).parent().parent().remove();
                });

                //initialize type option
                var typeOptionsdata = {};
                var typeOptions = '';
                typeOptionsdata.macvtap = 'macvtap';
                typeOptionsdata.ovs = 'ovs';
                typeOptionsdata.network = 'network';

                $.each(typeOptionsdata, function(key, value) {
                    if (value === networkData.type) {
                        typeOptions += '<option  value="' + key + '" selected="selected">' + networkData.type + '</option>';
                    } else {
                        typeOptions += '<option value="' + key + '">' + value + '</option>';
                    }
                });

                $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.type').append(typeOptions);
                $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.type').on('change', function() {
                    var itemNode = $(this).closest('div.item');

                    switch ($(this).val()) {
                        case 'macvtap':
                            $('span.mode .label-mode', itemNode).addClass('hide');
                            $('span.mode .bootstrap-select', itemNode).toggleClass("hide", false);

                            var networkOptions = '';
                            for (var i = 0; i < origmacvtapNetworks.length; i++) {
                                networkOptions += '<option>' + origmacvtapNetworks[i].name + '</option>';
                            }

                            $('span.network select', itemNode).empty().append(networkOptions);
                            $('span.network select', itemNode).selectpicker('refresh');

                            break;
                        case 'ovs':
                            $('span.mode .label-mode', itemNode).removeClass('hide');
                            $('span.mode .bootstrap-select', itemNode).toggleClass("hide", true);
                            var networkOptions = '';
                            for (var i = 0; i < origovsNetworks.length; i++) {
                                networkOptions += '<option>' + origovsNetworks[i] + '</option>';
                            }

                            $('span.network select', itemNode).empty().append(networkOptions);
                            $('span.network select', itemNode).selectpicker('refresh');

                            break;
                        case 'network':
                            $('span.mode .label-mode', itemNode).removeClass('hide');
                            $('span.mode .bootstrap-select', itemNode).toggleClass("hide", true);

                            var networkOptions = '';
                            for (var i = 0; i < result.length; i++) {
                                if (result[i].state === "active") {
                                    networkOptions += '<option>' + result[i].name + '</option>';
                                }
                            }
                            $('span.network select', itemNode).empty().append(networkOptions);
                            $('span.network select', itemNode).selectpicker('refresh');
                            break;
                    }
                });

                switch (networkData.type) {
                    case 'macvtap':
                        //initialize network option
                        var networkOptions = '';
                        for (var i = 0; i < origmacvtapNetworks.length; i++) {
                            if (networkName === origmacvtapNetworks[i].name) {
                                networkOptions += '<option selected="selected">' + origmacvtapNetworks[i].name + '</option>';
                            }
                            networkOptions += '<option>' + origmacvtapNetworks[i].name + '</option>';
                        }
                        $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.network').append(networkOptions);

                        //initialize Mode option for Macvtap
                        $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.mode').val(networkData.mode);
                        $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.mode').selectpicker('refresh');

                        $('span.mode .label-mode', nodeInterface).addClass('hide');
                        $('span.mode .bootstrap-select', nodeInterface).removeClass("hide");

                        break;
                    case 'ovs':
                        var networkOptions = '';
                        for (var i = 0; i < origovsNetworks.length; i++) {
                            if (networkName === origovsNetworks[i]) {
                                networkOptions += '<option selected="selected">' + origovsNetworks[i] + '</option>';
                            }
                            networkOptions += '<option>' + origovsNetworks[i] + '</option>';
                        }
                        $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.network').append(networkOptions);

                        //initialize Mode option for ovs
                        $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.mode').selectpicker('refresh');
                        $('span.mode .label-mode', nodeInterface).removeClass('hide');
                        $('span.mode .bootstrap-select', nodeInterface).addClass("hide");
                        break;
                    case 'network':
                        var networkOptions = '';
                        for (var i = 0; i < result.length; i++) {
                            if (networkName === result[i].name) {
                                networkOptions += '<option selected="selected">' + result[i].name + '</option>';
                            }
                            if (result[i].state === "active" && networkName !== result[i].name) {
                                networkOptions += '<option>' + result[i].name + '</option>';
                            }
                        }
                        $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.network').append(networkOptions);

                        //initialize Mode option for Network
                        $('select', '#form-template-interface-s390x #networkID' + networkItemNum + ' span.mode').selectpicker('refresh');
                        $('span.mode .label-mode', nodeInterface).removeClass('hide');
                        $('span.mode .bootstrap-select', nodeInterface).addClass("hide");
                        break;
                }
                $('select', '#form-template-interface-s390x #networkID' + networkItemNum).selectpicker();
                networkItemNum += 1;
            };
            if (origInterfaces && origInterfaces.length > 0) {
                for (var i = 0; i < origInterfaces.length; i++) {
                    addInterfaceItem({
                        networkID: 'networkID' + networkItemNum,
                        networkV: origInterfaces[i].name,
                        type: origInterfaces[i].type,
                        mode: origInterfaces[i].mode
                    });
                }
            }
            if (result && result.length > 0) {
                for (var i = 0; i < origNetworks.length; i++) {
                    addInterfaceItem({
                        networkID: 'networkID' + networkItemNum,
                        networkV: origNetworks[i],
                        type: 'network'
                    });
                }
            }
            $('#template-edit-interface-add-button-s390x').on("click", function(event) {
                event.preventDefault();
                addInterfaceItem({
                    networkID: 'networkID' + networkItemNum,
                    networkV: 'default',
                    type: 'network',
                    mode: 'None'
                });
            });
        };

        var initProcessor = function(){
            var setCPUValue = function(){
                if(!$('#cores').hasClass("invalid-field")&&$('#cores').val()!=""){
                    var computedCpu = parseInt($("#cores").val())*parseInt($("#threads").val());
                    $("#vcpus").val(computedCpu);
                    if ($("#cpus-check").prop("checked")) {
                        //If topology is checked, set maxcpu to be the same as # of cpu otherwise, backend gives error
                        $("#guest-edit-max-processor-textbox").val(computedCpu);
                    }
                } else {
                    $("#vcpus").val('');
                }
            };
            $("input:text", "#form-template-processor").on('keyup', function() {
                $(this).toggleClass("invalid-field", !$(this).val().match('^[0-9]*$'));
                if ($(this).prop('id') == 'cores') setCPUValue();
            });
            $("input:checkbox", "#form-template-processor").click(function() {
                $('#threads').selectpicker();
                $(".topology", "#form-template-processor").slideToggle();
                $("#vcpus").attr("disabled", $(this).prop("checked"));
                $("#guest-edit-max-processor-textbox").attr("disabled", $(this).prop("checked"));
                setCPUValue();
            });
            $('#threads').change(function() {
                setCPUValue();
            });
            kimchi.getCPUInfo(function(data) {
                var options = "";
                var topo = template.cpu_info.topology;
                for (var i = 0; Math.pow(2, i) <= data.threads_per_core; i++) {
                    var lastOne = Math.pow(2, i + 1) > data.threads_per_core ? " selected" : "";
                    options += "<option" + lastOne + ">" + Math.pow(2, i) + "</option>";
                }
                $('#threads').append(options);
                if (template.cpu_info.vcpus) {
                    $("#vcpus").val(template.cpu_info.vcpus);
                }
                if (template.cpu_info.maxvcpus) {
                    $("#guest-edit-max-processor-textbox").val(template.cpu_info.maxvcpus);
                }
                if (topo && topo.cores) {
                    $("#cores").val(topo.cores);
                }
                if (topo && topo.threads) {
                    $('#threads').val(topo.threads);
                    $('#threads').selectpicker();
                    $("input:checkbox", "#form-template-processor").trigger('click');
                }
            });
            $('#guest-show-max-processor').on('click', function(e) {
                e.preventDefault;
                $('#guest-max-processor-panel').slideToggle();
                var text = $('#guest-show-max-processor span.text').text();
                $('#guest-show-max-processor span.text').text(text == i18n['KCHVMED6008M'] ? i18n['KCHVMED6009M'] : i18n['KCHVMED6008M']);
                $('#guest-show-max-processor i.fa').toggleClass('fa-plus-circle fa-minus-circle');
            });
        };

        var checkInvalids = function() {
            $.each(template.invalid, function(key, value) {
                if (key === 'cdrom' || key === 'vm-image') {
                    $('.tab-content input[name="' + key + '"]').attr('disabled', false).parent().addClass('has-error has-changes');
                    return true;
                } else if (key === 'storagepools') {
                    return true;
                } else {
                    return false;
                }
            });
        }

        if (kimchi.hostarch === s390xArch) {
            kimchi.listmacvtapNetworks(function(macvtapnet) {
                origmacvtapNetworks = macvtapnet;
                kimchi.listovsNetworks(function(ovsnet) {
                    origovsNetworks = ovsnet;
                    kimchi.listNetworks(initInterface_s390x);
                });
            });
            kimchi.listStoragePools(initStorage_s390);
        } else {
            kimchi.listNetworks(initInterface);
            kimchi.listStoragePools(initStorage);
        }

        initProcessor();
        checkInvalids();
    };
    kimchi.retrieveTemplate(kimchi.selectedTemplate, initTemplate);

    $('#tmpl-edit-button-save').on('click', function() {
        $button = $(this);
        $button.html('<span class="wok-loading-icon" /> ' + i18n['KCHAPI6010M']);
        $button.prop('disabled', true);
        $('.modal .wok-mask').removeClass('hidden');
        $('.modal input[type="text"]').prop('disabled', true);
        $('.modal input[type="checkbox"]').prop('disabled', true);
        $('.modal select').prop('disabled', true);
        $('.modal .selectpicker').addClass('disabled');
        if(kimchi.hostarch === s390xArch){
            var editableFields = ['name', 'memory', 'graphics', 'max-memory', 'console'];
        }else {
            var editableFields = ['name', 'memory', 'graphics', 'max-memory'];
        }

        var data = {};
        var disks = $('.template-tab-body .item', '#form-template-storage');
        var disksForUpdate = new Array();
        $.each(disks, function(index, diskEntity) {
            if (kimchi.hostarch == s390xArch && ($(diskEntity).find('.template-storage-source').val()) == 'path') {
                var newDisk = {
                    'index': index,
                    'path': $(diskEntity).find('.template-storage-path').val(),
                    'size': Number($(diskEntity).find('.template-storage-disk').val()),
                    'format': $(diskEntity).find('.template-storage-disk-format').val()
                };
            } else {
                var newDisk = {
                    'index': index,
                    'pool': {
                        'name': '/plugins/kimchi/storagepools/' + $(diskEntity).find('.template-storage-name').val()
                    },
                    'size': Number($(diskEntity).find('.template-storage-disk').val()),
                    'format': $(diskEntity).find('.template-storage-disk-format').val()
                };
            }

            // image based template: add base to dictionary
            if ((baseImageTemplate) && (index == 0)) {
                newDisk["base"] = $('#template-edit-vmimage-textbox').val();
            }

            var storageType = $(diskEntity).find('.template-storage-type').val();
            if (storageType === 'iscsi' || storageType === 'scsi') {
                newDisk['volume'] = newDisk['pool']['name'].split('/').pop();
                newDisk['pool']['name'] = newDisk['pool']['name'].slice(0, newDisk['pool']['name'].lastIndexOf('/'));
                delete newDisk.size;
            }
            disksForUpdate.push(newDisk);
        });
        data.disks = disksForUpdate;

        $.each(editableFields, function(i, field) {
            if (field == 'graphics') {
                var type = $('#form-template-general [name="' + field + '"]').val();
                data[field] = { 'type': type };
            } else {
                data[field] = $('#form-template-general [name="' + field + '"]').val();
            }
        });
        data['memory'] = Number(data['memory']);
        data['max-memory'] = Number(data['max-memory']);

        memory = { 'current': data['memory'], 'maxmemory': data['max-memory'] };

        data['memory'] = memory;
        delete data['max-memory'];

        var cpu = parseInt($('#vcpus').val());
        var maxCpu = parseInt($('#guest-edit-max-processor-textbox').val());
        var maxCpuFinal = cpu; //Initially set maxCpu to be the same as cpu
        if (maxCpu >= cpu) {
            maxCpuFinal = maxCpu;
        }

        if ($('.tab-content .has-changes > input[name="cdrom"]').length) {
            data['cdrom'] = $('.tab-content input[name="cdrom"]').val();
        }

        if ($('.tab-content .has-changes > input[name="vm-image"]').length) {
            data['vm-image'] = $('.tab-content input[name="vm-image"]').val();
        }

        if ($("input:checkbox", "#form-template-processor").prop("checked")) {
            //Check if maxCpu field has a value
            data['cpu_info'] = {
                vcpus: cpu,
                maxvcpus: maxCpuFinal,
                topology: {
                    sockets: 1,
                    cores: parseInt($("#cores").val()),
                    threads: parseInt($("#threads").val())
                }
            };
        } else {
            data['cpu_info'] = {
                vcpus: cpu,
                maxvcpus: maxCpuFinal,
                topology: {}
            };
        }

        if(kimchi.hostarch === s390xArch){
            var interfaces = $('.template-tab-body .item', '#form-template-interface-s390x');
            var networkForUpdate = new Array();
            var interfacceForUpdate = new Array();

            $.each(interfaces, function(index, interfaceEntities) {
                var fields =  $('span.type select', interfaceEntities);
                switch(fields.val()){
                    case 'network':
                        var thisValue = $('span.network select', interfaceEntities).val();
                        networkForUpdate.push(thisValue);
                    break;
                    case 'macvtap':
                        var thisdata = {};
                        thisdata.type = $('span.type select', interfaceEntities).val();
                        thisdata.name = $('span.network select', interfaceEntities).val();
                        thisdata.mode = $('span.mode select', interfaceEntities).val();
                        interfacceForUpdate.push(thisdata);
                    break;
                    case 'ovs':
                        var thisdata = {};
                        thisdata.type = $('span.type select', interfaceEntities).val();
                        thisdata.name = $('span.network select', interfaceEntities).val();
                        interfacceForUpdate.push(thisdata);
                    break;
                }

                if (networkForUpdate instanceof Array) {
                    data.networks = networkForUpdate;
                } else if (networkForUpdate != null) {
                    data.networks = [networkForUpdate];
                } else {
                    data.networks = [];
                }

                if (networkForUpdate instanceof Array) {
                    data.interfaces = interfacceForUpdate;
                } else if (interfacceForUpdate != null) {
                    data.interfaces = [interfacceForUpdate];
                } else {
                    data.interfaces = [];
                }
        });
        }else {
            var networks = $('.template-tab-body .item', '#form-template-interface');
            var networkForUpdate = new Array();
            $.each(networks, function(index, networkEntities) {
                var thisValue = $('select', networkEntities).val();
                networkForUpdate.push(thisValue);
            });

            if (networkForUpdate instanceof Array) {
                data.networks = networkForUpdate;
            } else if (networkForUpdate != null) {
                data.networks = [networkForUpdate];
            } else {
                data.networks = [];
            }
        }

        if ($('.has-error', '#form-template-storage').length) {
            // Workaround to check if invalid storage wasn't changed
            $('a[href="#storage"]', '#edit-template-tabs').tab('show');
            $('.modal .wok-mask').addClass('hidden');
            $button.html(i18n['KCHAPI6007M']);
            $button.prop('disabled', false);
            $('.modal input[type="text"]').prop('disabled', false);
            $('.modal input[type="checkbox"]').prop('disabled', false);
            $('.modal select').prop('disabled', false);
            $('.modal .selectpicker').removeClass('disabled');
            wok.message.error(i18n['KCHTMPL6007M'], '#alert-modal-container');
        } else {
            kimchi.updateTemplate($('#template-name').val(), data, function() {
                kimchi.doListTemplates();
                wok.window.close();
            }, function(err) {
            $('.modal .wok-mask').addClass('hidden');
                $button.html(i18n['KCHAPI6007M']);
                $button.prop('disabled', false);
                $('.modal input[type="text"]').prop('disabled', false);
                $('.modal input[type="checkbox"]').prop('disabled', false);
                $('.modal select').prop('disabled', false);
                $('.modal .selectpicker').removeClass('disabled');
                wok.message.error(err.responseJSON.reason, '#alert-modal-container');
            });
        }
    });
};
