/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2014-2016
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
kimchi.switchPage = function(fromPageId, toPageId, direction) {
    $('.tab-content').css('overflow', 'hidden');
    direction = direction || 'left';
    var toLeftBegin;
    var fromLeftEnd;
    if ('left' === direction) {
        toLeftBegin = '100%';
        fromLeftEnd = '-100%';
    } else if ('right' === direction) {
        toLeftBegin = '-100%';
        fromLeftEnd = '100%';
    }
    var formPage = $('#' + fromPageId);
    var toPage = $('#' + toPageId);
    toPage.css({
        left: toLeftBegin
    });
    formPage.animate({
        left: fromLeftEnd,
        opacity: 0.1
    }, 400, function() {
        $('.tab-content').css('overflow', 'visible');
    });
    toPage.animate({
        left: '0',
        opacity: 1
    }, 400, function() {
        $('.tab-content').css('overflow', 'visible');
    });
};

kimchi.guest_storage_add_main = function() {
    var types = [{
        label: 'cdrom',
        value: 'cdrom',
    },
    {
        label: 'disk',
        value: 'disk',
    }];
    var typesRunning = [{
        label: 'disk',
        value: 'disk'
    }];

    var storageAddForm = $('#form-guest-storage-add');
    var submitButton = $('#guest-storage-button-add');
    var typeTextbox = $('select#guest-storage-type', storageAddForm);
    var pathTextbox = $('input[name="path"]', storageAddForm);
    var poolTextbox = $('select#guest-disk-pool', storageAddForm);
    var volTextbox = $('select#guest-disk-vol', storageAddForm);
    var newPoolTextbox = $('select#guest-disk-pool-new', storageAddForm);
    var capacityTextbox = $('input[name="capacity"]', storageAddForm);
    var formatTextbox = $('select#guest-disk-format-new', storageAddForm);
    var selectStorageTypeHTML = '';
    var selectStoragePoolHTML = '';
    var selectStorageVolHTML  = '';
    var rbExisting = 'false';

    var getFormatList = function() {
        var format = ["bochs", "cloop", "cow", "dmg", "qcow", "qcow2", "qed", "raw", "vmdk", "vpc"];
        var selectFormatHTML = '';
        var i;
        for (i = 0; i < format.length; i++) {
            selectFormatHTML += '<option value="'+ format[i] + '">' + format[i] + '</option>';
        }
        formatTextbox.empty();
        formatTextbox.append(selectFormatHTML);
        $(formatTextbox).change();
        formatTextbox.selectpicker();
        $('.selectpicker').selectpicker('refresh');
    };

    typeTextbox.change(function() {
        var pathObject = {'cdrom': ".path-section", 'disk': '.volume-section'};
        selectType = $(this).val();
        $.each(pathObject, function(type, value) {
            if(selectType === type){
                $(value).removeClass('hidden');
            } else if ((selectType === null) && (type === 'disk')) {
                $(value).removeClass('hidden');
            } else {
                $(value).addClass('hidden');
            }
        });
        if ($(".path-section").hasClass('hidden')) {
            $(pathTextbox).val("");
            if ($('#new-disk').checked) {
                $('#existing-disk-box').addClass('hidden');
                $(newPoolTextbox).val('default');
                $(newPoolTextbox).change();
                $(formatTextbox).val('qcow2');
                $(formatTextbox).change();
            } else if ($('#existing-disk').checked) {
                $('#new-disk-box').addClass('hidden');
                $(poolTextbox).val('default');
                $(poolTextbox).change();
            } else {
                //Goes here the first time since radiobuttons are undefined
                if (rbExisting === 'true') {
                    $('#new-disk-box').addClass('hidden');
                } else {
                    $('#existing-disk-box').addClass('hidden');
                    $(formatTextbox).val('qcow2');
                    $(formatTextbox).change();
                }
            }
        } else {
            $(poolTextbox).val("");
            $(volTextbox).val("");
            $(newPoolTextbox).val("");
            $(capacityTextbox).val("");
            $(formatTextbox).val("");
        }
        $('.selectpicker').selectpicker('refresh');
    });

    var getStoragePools = function(radioButton) {
        kimchi.listStoragePools(function(result) {
            var options = [];
            selectStoragePoolHTML = ''; //reset string
            if (result && result.length) {
                $.each(result, function(index, storagePool) {
                    if (radioButton === 'existing') {
                        if ((storagePool.state==="active") && (storagePool.type !== 'kimchi-iso')) {
                            options.push({
                                label: storagePool.name,
                                value: storagePool.name
                                });
                            selectStoragePoolHTML += '<option value="'+ storagePool.name + '">' + storagePool.name + '</option>';
                        }
                    } else { //new disk
                        if ((storagePool.type !== 'iscsi') && (storagePool.type !== 'scsi') && (storagePool.type !== 'kimchi-iso')) {
                            options.push({
                                label: storagePool.name,
                                value: storagePool.name
                                });
                            selectStoragePoolHTML += '<option value="'+ storagePool.name + '">' + storagePool.name + '</option>';
                        }
                    }
                });
                if (radioButton === 'existing') {
                    poolTextbox.empty();
                    poolTextbox.append(selectStoragePoolHTML);
                    $(poolTextbox).change();
	            poolTextbox.selectpicker();
                    $('.selectpicker').selectpicker('refresh');
                } else if (radioButton === 'new') { //new disk
                    newPoolTextbox.empty();
                    newPoolTextbox.append(selectStoragePoolHTML);
                    $(newPoolTextbox).val("qcow2");
                    newPoolTextbox.selectpicker();
                    getFormatList();
                }
            }
        });
    };

    //First time retrieving list of Storage Pools - defaulting to new disk
    getStoragePools('new');

    poolTextbox.change(function() {
        var options = [];
        selectStorageVolHTML = '';
        volTextbox.empty();
        kimchi.listStorageVolumes($(this).val(), function(result) {
            var validVolType = { cdrom: /iso/, disk: /^(raw|qcow|qcow2|bochs|qed|vmdk)$/};
            if (result.length) {
                $.each(result, function(index, value) {
                    // Only unused volume can be attached
                    if (value.used_by.length === 0 && value.isvalid && (value.type !== 'file' || validVolType[selectType].test(value.format))) {
                        options.push({
                            label: value.name,
                            value: value.name
                        });
                    }
                });
                if (options.length) {
                    for (var i = 0; i < options.length; i++) {
                        selectStorageVolHTML += '<option value="'+ options[i].value + '">' + options[i].label + '</option>';
                    }
                    volTextbox.append(selectStorageVolHTML);
                    $(volTextbox).val(options[0].value);
                    $(volTextbox).change();
                    $(volTextbox).prop('disabled',false);
                }else {
                    $(volTextbox).prop('disabled',true);
                    $(submitButton).prop('disabled', true);
                }
            } else {
                $(volTextbox).prop('disabled',true);
                $(submitButton).prop('disabled', true);
            }
            volTextbox.selectpicker();
            $('.selectpicker').selectpicker('refresh');
        }, null, false);
    });

    typeTextbox.change(function() {
        var pathObject = {'cdrom': ".path-section", 'disk': '.volume-section'};
        var selectType = $(this).val();
        $.each(pathObject, function(type, value) {
            if(selectType === type){
                $(value).removeClass('hidden');
            } else {
                $(value).addClass('hidden');
            }
        });
    });

    var currentPage = 'new-disk-box';
    $('#existing-disk').change(function() {
        if (this.checked) {
            rbExisting = 'true';
            if (currentPage === 'new-disk-box') {
                kimchi.switchPage(currentPage, 'existing-disk-box', 'right');
            }
            currentPage = 'existing-disk-box';
            $('#existing-disk-box').removeClass('hidden');
            $('#new-disk-box').addClass('hidden');
            $('#guest-storage-add-window .modal-body .template-pager').animate({
                height: "200px"
            }, 300);
            getStoragePools('existing');
            $(pathTextbox).val("");
            $(newPoolTextbox).val("");
            $(capacityTextbox).val("");
            $(formatTextbox).val("");
        }
    });

    $('#new-disk').change(function() {
        if (this.checked) {
            $(formatTextbox).val("qcow2");
            $(formatTextbox).change();
            rbExisting = 'false';
            if (currentPage === 'existing-disk-box') {
                kimchi.switchPage(currentPage, 'new-disk-box', 'right');
            } else if($(capacityTextbox).is(":visible") === false ) {
                 kimchi.switchPage(currentPage, 'new-disk-box', 'right');
            }
            currentPage = 'new-disk-box';
            $('#existing-disk-box').addClass('hidden');
            $('#new-disk-box').removeClass('hidden');
            $('#guest-storage-add-window .modal-body .template-pager').animate({
                height: "300px"
            }, 400);
            $(pathTextbox).val("");
            $(poolTextbox).val("");
            $(volTextbox).val("");
        }
    });

    if (kimchi.thisVMState === 'running') {
        types =typesRunning;
        $(typeTextbox).val('disk');
        typeTextbox.change();
        poolTextbox.change();
    }
    var selectType = $(typeTextbox).val();
    for (var i = 0; i < types.length; i++) {
        selectStorageTypeHTML += '<option value="'+ types[i].value + '">' + types[i].label + '</option>';
    }
    typeTextbox.append(selectStorageTypeHTML);
    typeTextbox.find('option:first').attr('selected','selected');
    typeTextbox.selectpicker();

    var validateCDROM = function(settings) {
        if (/^((https|http|ftp|ftps|tftp|\/).*)+$/.test(settings['path'])){
            // Delete pool and vol properties since they are not needed for cdrom
            delete settings['pool'];
            delete settings['vol'];
            return true;
        }
        else {
            wok.message.error(i18n['KCHVMSTOR0001E'],'#alert-modal-container2');
            return false;
        }
    };

    var onError = function(result) {
        if(!result) {
            return;
        }
        var msg = result['message'] || (
            result['responseJSON'] && result['responseJSON']['reason']
        );
        wok.message.error(msg);
    };

    var addStorage = function(settings) {
        kimchi.addVMStorage(settings, function(result) {
            wok.window.close();
            wok.topic('kimchi/vmCDROMAttached').publish({
            result: result
            });
        }, function(result) {
            var errText = result['reason'] ||
            result['responseJSON']['reason'];
            wok.message.error(errText, '#alert-modal-container2');
            $.each([submitButton, pathTextbox, poolTextbox, volTextbox, newPoolTextbox, capacityTextbox, formatTextbox], function(i, c) {
                $(c).prop('disabled', false);
            });
        });
    }

    var createVol = function(settings, addVolSettings) {
        kimchi.createVolumeWithCapacity(settings['pool'], {
            name: settings['vol'],
            format: settings['format'],
            capacity: settings['capacity']
        }, function(result) {
            var taskId = result.id;
            function monitorTask() {
                kimchi.getTask(taskId, function(result) {
                    var status = result.status;
                    if (status === "finished") {
                        //Now add newly created volume to VM
                        addStorage(addVolSettings);
                    } else if (status === "running") {
                        setTimeout(monitorTask, 2000);
                        $(submitButton).prop('disabled', true);
                    } else if (status === "failed") {
                        var errText = result['reason'] ||
                        result['responseJSON']['reason'];
                        $(submitButton).prop('disabled', true);
                        wok.message.error(errText, '#alert-modal-container2');
                    }
                });
            }
            setTimeout(monitorTask, 2000);
        }, onError);
    };

    var bNewDisk = 'false';

    var validateDisk = function(settings) {
        // Determine whether it's existing disk or new disk
        if($(capacityTextbox).is(":visible") === true ) {
            bNewDisk = 'true';
        }
        if (bNewDisk === 'true') {
            if (settings['newpool'] && settings['capacity'] && settings['format']){
                //Change settings['newpool'] to settings['pool']
                settings['pool']=settings['newpool'];
                var vmname = settings['vm'];
                vmname = vmname + new Date().getTime();
                //Unique vol name to be created
                settings['vol']=vmname + ".img";
                //This is all that is needed for attaching newly created volume to VM
                var addVolSettings = {
                    vm: settings['vm'],
                    type: settings['type'],
                    vol:  settings['vol'],
                    pool: settings['pool']
                };
                var sizeInMB = parseInt(settings['capacity']) * 1024;
                settings['capacity'] = sizeInMB;
                //These need to be deleted so they don't get passed to backend
                delete settings['path'];
                delete settings['newpool'];
                //Create an empty storage volume and attach to VM if successful
                createVol(settings, addVolSettings);
                return true;
            } else {
                wok.message.error(i18n['KCHVMSTOR0002E'],'#alert-modal-container2');
                return false;
            }
        } else {
            if (settings['pool'] && settings['vol']){
                // Delete path property since it's not needed for disk
                delete settings['path'];
                return true;
            }
            else {
                wok.message.error(i18n['KCHVMSTOR0002E'],'#alert-modal-container2');
                return false;
            }
        }
    };

    validator = {cdrom: validateCDROM, disk: validateDisk};
    var submitForm = function(event) {
        if (submitButton.prop('disabled')) {
            return false;
        }
        var bNewDisk = 'false';
        // Determine whether it's existing disk or new disk
        if($(capacityTextbox).is(":visible") === true ) {
            bNewDisk = 'true';
        }

        var formData = storageAddForm.serializeObject();
        var settings = {
            vm: kimchi.selectedGuest,
            type: typeTextbox.val(),
            path: pathTextbox.val(),
            pool: poolTextbox.val(),
            vol: volTextbox.val(),
            newpool: newPoolTextbox.val(),
            format: formatTextbox.val(),
            capacity: capacityTextbox.val()
        };

        $(submitButton).prop('disabled', true);
        $.each([pathTextbox, poolTextbox, volTextbox, newPoolTextbox, capacityTextbox, formatTextbox], function(i, c) {
            $(c).prop('disabled', true);
        });
        // Validate form for cdrom and disk
        validateSpecifiedForm = validator[settings['type']];
        if (!validateSpecifiedForm(settings)) {
            $(submitButton).prop('disabled', false);
            $.each([submitButton, pathTextbox, poolTextbox, volTextbox, newPoolTextbox, capacityTextbox, formatTextbox], function(i, c) {
                $(c).prop('disabled', false);
            });
            return false;
        }
        $(submitButton).addClass('loading').text(i18n['KCHVMCD6003M']);

        if(bNewDisk === 'false'){
            addStorage(settings);
        }
        event.preventDefault();
    };

    storageAddForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
    pathTextbox.on('change input propertychange', function(event) {
        $(submitButton).prop('disabled', $(this).val() === '');
    });
    volTextbox.on('change propertychange', function (event) {
        $(submitButton).prop('disabled', $(this).val() === '');
    });
    capacityTextbox.on('change input propertychange', function(event) {
        $(submitButton).prop('disabled', $(this).val() === '');
    });

};
