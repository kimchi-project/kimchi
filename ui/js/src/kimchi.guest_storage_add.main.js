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
        label: i18n.KCHVMSTOR0001M,
        value: 'cdrom',
    },
    {
        label: i18n.KCHVMSTOR0002M,
        value: 'disk',
    }];
    var typesRunning = [{
        label: i18n.KCHVMSTOR0002M,
        value: 'disk'
    }];

    var source = [{
        label: i18n.KCHVMSTOR0003M,
        value: 'pool'
    },{
        label: i18n.KCHVMSTOR0004M,
        value: 'path'
    }];

    var storageAddForm = $('#form-guest-storage-add');
    var submitButton = $('#guest-storage-button-add');
    var typeTextbox = $('select#guest-storage-type', storageAddForm);
    var pathTextbox = $('input[name="path"]', storageAddForm);
    var poolTextbox = $('select#guest-disk-pool', storageAddForm);
    var sourceTextbox = $('select#guest-disk-source', storageAddForm);
    var sourcenewTextbox = $('select#guest-disk-source-new', storageAddForm);
    var directorypathTextbox = $('#directorypath', storageAddForm);
    var diskpathTextbox = $('#diskpath', storageAddForm);
    var volTextbox = $('select#guest-disk-vol', storageAddForm);
    var newPoolTextbox = $('select#guest-disk-pool-new', storageAddForm);
    var capacityTextbox = $('input[name="capacity"]', storageAddForm);
    var formatTextbox = $('select#guest-disk-format-new', storageAddForm);
    var selectStorageTypeHTML = '';
    var selectStoragePoolHTML = '';
    var selectStorageVolHTML  = '';
    var rbExisting = 'false';
    var s390xArch = 's390x';

    var getFormatList = function() {
        var format = [i18n['KCHVMSTOR0005M'], i18n['KCHVMSTOR0006M'], i18n['KCHVMSTOR0007M'], i18n['KCHVMSTOR0008M'], i18n['KCHVMSTOR0009M'], i18n['KCHVMSTOR0010M']];
        var selectFormatHTML = '';
        var i;
        for (i = 0; i < format.length; i++) {
            selectFormatHTML += '<option value="'+ format[i] + '">' + format[i] + '</option>';
        }
        formatTextbox.empty();
        formatTextbox.append(selectFormatHTML);
        formatTextbox.val("qcow2");
        $(formatTextbox).trigger('change');
        formatTextbox.selectpicker();
        $('.selectpicker').selectpicker('refresh');
    };

    typeTextbox.on('change',function() {
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
                $(newPoolTextbox).trigger('change');
                $(formatTextbox).val('qcow2');
                $(formatTextbox).trigger('change');
            } else if ($('#existing-disk').checked) {
                $('#new-disk-box').addClass('hidden');
                $(poolTextbox).val('default');
                $(poolTextbox).trigger('change');
            } else {
                //Goes here the first time since radiobuttons are undefined
                if (rbExisting === 'true') {
                    $('#new-disk-box').addClass('hidden');
                } else {
                    $('#existing-disk-box').addClass('hidden');
                    $(formatTextbox).val('qcow2');
                    $(formatTextbox).trigger('change');
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
                    $(poolTextbox).trigger('change');
	            poolTextbox.selectpicker();
                    $('.selectpicker').selectpicker('refresh');
                } else if (radioButton === 'new') { //new disk
                    newPoolTextbox.empty();
                    newPoolTextbox.append(selectStoragePoolHTML);
                    $(newPoolTextbox).val("ISO");
                    newPoolTextbox.selectpicker();
                    getFormatList();
                }
            }
        });
    };

    //First time retrieving list of Storage Pools - defaulting to new disk
    getStoragePools('new');

    if(kimchi.hostarch === s390xArch){
        //initialize source dropdown for new disk
        $('#new-disk-box div.source').show();

        var getStorageSourceNew = function(sourceSelected ) {
            selectStorageSourceHTML = ''; //reset string
            $.each(source, function(index, storageSource) {
                selectStorageSourceHTML += '<option value="'+ storageSource.value + '">' + storageSource.label + '</option>';
            });

            sourcenewTextbox.empty();
            sourcenewTextbox.append(selectStorageSourceHTML);
            sourcenewTextbox.val(sourceSelected);
            $(sourcenewTextbox).trigger('change');
            sourcenewTextbox.selectpicker();
            $('.selectpicker').selectpicker('refresh');
        };

        getStorageSourceNew('pool');

        //initialize source dropdown for existing disk
        $('#existing-disk-box div.source').show();

        var getStorageSource = function(sourceSelected ) {
            selectStorageSourceHTML = ''; //reset string
            $.each(source, function(index, storageSource) {
                selectStorageSourceHTML += '<option value="'+ storageSource.value + '">' + storageSource.label + '</option>';
            });

            sourceTextbox.empty();
            sourceTextbox.append(selectStorageSourceHTML);
            sourceTextbox.val(sourceSelected);
            $(sourceTextbox).trigger('change');
            sourceTextbox.selectpicker();
            $('.selectpicker').selectpicker('refresh');
        };
        getStorageSource('pool');
    }

    poolTextbox.on('change',function() {
        var options = [];
        selectStorageVolHTML = '';
        volTextbox.empty();
        kimchi.listStorageVolumes($(this).val(), function(result) {
            var validVolType = { cdrom: /iso/, disk: /^(raw|qcow|qcow2|qed|vmdk|vpc)$/};
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
                    $(volTextbox).trigger('change');
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

    if (kimchi.hostarch === s390xArch) {
        sourcenewTextbox.on('change', function() {
            switch ($(this).val()) {
                case 'path':
                    $('#new-disk-box div.pool').hide();
                    $('#new-disk-box div.directorypath').show();
                    $(directorypathTextbox).val("");

                    break;
                default:
                    $('#new-disk-box div.pool').show();
                    $('#new-disk-box div.directorypath').hide();
            }
            $(capacityTextbox).val("").trigger('change');
        });

        sourceTextbox.on('change', function() {
            switch ($(this).val()) {
                case 'path':
                    $('#existing-disk-box div.pool,div.volume').hide();
                    $('#existing-disk-box div.diskpath').show();
                    $(diskpathTextbox).val("").trigger('change');
                    $(submitButton).prop('disabled', true);

                    break;
                default:
                    $('#existing-disk-box div.pool,div.volume').show();
                    $('#existing-disk-box div.diskpath').hide();
                    $(submitButton).prop('disabled', false);
            }
        });
    }

    typeTextbox.on('change',function() {
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
    $('#existing-disk').on('change',function() {
        if (this.checked) {
            rbExisting = 'true';
            if (currentPage === 'new-disk-box') {
                kimchi.switchPage(currentPage, 'existing-disk-box', 'right');
            }
            currentPage = 'existing-disk-box';
            $('#existing-disk-box').removeClass('hidden');
            $('#new-disk-box').addClass('hidden');
            $('#guest-storage-add-window .modal-body .template-pager').animate({
                height: "300px"
            }, 300);
            getStoragePools('existing');
            if(kimchi.hostarch === s390xArch){
                getStorageSource('pool');
                $(diskpathTextbox).val("").trigger('change');
            }
            $(pathTextbox).val("");
            $(newPoolTextbox).val("");
            $(capacityTextbox).val("");
            $(formatTextbox).val("");
        }
    });

    $('#new-disk').on('change',function() {
        if (this.checked) {
            $(formatTextbox).val("qcow2");
            $(formatTextbox).trigger('change');
            rbExisting = 'false';
            if (currentPage === 'existing-disk-box') {
                kimchi.switchPage(currentPage, 'new-disk-box', 'right');
            } else if($(capacityTextbox).is(":visible") === false ) {
                 kimchi.switchPage(currentPage, 'new-disk-box', 'right');
            }
            currentPage = 'new-disk-box';
            $('#existing-disk-box').addClass('hidden');
            $('#new-disk-box').removeClass('hidden');

            if(kimchi.hostarch === s390xArch){
                getStorageSourceNew('pool');
                $('#guest-storage-add-window .modal-body .template-pager').animate({
                    height: "400px"
                }, 400);
                $(capacityTextbox).val("").trigger('change');
            }else{
                $('#guest-storage-add-window .modal-body .template-pager').animate({
                    height: "300px"
                }, 400);
            }
            $(pathTextbox).val("");
            $(poolTextbox).val("");
            $(volTextbox).val("");
        }
    });

    var selectType = $(typeTextbox).val();
    if (kimchi.thisVMState === 'running') {
        types = typesRunning;
    }
    for (var i = 0; i < types.length; i++) {
        selectStorageTypeHTML += '<option value="'+ types[i].value + '">' + types[i].label + '</option>';
    }
    typeTextbox.append(selectStorageTypeHTML);
    typeTextbox.find('option:first').attr('selected','selected');
    typeTextbox.selectpicker();
    if (kimchi.thisVMState === 'running') {
        $(typeTextbox).val('disk');
        typeTextbox.trigger('change');
        poolTextbox.trigger('change');
    }

    var validateCDROM = function(settings) {
        if (/^((https|http|ftp|ftps|tftp|file|\/).*)+$/.test(settings['path'])){
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
                        var errText = result['message'] ||
                        result['responseJSON']['reason'];
                        $(submitButton).text(i18n['KCHVMCD6002M']);
                        $(submitButton).prop('disabled', false);
                        $(capacityTextbox).prop('disabled', false);
                        $(formatTextbox).prop('disabled', false);
                        wok.message.error(errText, '#alert-modal-container2');
                    }
                });
            }
            setTimeout(monitorTask, 2000);
        }, onError);
    };

    var bNewDisk = 'false';

    var validateDisk = function(settings) {
        bNewDisk = 'false';
        // Determine whether it's existing disk or new disk
        if($(capacityTextbox).is(":visible") === true ) {
            bNewDisk = 'true';
        }
        if (kimchi.hostarch === s390xArch && ((sourceTextbox.val() === 'path' || sourcenewTextbox.val() === 'path'))) {
            if (bNewDisk === 'true') {
                if ((/^((https|http|ftp|ftps|tftp|\/).*)+$/.test(settings['dir_path'])) && settings['size'] && settings['format']){
                    return true;
                }else{
                    wok.message.error(i18n['KCHVMSTOR0003E'],'#alert-modal-container2');
                    return false;
                }
            }else{
                if (/^((https|http|ftp|ftps|tftp|\/).*)+$/.test(settings['path'])){
                    return true;
                }else{
                    wok.message.error(i18n['KCHVMSTOR0004E'],'#alert-modal-container2');
                    return false;
                }
            }
        }else{
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
                    wok.message.error(i18n['KCHVMSTOR0005E'],'#alert-modal-container2');
                    return false;
                }
            } else {
                if (settings['pool'] && settings['vol']){
                    // Delete path property since it's not needed for disk
                    delete settings['path'];
                    return true;
                } else {
                    wok.message.error(i18n['KCHVMSTOR0002E'],'#alert-modal-container2');
                    return false;
                }
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
        if (kimchi.hostarch === s390xArch && ((sourceTextbox.val() === 'path' || sourcenewTextbox.val() === 'path'))) {
            if ($('#new-disk').prop('checked')) {
                var settings = {
                    vm: kimchi.selectedGuest,
                    dir_path: directorypathTextbox.val(),
                    name: kimchi.selectedGuest + '_' + $.now() + '.img',
                    size: capacityTextbox.val(),
                    type: typeTextbox.val(),
                    format: formatTextbox.val()
                };
            } else if ($('#existing-disk').prop('checked')) {
                var settings = {
                    vm: kimchi.selectedGuest,
                    path: diskpathTextbox.val(),
                    type: typeTextbox.val(),
                    format: formatTextbox.val()
                };
            }
        } else {
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
        }

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

            if((bNewDisk === 'false' || ((kimchi.hostarch === s390xArch && ((sourceTextbox.val() === 'path' || sourcenewTextbox.val() === 'path')))))){
                addStorage(settings);
            }

        $(submitButton).addClass('loading').text(i18n['KCHVMCD6003M']);
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


    if(kimchi.hostarch === s390xArch){
        $(capacityTextbox).on('change input propertychange', function(event){
            if(sourcenewTextbox.val() === 'path'){
                $(submitButton).prop('disabled', $(capacityTextbox).val() === '' || $(directorypathTextbox).val() === '');
            }else{
                $(submitButton).prop('disabled', $(capacityTextbox).val() === '');
            }
        });

        $(directorypathTextbox).on('change input propertychange', function(event){
            if(sourcenewTextbox.val() === 'path'){
                $(submitButton).prop('disabled', $(capacityTextbox).val() === '' || $(directorypathTextbox).val() === '');
            }else{
                $(submitButton).prop('disabled', $(capacityTextbox).val() === '');
            }
        });

        diskpathTextbox.on('change input propertychange', function(event) {
            $(submitButton).prop('disabled', $(this).val() === '');
        });
    }else{
        capacityTextbox.on('change input propertychange', function(event) {
            $(submitButton).prop('disabled', $(this).val() === '');
        });
    }
};
