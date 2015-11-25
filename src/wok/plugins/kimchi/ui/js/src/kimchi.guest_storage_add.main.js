/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014-2015
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
    var selectStorageTypeHTML = '';
    var selectStoragePoolHTML = '';
    var selectStorageVolHTML  = '';

    typeTextbox.change(function() {
        var pathObject = {'cdrom': ".path-section", 'disk': '.volume-section'}
        selectType = $(this).val();
        $.each(pathObject, function(type, value) {
            if(selectType == type){
                $(value).removeClass('hidden');
            } else {
                $(value).addClass('hidden');
            }
        });

        if ($(".path-section").hasClass('hidden')) {
            $(poolTextbox).val('default');
            $(poolTextbox).change();
            $(pathTextbox).val("");
        }
        else {
            $(poolTextbox).val("");
            $(volTextbox).val("");
        }
        $('.selectpicker').selectpicker('refresh');
    });

    kimchi.listStoragePools(function(result) {
        var options = [];
        if (result && result.length) {
            $.each(result, function(index, storagePool) {
                if ((storagePool.state=="active") && (storagePool.type !== 'kimchi-iso')) {
                    options.push({
                        label: storagePool.name,
                        value: storagePool.name
                        });
                    selectStoragePoolHTML += '<option value="'+ storagePool.name + '">' + storagePool.name + '</option>';
                    }

                });
            poolTextbox.append(selectStoragePoolHTML);
            poolTextbox.val(options[0].value);
            poolTextbox.selectpicker();
        }
    });

    poolTextbox.change(function() {
        var options = [];
        selectStorageVolHTML = '';
        volTextbox.empty();
        kimchi.listStorageVolumes($(this).val(), function(result) {
            var validVolType = { cdrom: /iso/, disk: /^(raw|qcow|qcow2|bochs|qed|vmdk)$/};
            if (result.length) {
                $.each(result, function(index, value) {
                    // Only unused volume can be attached
                    if (value.used_by.length == 0 && value.isvalid && (value.type != 'file' || validVolType[selectType].test(value.format))) {
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
                volTextbox.selectpicker();
                $('.selectpicker').selectpicker('refresh');
            } 
        }, null, false);
    });


    typeTextbox.change(function() {
        var pathObject = {'cdrom': ".path-section", 'disk': '.volume-section'}
        var selectType = $(this).val();
        $.each(pathObject, function(type, value) {
            if(selectType == type){
                $(value).removeClass('hidden');
            } else {
                $(value).addClass('hidden');
            }
        });
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
        if (/^((https|http|ftp|ftps|tftp|\/).*)+$/.test(settings['path']))
            return true;
        else {
            wok.message.error.code('KCHVMSTOR0001E');
            return false;
        }
    }

    var validateDisk = function(settings) {
        if (settings['pool'] && settings['vol'])
            return true;
        else {
            wok.message.error.code('KCHVMSTOR0002E');
            return false;
        }
    }

    validator = {cdrom: validateCDROM, disk: validateDisk};
    var submitForm = function(event) {
        if (submitButton.prop('disabled')) {
            return false;
        }

        var formData = storageAddForm.serializeObject();
        var settings = {
            vm: kimchi.selectedGuest,
            type: typeTextbox.val(),
        };

        $(submitButton).prop('disabled', true);
        $.each([pathTextbox, poolTextbox, volTextbox], function(i, c) {
            $(c).prop('disabled', true);
            val = $(c).val()
            if (val && val != '') {
                settings[$(c).attr('name')] = $(c).val();
            }
        });
        // Validate form for cdrom and disk
        validateSpecifiedForm = validator[settings['type']];
        if (!validateSpecifiedForm(settings)) {
            $(submitButton).prop('disabled', false);
            $.each([submitButton, pathTextbox, poolTextbox, volTextbox], function(i, c) {
                $(c).prop('disabled', false);
            });
            return false;
        }
        $(submitButton).addClass('loading').text(i18n['KCHVMCD6003M']);

        kimchi.addVMStorage(settings, function(result) {
            wok.window.close();
            wok.topic('kimchi/vmCDROMAttached').publish({
                result: result
            });
        }, function(result) {
            var errText = result['reason'] ||
                result['responseJSON']['reason'];
            wok.message.error(errText);

            $.each([submitButton, pathTextbox, poolTextbox, volTextbox], function(i, c) {
                $(c).prop('disabled', false);
            });
            $(submitButton).removeClass('loading').text(i18n['KCHVMCD6002M']);
        });

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

};
