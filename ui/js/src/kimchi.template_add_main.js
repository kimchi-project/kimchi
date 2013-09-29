/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Xin Ding <xinding@cn.ibm.com>
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
    // 1-1 local iso
    $('#iso-local').click(function() {
        kimchi.switchPage('iso-type-box', 'iso-local-box');
        initLocalIsoField();
        initIsoFileField();
        kimchi.listIsos(function(isos) {
            if (isos && isos.length) {
                showLocalIsoField(isos);
            } else {
                //deep scan is unavailable by now.
                //kimchi.listDeepScanIsos(function(isos) {
                //    showLocalIsoField(isos);
                //}, function(err) {
                //    kimchi.message.error(err.responseJSON.reason);
                //});
            }
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    });

    $('#iso-local-box-back').click(function() {
        kimchi.switchPage('iso-local-box', 'iso-type-box', 'right');
    });

    //1-1-1 local iso list
    var initLocalIsoField = function() {
        $('#local-iso-field').hide();
        $('#select-all-local-iso').prop('checked', false);
        $('#btn-template-local-iso-create').attr('disabled', 'disabled');
    };

    var showLocalIsoField = function(isos) {
        if (isos && isos.length) {
            kimchi.isoInfo = {};
            var html = '';
            var template = $('#tmpl-list-local-iso').html();
            $.each(isos, function(index, volume) {
                var isoId = volume.os_distro + '*' + volume.name + '*' + volume.os_version;
                if (!kimchi.isoInfo[isoId]) {
                    volume.isoId = isoId;
                    kimchi.isoInfo[isoId] = volume;
                    html += kimchi.template(template, volume);
                }
            });
            $('#list-local-iso').html(html);
            $('#local-iso-field').show();
        } else {
            kimchi.message.warn(i18n['msg.fail.template.no.iso']);
        }
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
            kimchi.message.error(i18n['msg.invalid.path']);
            return;
        }
        var data = {
            "name" : kimchi.get_iso_name(isoFile),
            "cdrom" : isoFile
        };
        addTemplate(data);
    });

    //1-2 remote iso
    $('#iso-remote').css('opacity', 0.3).css('cursor', 'not-allowed');
    /*
    $('#iso-remote').click(function() {
        kimchi.switchPage('iso-type-box', 'iso-remote-box');
        initRemoteIsoField();
        initIsoUrlField();
        kimchi.listDistros(function(isos) {
            showRemoteIsoField(isos);
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    });
    */

    $('#iso-remote-box-back').click(function() {
        kimchi.switchPage('iso-remote-box', 'iso-type-box', 'right');
    });

    //1-2-1 remote iso list
    var initRemoteIsoField = function() {
        $('#remote-iso-field').hide();
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
                    html += kimchi.template(template, volume);
                }
            });
            $('#list-remote-iso').html(html);
            $('#remote-iso-field').show();
        } else {
            kimchi.message.warn(i18n['msg.fail.template.no.iso']);
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

    $('#btn-template-url-create').click(function() {
        var isoUrl = $('#iso-url').val();
        if (!kimchi.template_check_url(isoUrl)) {
            kimchi.message.error(i18n['msg.invalid.url']);
            return;
        }
        var data = {
            "name" : kimchi.get_iso_name(isoUrl),
            "cdrom" : isoUrl
        };
        addTemplate(data);
    });

    //do create
    var addTemplate = function(data) {
        kimchi.createTemplate(data, function() {
            kimchi.doListTemplates();
            kimchi.window.close();
        }, function(err) {
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
                    "name" : kimchi.get_iso_name(isoInfo.name),
                    "os_distro" : isoInfo.os_distro,
                    "os_version" : isoInfo.os_version,
                    "cdrom" : isoInfo.path
                };
                kimchi.createTemplate(data, function() {
                    successNum++;
                    if (successNum === length) {
                        kimchi.doListTemplates();
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
    var protocols = "((https|http|ftp|ftps|tftp)?://)?",
        userinfo = "(([0-9a-z_!~*'().&=+$%-]+:)?[0-9a-z_!~*'().&=+$%-]+@)?",
        ip = "(\\d{1,3}\.){3}\\d{1,3}",
        domain = "([0-9a-z_!~*'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6}",
        port = "(:\\d{1,5})?",
        address = "(/[\\w!~*'().;?:@&=+$,%#-]+)+",
        domaintype = [ protocols, userinfo, domain, port, address ],
        ipType = [ protocols, userinfo, ip, port, address ],
        validate = function(type) {
            return new RegExp('^' + type.join('') + '$');
        };
    if (url.constructor === String) {
        return validate(domaintype).test(url) || validate(iptype).test(url);
    }
    return false;
};

kimchi.template_check_path = function(filePath) {
    var reg = /((\/([0-9a-zA-Z-_ \.]+))+[\.]iso)$/;
    if (filePath.constructor === String) {
        return reg.test(filePath);
    }
    return false;
};

kimchi.get_iso_name = function(isoPath) {
    if ((isoPath.charAt(isoPath.length - 1) == "/") == true) {
        isoPath = isoPath.substring(0, isoPath.length - 1)
    }
    if (/.iso$/.test(isoPath)) {
        return isoPath.substring(isoPath.lastIndexOf("/") + 1,
                isoPath.lastIndexOf(".")) + new Date().getTime();
    } else {
        return isoPath.substring(isoPath.lastIndexOf("/") + 1) +
        new Date().getTime();
    }
};
