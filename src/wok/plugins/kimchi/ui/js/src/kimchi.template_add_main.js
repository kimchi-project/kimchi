/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2015
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
    direction = direction || 'left';
    var toLeftBegin;
    var fromLeftEnd;
    if('left' === direction) {
        toLeftBegin = '100%';
        fromLeftEnd = '-100%';
    } else if('right' === direction) {
        toLeftBegin = '-100%';
        fromLeftEnd = '100%';
    }
    var formPage = $('#'+fromPageId);
    var toPage = $('#'+toPageId);
    toPage.css({
        left: toLeftBegin
    });
    formPage.animate({
        left: fromLeftEnd,
        opacity: 0.1
    }, 400);
    toPage.animate({
        left: '0',
        opacity: 1
    }, 400);
};

kimchi.template_add_main = function() {
    "use strict";
    var currentPage = 'iso-local-box';
    kimchi.deepScanHandler = null;

    var deepScan = function(button) {
        kimchi.deepScanHandler = kimchi.stepListDeepScanIsos(function(isos, isFinished) {
            if (isos && isos.length) {
                if(button === '#iso-search') {
                    $(button + '-loading').hide();
                    button = '#iso-more';
                    $(button + '-loading').show();
                }
                showLocalIsoField(isos);
            } else {
                if (isFinished) {
                    wok.message.warn(i18n['KCHTMPL6001W']);
                }
            }
            if (isFinished) {
                $(button + '-loading').hide();
                $(button).show();
            }
        }, function(err) {
            wok.message.error(err.responseJSON.reason);
            $(button + '-loading').hide();
            $(button).show();
        });
    };

    //1-1-1 local iso list
    var initLocalIsoField = function() {
        kimchi.isoInfo = {};
        $('#local-iso-field').hide();
        $('#select-all-local-iso').prop('checked', false);
        $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        $('#iso-search').hide();
        $('#iso-more').hide();
        $('#iso-search-loading').hide();
        $('#iso-more-loading').hide();
        $('#list-local-iso').empty();

        // Resets input fields and hide other buttons
        $('#iso-file').val(''); // 1 - Folder path text
        $('vm-image-local-text').val(''); // 3 - File path text
        $('#iso-url').val(''); // 4 - Remote folder path text
        $('#btn-template-file-create').attr('disabled', 'disabled').css('display','inline-block'); // 1 - Folder path
        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs
        $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path
        $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path
        $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos
        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false); // False to all select-all checkboxes
        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false); // False to all list checkboxes

    };

    var showLocalIsoField = function(isos) {
        var html = '';
        var template = $('#tmpl-list-local-iso').html();
        $.each(isos, function(index, volume) {
            var isoId = volume.os_distro + '*' + volume.name + '*' + volume.os_version;
            if (!kimchi.isoInfo[isoId]) {
                volume.isoId = isoId;
                volume.capacity = wok.changetoProperUnit(volume.capacity, 1);
                kimchi.isoInfo[isoId] = volume;
                html += wok.substitute(template, volume);
            }
        });
        $('#list-local-iso').append(html);
        $('#local-iso-field').show();
    };


    //1-1-2 local iso file
    var initIsoFileField = function() {
        //$('#iso-file-check').prop('checked', false);
        $('#iso-file').val('');
        $('vm-image-local-text').val('');
        $('#iso-url').val(''); 
        $('#btn-template-file-create').attr('disabled', 'disabled').css('display','inline-block');

        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs

        $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

        $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path

        $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos

        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false); // False to all select-all checkboxes

        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false); // False to all list checkboxes

    };

    $('#iso-file').on('input propertychange', function() {
        if ($('#iso-file').val()) {

        $('#btn-template-file-create').removeAttr('disabled').css('display','inline-block'); // 1 - Folder path

        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs

        $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

        $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path

        $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos

        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false); // False to all select-all checkboxes

        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false); // False to all list checkboxes

        } else {
            $('#btn-template-file-create').attr('disabled', 'disabled');
        }
    });

    initLocalIsoField();
    initIsoFileField();
    kimchi.listIsos(function(isos) {
        if (isos && isos.length) {
            showLocalIsoField(isos);
            $('#iso-more').show();
        } else {
            $('#iso-search').show();
        }
    }, function(err) {
        wok.message.error(err.responseJSON.reason);
    });
    $('#template-add-window .modal-body .template-pager').animate({
    height: "689px"
  },400);

    // 1-1 local iso
    $('#iso-local').change(function() {
        if(this.checked){
            if(currentPage === 'vm-image-local-box') {
                kimchi.switchPage(currentPage, 'iso-local-box','right'); 
            } else if(currentPage === 'iso-remote-box') {
                kimchi.switchPage(currentPage, 'iso-local-box','right'); 
            }
            currentPage = 'iso-local-box';
                $('#template-add-window .modal-body .template-pager').animate({
                height: "689px"
              },400);            
            initLocalIsoField();
            initIsoFileField();

            $('#btn-template-file-create').attr('disabled', 'disabled').css('display','inline-block'); // 1 - Folder path

            $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs

            $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

            $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path

            $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos
    

            kimchi.listIsos(function(isos) {
                if (isos && isos.length) {
                    showLocalIsoField(isos);
                    $('#iso-more').show();
                } else {
                    $('#iso-search').show();
                }
            }, function(err) {
                wok.message.error(err.responseJSON.reason);
            });
        }
    });

    $('#iso-search').click(function() {
        var settings = {
            content : i18n['KCHTMPL6002M']
        };
        wok.confirm(settings, function() {
            $('#iso-search').hide();
            $('#iso-search-loading').show();
            deepScan('#iso-search');
        });
    });

    $('#iso-more').click(function() {
        var settings = {
            content : i18n['KCHTMPL6002M']
        };
        wok.confirm(settings, function() {
            $('#iso-more').hide();
            $('#iso-more-loading').show();
            deepScan('#iso-more');
        });
    });

    $('#iso-search-loading').click(function() {
        $('#iso-search-loading').hide();
        $('#iso-search').show();
        if (kimchi.deepScanHandler) {
            kimchi.deepScanHandler.stop = true;
        }
    });

    $('#iso-more-loading').click(function() {
        $('#iso-more-loading').hide();
        $('#iso-more').show();
        if (kimchi.deepScanHandler) {
            kimchi.deepScanHandler.stop = true;
        }
    });

    $('#select-all-local-iso').click(function() {
        $('#list-local-iso [type="checkbox"]').prop('checked', $(this).prop('checked'));
        if ($(this).prop('checked')) {
            $('#iso-file').val('');
            $('vm-image-local-text').val('');

            $('#btn-template-file-create').attr('disabled', 'disabled').css('display','none'); // 1 - Folder path

            $('#btn-template-local-iso-create').removeAttr('disabled').css('display','inline-block'); // 2 - Selected ISOs

            $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

            $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path

            $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos

        } else {
            $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        }
    });

    $('#list-local-iso').on('click', '[type="checkbox"]', function() {
        var checkedLength = $('#list-local-iso [type="checkbox"]:checked').length;
        $('#iso-file').val('');
        $('vm-image-local-text').val('');
        $('#iso-url').val('');

        $('#btn-template-file-create').attr('disabled', 'disabled').css('display','none'); // 1 - Folder path

        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','inline-block'); // 2 - Selected ISOs

        $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

        $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path

        $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos
        if (checkedLength) {
            $('#btn-template-local-iso-create').removeAttr('disabled');
            var length = $('#list-local-iso [type="checkbox"]').length;
            $('#select-all-local-iso').prop('checked', length == checkedLength);
            $('#btn-template-local-iso-create').removeAttr('disabled');
        } else {
            $('#select-all-local-iso').prop('checked', false);
            $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        }
    });

    $('#btn-template-local-iso-create').click(function() {
        submitIso('form-local-iso');
    });

    $('#btn-template-file-create').click(function() {
        var isoFile = $('#iso-file').val();
        $('vm-image-local-text').val('');
        if (!kimchi.template_check_path(isoFile)) {
            wok.message.error.code('KCHAPI6003E');
            return;
        }
        var data = {
            "cdrom" : isoFile
        };
        addTemplate(data);
    });

    //1-2 remote iso
    $('#iso-remote').attr("disabled", true).css('cursor', 'not-allowed');

    var enabledRemoteIso = function() {
        if (kimchi.capabilities == undefined) {
            setTimeout(enabledRemoteIso, 2000);
            return;
        }

        if (kimchi.capabilities.qemu_stream != true) {
            return;
        }

        $('#iso-remote').attr("disabled", false).css('cursor', 'pointer');
        $('#iso-remote').change(function() {
            if (this.checked) {
                if(currentPage === 'iso-local-box') { // slide twice
                    kimchi.switchPage(currentPage, 'iso-remote-box','left'); 
                } else if(currentPage === 'vm-image-local-box') { // slide once
                    kimchi.switchPage(currentPage, 'iso-remote-box','left'); 
                }
                currentPage = 'iso-remote-box';
                $('#template-add-window .modal-body .template-pager').animate({
                    height: "635px"
                },400);
                initRemoteIsoField();
                initIsoUrlField();
                kimchi.listDistros(function(isos) {
                    showRemoteIsoField(isos);
                }, function() {
                });
            }
        });
    };
    enabledRemoteIso();

    //1-2-1 remote iso list
    var initRemoteIsoField = function() {
        $('#load-remote-iso').show();
        $('#remote-iso-field').hide();
        $('#iso-url-field').hide();
        $('#select-all-remote-iso').prop('checked', false);
        $('#btn-template-remote-iso-create').attr('disabled', 'disabled');

        $('#iso-file').val('');
        $('vm-image-local-text').val('');
        $('#iso-url').val('');

        $('#btn-template-file-create').attr('disabled', 'disabled').css('display','none'); // 1 - Folder path

        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs

        $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

        $('#btn-template-url-create').attr('disabled', 'disabled').css('display','inline-block'); // 4 - Remote folder path

        $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos

        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false); // False to all select-all checkboxes

        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false); // False to all list checkboxes

    };

    var showRemoteIsoField = function(isos) {
        if (isos && isos.length) {
            kimchi.isoInfo = {};
            var html = '';
            var template = $('#tmpl-list-remote-iso').html();
            $.each(isos, function(index, volume) {
                var isoId = volume.os_distro + '*' + volume.name + '*' + volume.os_version;
                if (!kimchi.isoInfo[isoId]) {
                    volume.isoId = isoId;
                    kimchi.isoInfo[isoId] = volume;
                    html += wok.substitute(template, volume);
                }
            });
            $('#list-remote-iso').html(html);
            $('#load-remote-iso').hide()
            $('#remote-iso-field').show();
            $('#iso-url-field').show();
        } else {
            $('#load-remote-iso').hide()
            $('#iso-url-field').show();
            wok.message.warn(i18n['KCHTMPL6001W']);
        }
    };

    $('#select-all-remote-iso').click(function() {
        $('#list-remote-iso [type="checkbox"]').prop('checked', $(this).prop('checked'));
        if ($(this).prop('checked')) {

            $('#iso-file').val('');
            $('vm-image-local-text').val('');
            $('#iso-url').val(''); 

            $('#btn-template-file-create').attr('disabled', 'disabled').css('display','none'); // 1 - Folder path

            $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs

            $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

            $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path

            $('#btn-template-remote-iso-create').removeAttr('disabled').css('display','inline-block');  // 5 - Remote selected isos

        } else {
            $('#btn-template-remote-iso-create').attr('disabled', 'disabled');
        }
    });

    $('#list-remote-iso').on('click', '[type="checkbox"]', function() {
        var checkedLength = $('#list-remote-iso [type="checkbox"]:checked').length;
        if (checkedLength) {
            $('#btn-template-remote-iso-create').removeAttr('disabled');
            var length = $('#list-remote-iso [type="checkbox"]').length;
            $('#select-all-remote-iso').prop('checked', length == checkedLength);

            $('#iso-file').val('');
            $('vm-image-local-text').val('');
            $('#iso-url').val('');

            $('#btn-template-file-create').attr('disabled', 'disabled').css('display','none'); // 1 - Folder path

            $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs

            $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

            $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path

            $('#btn-template-remote-iso-create').removeAttr('disabled').css('display','inline-block');  // 5 - Remote selected isos

        } else {
            $('#select-all-remote-iso').prop('checked', false);
            $('#btn-template-remote-iso-create').attr('disabled', 'disabled');
        }
    });

    $('#btn-template-remote-iso-create').click(function() {
        submitIso('form-remote-iso');
    });

    //1-2-2 remote iso url
    var initIsoUrlField = function() {

        $('#iso-file').val('');
        $('vm-image-local-text').val('');
        $('#iso-url').val('');

        $('#btn-template-file-create').attr('disabled', 'disabled').css('display','none'); // 1 - Folder path

        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs

        $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','none'); // 3 - File path

        $('#btn-template-url-create').attr('disabled','disabled').css('display','inline-block'); // 4 - Remote folder path

        $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos

    }

    $('#iso-url').on('input propertychange', function() {
        if ($('#iso-url').val()) {
            $('#btn-template-url-create').removeAttr('disabled');
        } else {
            $('#btn-template-url-create').attr('disabled', 'disabled');
        }
    });

    $('#vm-image-local').change(function(){
        if(this.checked) {
            if(currentPage === 'iso-local-box') {
                kimchi.switchPage(currentPage, 'vm-image-local-box','left'); 
            } else if(currentPage === 'iso-remote-box') {
                kimchi.switchPage(currentPage, 'vm-image-local-box','right'); 
            }
            currentPage = 'vm-image-local-box';
            $('#template-add-window .modal-body .template-pager').animate({
                height: "100px"
              },400);

            $('#btn-template-file-create').attr('disabled', 'disabled').css('display','none'); // 1 - Folder path
            $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display','none'); // 2 - Selected ISOs
            $('#vm-image-local-box-button').attr('disabled', 'disabled').css('display','inline-block'); // 3 - File path
            $('#btn-template-url-create').attr('disabled', 'disabled').css('display','none'); // 4 - Remote folder path
            $('#btn-template-remote-iso-create').attr('disabled', 'disabled').css('display','none');  // 5 - Remote selected isos

        }
    });
    $('input', '#vm-image-local-box').on('keyup cut paste', function(){
        setTimeout(function(){
            var isValid = kimchi.template_check_path($('input', '#vm-image-local-box').val());
            $('input', '#vm-image-local-box').toggleClass('invalid-field', !isValid);
            $('#vm-image-local-box-button').attr('disabled', (isValid ? "false" : "true"));
        }, 0);
    });
    $('button', $('#vm-image-local-box')).button({
        disabled: true
    }).click(function(){
        $('input', '#vm-image-local-box').prop('disabled', true);
        $(this).button('option', {
            label: i18n['KCHAPI6008M'],
            disabled: true
        });
        addTemplate({disks:[{base:$('input', '#vm-image-local-box').val()}]}, function(){
            $('input', '#vm-image-local-box').prop('disabled', false);
            $('button', $('.body', '#vm-image-local-box')).button('option', {
                label: i18n['KCHAPI6005M'],
                disabled: false
            });
        });
    });

    $('#btn-template-url-create').click(function() {
        var isoUrl = $('#iso-url').val();
        if (!kimchi.template_check_url(isoUrl)) {
            wok.message.error.code('KCHAPI6004E');
            return;
        }
        var data = {
            "cdrom" : isoUrl
        };
        addTemplate(data);
    });

    //do create
    var addTemplate = function(data, callback) {
        kimchi.createTemplate(data, function() {
            if(callback) callback();
            kimchi.doListTemplates();
            wok.window.close();
            wok.topic('templateCreated').publish();
        }, function(err) {
            if(callback) callback();
            wok.message.error(err.responseJSON.reason);
        });
    };

    var submitIso = function(formId) {
        var formData = $('#' + formId).serializeObject();
        if (formData.iso) {
            var length = 0;
            var successNum = 0;
            var addTemplate = function(isoInfo) {
                var data = {
                    "os_distro" : isoInfo.os_distro,
                    "os_version" : isoInfo.os_version,
                    "cdrom" : isoInfo.path
                };
                kimchi.createTemplate(data, function() {
                    successNum++;
                    $('input[value="' + isoInfo.isoId + '"]').prop('checked', false);
                    $('.check-all>input').prop('checked', false);
                    kimchi.doListTemplates();
                    wok.topic('templateCreated').publish(data);
                    if (successNum === length) {
                        wok.window.close();
                    }
                }, function(err) {
                    wok.message.error(err.responseJSON.reason);
                });
            };
            if (formData.iso instanceof Array) {
                length = formData.iso.length;
                $.each(formData.iso, function(index, value) {
                    addTemplate(kimchi.isoInfo[value]);
                });
            } else {
                length = 1;
                addTemplate(kimchi.isoInfo[formData.iso]);
            }
        }
    };
};

kimchi.template_check_url = function(url) {
    var reg = /(https|http|ftp|ftps|tftp):\/\//;
    if (url.constructor === String) {
        return reg.test(url);
    }
    return false;
};

kimchi.template_check_path = function(filePath) {
    var reg = /((\/([0-9a-zA-Z-_ \.]+))+)$/;
    if (filePath.constructor === String) {
        return reg.test(filePath);
    }
    return false;
};