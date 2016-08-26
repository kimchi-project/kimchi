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
kimchi.template_add_main = function() {
    "use strict";
    var currentPage = 'iso-local-box';
    $('#loading-isos').fadeIn(100, function() {});
    kimchi.deepScanHandler = null;
    var isos = [];
    var local_isos = [];
    var remote_isos = [];

    var deepScan = function(button) {
        kimchi.deepScanHandler = kimchi.stepListDeepScanIsos(function(isos, isFinished) {
            if (isos && isos.length) {
                if (button === '#iso-search') {
                    $(button + '-loading').hide();
                    button = '#iso-more';
                    $(button + '-loading').show();
                }
                showLocalIsoField(isos);
                $('[data-toggle="tooltip"]').tooltip();
            } else {
                if (isFinished) {
                    wok.message.warn(i18n['KCHTMPL6001W'], '#local-iso-warning-container');
                }
            }
            if (isFinished) {
                $(button + '-loading').hide();
                $(button).show();
            }
        }, function(err) {
            wok.message.error(err.responseJSON.reason, '#local-iso-error-container');
            $(button + '-loading').hide();
            $(button).show();
        });
    };

    var initLocalIsoField = function() {
        kimchi.isoInfo = {};
        $('#local-iso-field').hide();
        $('#select-all-local-iso').prop('checked', false);
        $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        $('#btn-template-netboot-create').attr('disabled', 'disabled');
        $('#iso-search').hide();
        $('#iso-more').hide();
        $('#iso-search-loading').hide();
        $('#iso-more-loading').hide();
        $('#list-local-iso').empty();

        // Resets input fields and hide other buttons
        $('#iso-file').val(''); // 1 - Folder path text
        $('#iso-url').val(''); // 4 - Remote folder path text
        $('#btn-template-file-create').attr('disabled', 'disabled').css('display', 'inline-block'); // 1 - Folder path
        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display', 'none'); // 2 - Selected ISOs
        $('#btn-template-netboot-create').attr('disabled', 'disabled').css('display', 'none'); // 3 - Netboot
        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false); // False to all select-all checkboxes
        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false); // False to all list checkboxes
    };

    var showLocalIsoField = function(isos) {
        var html = '';
        var template = $('#tmpl-list-local-iso').html();
        $.each(isos, function(index, volume) {
            if ((volume.path).indexOf('http') === -1) { // Didn't find 'http', so must be local
                volume.icon = 'fa fa-hdd-o';
            } else {
                volume.icon = 'fa fa-globe';
            }
            if ((volume.path).substr((volume.path).lastIndexOf('.')+1) === 'iso'){
                volume.format = 'iso';
            } else {
                volume.format = 'img';
            }
            if (!volume.hasOwnProperty('has_permission')) {
                volume.has_permission = true;
            }
            if (volume.has_permission){
                volume.volume_hidden = 'hidden';
            } else {
                volume.disabled = "disabled";
            }
            var isoId = volume.os_distro + '*' + volume.name + '*' + volume.os_version;
            if (!kimchi.isoInfo[isoId]) {
                volume.isoId = isoId;
                volume.capacity = wok.changetoProperUnit(volume.capacity, 1);
                if (volume.capacity === "") {
                    volume.capacity = i18n['KCHTMPL6006M'];
                }
                kimchi.isoInfo[isoId] = volume;
                html += wok.substitute(template, volume);
            }
        });

        $('#list-local-iso').append(html);
        $('#local-iso-field').show();
    };

    var initIsoFileField = function() {
        $('#iso-file').val('');
        $('#iso-url').val('');
        $('#btn-template-file-create').attr('disabled', 'disabled').css('display', 'inline-block');
        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display', 'none'); // 2 - Selected ISOs
        $('#btn-template-netboot-create').attr('disabled', 'disabled').css('display', 'none'); // 3 - Netboot
        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false); // False to all select-all checkboxes
        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false); // False to all list checkboxes
    };

    $('#iso-file').on('input propertychange keyup focus cut paste click', function() {
        $('#btn-template-file-create').css('display', 'inline-block'); // 1 - Folder path
        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false);
        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false);
        setTimeout(function() {
            var isValid = kimchi.template_check_path($('input#iso-file').val());
            $('input#iso-file').parent().toggleClass('has-error', !isValid);
            $('#btn-template-file-create').attr('disabled', (isValid ? false : true));
        }, 0);
        if ($('#iso-file').val()) {
            $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display', 'none'); // 2 - Selected ISOs
        } else {
            $('#btn-template-file-create').attr('disabled', 'disabled');
        }
        $('#btn-template-netboot-create').attr('disabled', 'disabled').css('display', 'none'); // 3 - Netboot
    });

    initLocalIsoField();
    initIsoFileField();

    kimchi.listIsos(function(local_isos) { //local ISOs
        kimchi.listDistros(function(remote_isos) {  //remote ISOs
            isos = local_isos.concat(remote_isos); //all isos
            if (isos && isos.length) {
                showLocalIsoField(isos);
                $('#iso-more').show();
            } else {
                $('#iso-search').show();
            }
            $('#loading-isos').fadeOut(100, function() {});
            $('[data-toggle="tooltip"]').tooltip();
        });
    }, function(err) {
        wok.message.error(err.responseJSON.reason, '#local-iso-error-container');
        $('#loading-isos').fadeOut(300, function() {});
    });

    $('#template-add-window .modal-body .template-pager').animate({
        height: "689px"
    }, 400);

    var filterISOs = function(group, text) {
        text = text.trim().split(" ");
        var list = $('#isoRow').find('li');
        if(text === ""){
            list.show();
            return;
        }
        list.hide();

        list.filter(function(index, value){
            var $li = $(this);
            for (var i = 0; i < text.length; ++i){
                if ($li.is(":containsNC('" + text[i] + "')")) {
                    if (group === 'all') {
                        return true;
                    } else if (group === 'local') {
                        return true;
                    } else if (group === 'remote') {
                        return true;
                    }
                }
            }
            return false;
        }).show();
    };

    var setupFilters = function() {
        $('input#template-add-iso-filter', '#template-filter').on('keyup', function() {
            filterISOs("all", $(this).val());  // Default to 'all' for now
        });
    };

    setupFilters();

    $('#iso-search').click(function() {
        var settings = {
            content: i18n['KCHTMPL6002M']
        };
        wok.confirm(settings, function() {
            $('#iso-search').hide();
            $('#iso-search-loading').show();
            deepScan('#iso-search');
        });
    });

    $('#iso-more').click(function() {
        var settings = {
            content: i18n['KCHTMPL6002M']
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
        $('#list-local-iso [data-permission="true"]').prop('checked', $(this).prop('checked'));
        if ($(this).prop('checked')) {
            $('#iso-file').val('');
            $('#iso-file').parent().removeClass('has-error');

            $('#btn-template-file-create').attr('disabled', 'disabled').css('display', 'none'); // 1 - Folder path
            $('#btn-template-local-iso-create').removeAttr('disabled').css('display', 'inline-block'); // 2 - Selected ISOs
        } else {
            $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        }
        $('#btn-template-netboot-create').attr('disabled', 'disabled').css('display', 'none'); // 3 - Netboot
    });

    $('#list-local-iso').on('click', '[type="checkbox"]', function() {
        $('#iso-file').parent().removeClass('has-error');
        var checkedLength = $('#list-local-iso [type="checkbox"]:checked').length;
        $('#iso-file').val('');
        $('#iso-url').val('');

        $('#btn-template-file-create').attr('disabled', 'disabled').css('display', 'none'); // 1 - Folder path
        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display', 'inline-block'); // 2 - Selected ISOs
        $('#btn-template-netboot-create').attr('disabled', 'disabled').css('display', 'none'); // 3 - Netboot

        if (checkedLength) {
            $('#btn-template-local-iso-create').removeAttr('disabled');
            var length = $('#list-local-iso [type="checkbox"]').length;
            $('#select-all-local-iso').prop('checked', length === checkedLength);
            $('#btn-template-local-iso-create').removeAttr('disabled');
        } else {
            $('#select-all-local-iso').prop('checked', false);
            $('#btn-template-local-iso-create').attr('disabled', 'disabled');
        }
    });

    $('#btn-template-netboot-create').click(function() {
        var data = {
            "source_media": {"type": "netboot"}
        };
        addTemplate(data, function() {
            $('#btn-template-netboot-create').text(i18n['KCHAPI6005M']);
            $('#btn-template-netboot-create').prop('disabled', false);
        });
    });

    $('#btn-template-local-iso-create').click(function() {
        $('input', '#iso-file-box').prop('disabled', true);
        $('#btn-template-local-iso-create').text(i18n['KCHAPI6008M']);
        $('#btn-template-local-iso-create').prop('disabled', true);
        submitIso();
    });

    $('#btn-template-file-create').click(function() {
        var isoFile = $('#iso-file').val();
        $('input', '#iso-file-box').prop('disabled', true);
        $('#btn-template-file-create').text(i18n['KCHAPI6008M']);
        $('#btn-template-file-create').prop('disabled', true);
        if (!kimchi.template_check_path(isoFile)) {
            wok.message.error(i18n['KCHAPI6003E'],'#local-iso-error-container');
            return;
        }
        var data = {
            "source_media": {"type": "disk", "path": isoFile}
        };
        addTemplate(data, function() {
            $('input', '#iso-file-box').prop('disabled', false);
            $('#btn-template-file-create').text(i18n['KCHAPI6005M']);
            $('#btn-template-file-create').prop('disabled', false);
        });
    });

    var enabledRemoteIso = function() {
        if (kimchi.capabilities === undefined) {
            setTimeout(enabledRemoteIso, 2000);
            return;
        }

        if (kimchi.capabilities.qemu_stream !== true) {
            return;
        }
    };

    enabledRemoteIso();

    var initRemoteIsoField = function() {
        $('#load-remote-iso').show();
        $('#remote-iso-field').hide();
        $('#iso-url-field').hide();
        $('#select-all-remote-iso').prop('checked', false);

        $('#iso-file').val('');
        $('#iso-url').val('');

        $('#btn-template-file-create').attr('disabled', 'disabled').css('display', 'none'); // 1 - Folder path
        $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display', 'none'); // 2 - Selected ISOs
        $('#btn-template-netboot-create').attr('disabled', 'disabled').css('display', 'none'); // 3 - Netboot
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
            $('#load-remote-iso').hide();
            $('#remote-iso-field').show();
            $('#iso-url-field').show();
        } else {
            $('#load-remote-iso').hide();
            $('#iso-url-field').show();
            wok.message.warn(i18n['KCHTMPL6001W'],"#remote-iso-warning-container");
        }
    };

    $('#iso-url').on('input propertychange keyup focus cut paste click', function() {
        $('#select-all-local-iso, #select-all-remote-iso').prop('checked', false);
        $('#list-local-iso [type="checkbox"], #list-remote-iso [type="checkbox"]').prop('checked', false);
        setTimeout(function() {
            var isValid = kimchi.template_check_url($('input#iso-url').val());
            $('input#iso-url').parent().toggleClass('has-error', !isValid);
        }, 0);
    });

    $('#image-src').change(function() {
        if (this.checked) {
            if (currentPage === 'netboot-path') {
                kimchi.switchPage(currentPage, 'iso-local-box', 'right');
            }
            currentPage = 'iso-local-box';
            $('#template-add-window .modal-body .template-pager').animate({
                height: "700px"
            }, 400);
            initLocalIsoField();
            initIsoFileField();
            $('#loading-isos').fadeIn(100, function() {});
            kimchi.listIsos(function(local_isos) { //local ISOs
                kimchi.listDistros(function(remote_isos) {  //remote ISOs

                    isos = local_isos.concat(remote_isos); //all isos
                    if (isos && isos.length) {
                        showLocalIsoField(isos);
                        $('#iso-more').show();
                    } else {
                        $('#iso-search').show();
                    }
                    $('#loading-isos').fadeOut(100, function() {});
                });
            }, function(err) {
                wok.message.error(err.responseJSON.reason, '#local-iso-error-container');
                $('#loading-isos').fadeOut(300, function() {});
            });
            setupFilters();
            enabledRemoteIso();
        }
    });

    $('#netboot-src').change(function() {
        if (this.checked) {
            if (currentPage === 'iso-local-box') {
                kimchi.switchPage(currentPage, 'netboot-path', 'left');
            }
            currentPage = 'netboot-path';
            $('#template-add-window .modal-body .template-pager').animate({
                height: "300px"
            }, 400);
            $('#btn-template-file-create').attr('disabled', 'disabled').css('display', 'none'); // 1 - Folder path
            $('#btn-template-local-iso-create').attr('disabled', 'disabled').css('display', 'none'); // 2 - Selected ISOs
            $('#btn-template-netboot-create').removeAttr('disabled').css('display', 'inline-block'); // 3 - Netboot
        }
    });

    //do create
    var addTemplate = function(data, callback) {
        kimchi.createTemplate(data, function() {
            if (callback) {
                callback();
            }
            kimchi.doListTemplates();
            wok.window.close();
            wok.topic('templateCreated').publish();
        }, function(err) {
            if (callback) {
                callback();
            }
            wok.message.error(err.responseJSON.reason, '#alert-modal-container');
        });
    };

    var submitIso = function() {
        var formData = $('#form-local-iso').serializeObject();
        if (formData.iso) {
            var length = 0;
            var successNum = 0;
            var addTemplate = function(isoInfo) {
                var data = {
                    "os_distro": isoInfo.os_distro,
                    "os_version": isoInfo.os_version,
                    "source_media": {"type": "disk", "path": isoInfo.path}
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
                    wok.message.error(err.responseJSON.reason, '#alert-modal-container');
                    $('input', '#iso-file-box').prop('disabled', false);
                    $('#btn-template-local-iso-create').text(i18n['KCHAPI6005M']);
                    $('#btn-template-local-iso-create').prop('disabled', false);
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
