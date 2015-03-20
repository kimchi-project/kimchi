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
    kimchi.deepScanHandler = null;
    // 1-1 local iso
    $('#iso-local').click(function() {
        kimchi.switchPage('iso-type-box', 'iso-local-box');
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
            kimchi.message.error(err.responseJSON.reason);
        });
    });

    $('#iso-local-box-back').click(function() {
        if (kimchi.deepScanHandler) {
            kimchi.deepScanHandler.stop = true;
        }
        kimchi.switchPage('iso-local-box', 'iso-type-box', 'right');
    });

    $('#iso-search').click(function() {
        var settings = {
            content : i18n['KCHTMPL6002M']
        };
        kimchi.confirm(settings, function() {
            $('#iso-search').hide();
            $('#iso-search-loading').show();
            deepScan('#iso-search');
        });
    });

    $('#iso-more').click(function() {
        var settings = {
            content : i18n['KCHTMPL6002M']
        };
        kimchi.confirm(settings, function() {
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
                    kimchi.message.warn(i18n['KCHTMPL6001W']);
                }
            }
            if (isFinished) {
                $(button + '-loading').hide();
                $(button).show();
            }
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
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
    };

    var showLocalIsoField = function(isos) {
        var html = '';
        var template = $('#tmpl-list-local-iso').html();
        $.each(isos, function(index, volume) {
            var isoId = volume.os_distro + '*' + volume.name + '*' + volume.os_version;
            if (!kimchi.isoInfo[isoId]) {
                volume.isoId = isoId;
                volume.capacity = kimchi.changetoProperUnit(volume.capacity, 1);
                kimchi.isoInfo[isoId] = volume;
                html += kimchi.substitute(template, volume);
            }
        });
        $('#list-local-iso').append(html);
        $('#local-iso-field').show();
    };

    $('#select-all-local-iso').click(function() {
        $('#list-local-iso [type="checkbox"]').prop('checked', $(this).prop('checked'));
        if ($(this).prop('checked')) {
            $('#btn-template-local-iso-create').removeAttr('disabled');
        } else {
            $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        }
    });

    $('#list-local-iso').on('click', '[type="checkbox"]', function() {
        var checkedLength = $('#list-local-iso [type="checkbox"]:checked').length;
        if (checkedLength) {
            $('#btn-template-local-iso-create').removeAttr('disabled');
            var length = $('#list-local-iso [type="checkbox"]').length;
            $('#select-all-local-iso').prop('checked', length == checkedLength);
        } else {
            $('#select-all-local-iso').prop('checked', false);
            $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        }
    });

    $('#btn-template-local-iso-create').click(function() {
        submitIso('form-local-iso');
    });

    //1-1-2 local iso file
    var initIsoFileField = function() {
        $('#iso-file-check').prop('checked', false);
        $('#iso-file-box').hide();
        $('#iso-file').val('');
        $('#btn-template-file-create').attr('disabled', 'disabled');
    };

    $('#iso-file-check').click(function() {
        if ($(this).prop('checked')) {
            $('#iso-file-box').slideDown();
        } else {
            $('#iso-file-box').slideUp();
        }
    });

    $('#iso-file').on('input propertychange', function() {
        if ($('#iso-file').val()) {
            $('#btn-template-file-create').removeAttr('disabled');
        } else {
            $('#btn-template-file-create').attr('disabled', 'disabled');
        }
    });

    $('#btn-template-file-create').click(function() {
        var isoFile = $('#iso-file').val();
        if (!kimchi.template_check_path(isoFile)) {
            kimchi.message.error.code('KCHAPI6003E');
            return;
        }
        var data = {
            "cdrom" : isoFile
        };
        addTemplate(data);
    });

    //1-2 remote iso
    $('#iso-remote').css('opacity', 0.3).css('cursor', 'not-allowed');

    var enabledRemoteIso = function() {
        if (kimchi.capabilities == undefined) {
            setTimeout(enabledRemoteIso, 2000);
            return;
        }

        if (kimchi.capabilities.qemu_stream != true) {
            return;
        }

        $('#iso-remote').css('opacity', 1).css('cursor', 'pointer');
        $('#iso-remote').click(function() {
            kimchi.switchPage('iso-type-box', 'iso-remote-box');
            initRemoteIsoField();
            initIsoUrlField();
            kimchi.listDistros(function(isos) {
                showRemoteIsoField(isos);
            }, function() {
            });
        });
    };
    enabledRemoteIso();

    $('#iso-remote-box-back').click(function() {
        kimchi.switchPage('iso-remote-box', 'iso-type-box', 'right');
    });

    //1-2-1 remote iso list
    var initRemoteIsoField = function() {
        $('#load-remote-iso').show();
        $('#remote-iso-field').hide();
        $('#iso-url-field').hide();
        $('#select-all-remote-iso').prop('checked', false);
        $('#btn-template-remote-iso-create').attr('disabled', 'disabled');
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
                    html += kimchi.substitute(template, volume);
                }
            });
            $('#list-remote-iso').html(html);
            $('#load-remote-iso').hide()
            $('#remote-iso-field').show();
            $('#iso-url-field').show();
        } else {
            $('#load-remote-iso').hide()
            $('#iso-url-field').show();
            kimchi.message.warn(i18n['KCHTMPL6001W']);
        }
    };

    $('#select-all-remote-iso').click(function() {
        $('#list-remote-iso [type="checkbox"]').prop('checked', $(this).prop('checked'));
        if ($(this).prop('checked')) {
            $('#btn-template-remote-iso-create').removeAttr('disabled');
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
        $('#iso-url-check').prop('checked', false);
        $('#iso-url-box').hide();
        $('#iso-url').val('');
        $('#btn-template-url-create').attr('disabled', 'disabled');
    }

    $('#iso-url-check').click(function() {
        if ($(this).prop('checked')) {
            $('#iso-url-box').slideDown();
        } else {
            $('#iso-url-box').slideUp();
        }
    });

    $('#iso-url').on('input propertychange', function() {
        if ($('#iso-url').val()) {
            $('#btn-template-url-create').removeAttr('disabled');
        } else {
            $('#btn-template-url-create').attr('disabled', 'disabled');
        }
    });

    $('#vm-image-local').click(function(){
        kimchi.switchPage('iso-type-box', 'vm-image-local-box');
    });
    $('#vm-image-local-box-back').click(function(){
        kimchi.switchPage('vm-image-local-box', 'iso-type-box', 'right');
    });
    $('input', '#vm-image-local-box').on('keyup cut paste', function(){
        setTimeout(function(){
            var isValid = kimchi.template_check_path($('input', '#vm-image-local-box').val());
            $('input', '#vm-image-local-box').toggleClass('invalid-field', !isValid);
            $('button', $('.body', '#vm-image-local-box')).button(isValid ? "enable" : "disable");
        }, 0);
    });
    $('button', $('.body', '#vm-image-local-box')).button({
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
            kimchi.message.error.code('KCHAPI6004E');
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
            kimchi.window.close();
            kimchi.topic('templateCreated').publish();
        }, function(err) {
            if(callback) callback();
            kimchi.message.error(err.responseJSON.reason);
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
                    kimchi.topic('templateCreated').publish(data);
                    if (successNum === length) {
                        kimchi.window.close();
                    }
                }, function(err) {
                    kimchi.message.error(err.responseJSON.reason);
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
