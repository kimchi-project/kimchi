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
kimchi.template_add_main = function() {
    // 1-1
    function init_iso_location_box() {
        $('#iso_location_box').hide();
        $('#iso_local').prop('checked', false);
        $('#iso_internet').prop('checked', false);
        init_iso_file_box();
        init_iso_url_box();
    }
    // 1-2
    function init_iso_scan_box() {
        $('#iso_scan_box').hide();
        $('#iso_scan_type').prop('checked', false);
        $('#btn-iso-scan').attr('disabled', 'disabled');
        init_iso_field();
    }
    // 1-3
    function init_iso_distr_box() {
        init_iso_field();
    }
    // 1-1-1
    function init_iso_file_box() {
        $('#iso_file_box').hide();
        $('#iso_file').val('');
        $('#btn-template-iso-create').attr('disabled', 'disabled');
    }
    // 1-1-2
    function init_iso_url_box() {
        $('#iso_url_box').hide();
        $('#iso_url').val('');
        $('#btn-template-url-create').attr('disabled', 'disabled');
    }
    function init_iso_field() {
        $('#iso-field').hide();
        $('#select_all_iso').prop('checked', false);
        $('#btn-template-iso-selecte-create').attr('disabled', 'disabled');
    }

    // 1-1-1
    $('#iso_file').on('input propertychange', function() {
        if ($('#iso_file').val()) {
            $('#btn-template-iso-create').removeAttr('disabled');
        } else {
            $('#btn-template-iso-create').attr('disabled', 'disabled');
        }
    });
    // 1-1-2
    $('#iso_url').on('input propertychange', function() {
        if ($('#iso_url').val()) {
            $('#btn-template-url-create').removeAttr('disabled');
        } else {
            $('#btn-template-url-create').attr('disabled', 'disabled');
        }
    });

    var showIsoField = function(isos) {
        if (isos && isos.length) {
            kimchi.isoInfo = {};
            var html = '';
            var template = $('#tmpl-list-iso').html();
            $.each(isos, function(index, volume) {
                var isoId = volume.os_distro + '*' + volume.name + '*' + volume.os_version;
                if (!kimchi.isoInfo[isoId]) {
                    volume.isoId = isoId;
                    kimchi.isoInfo[isoId] = volume;
                    html += kimchi.template(template, volume);
                }
            });
            $('#list-iso').html(html);
            $('#iso-field').slideDown();
        } else {
            kimchi.message.warn(i18n['msg.fail.template.no.iso']);
        }
    };

    // 1-1
    $('#iso_specify').click(function() {
        $('#iso_location_box').slideDown();
        init_iso_scan_box();
        init_iso_distr_box();
    });
    // 1-2
    $('#iso_scan').click(function() {
        $('#iso_scan_box').slideDown();
        init_iso_location_box();
        init_iso_distr_box();
    });
    // 1-3
    $('#iso_distr').click(function() {
        init_iso_location_box();
        init_iso_scan_box();
        init_iso_field();
        kimchi.listDistros(function(result) {
            showIsoField(result);
        }, function() {
            kimchi.message.error(i18n['msg.fail.template.distr']);
        });
    });
    // 1-1-1
    $('#iso_local').click(function() {
        $('#iso_file_box').slideDown();
        init_iso_url_box();
    });
    // 1-1-2
    $('#iso_internet').click(function() {
        $('#iso_url_box').slideDown();
        init_iso_file_box();
    });
    // 1-2-1
    $('#iso_scan_shallow').click(function() {
        $('#btn-iso-scan').removeAttr('disabled');
    });
    // 1-2-2
    $('#iso_scan_deep').click(function() {
        $('#btn-iso-scan').removeAttr('disabled');
    });

    $('#select_all_iso').click(function() {
        $('#list-iso [type="checkbox"]').prop('checked', $(this).prop('checked'));
        if ($(this).prop('checked')) {
            $('#btn-template-iso-selecte-create').removeAttr('disabled');
        } else {
            $('#btn-template-iso-selecte-create').attr('disabled', 'disabled');
        }
    });

    $('#iso-field').on('click', '#list-iso [type="checkbox"]', function() {
        var checkedLength = $('#list-iso [type="checkbox"]:checked').length;
        var length = $('#list-iso [type="checkbox"]').length;
        var formData = $('#form-iso').serializeObject();
        if (checkedLength) {
            $('#btn-template-iso-selecte-create').removeAttr('disabled');
            $('#select_all_iso').prop('checked', length == checkedLength);
        } else {
            $('#select_all_iso').prop('checked', false);
            $('#btn-template-iso-selecte-create').attr('disabled', 'disabled');
        }
    });

    var addTemplate = function(data) {
        kimchi.createTemplate(data, function() {
            kimchi.doListTemplates();
            kimchi.window.close();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    };

    $('#btn-template-iso-create').click(function() {
        var iso_file = $('#iso_file').val();
        if (!kimchi.template_check_path(iso_file)) {
            kimchi.message.error(i18n['msg.invalid.path']);
            return;
        }
        var data = {
            "name" : kimchi.get_iso_name(iso_file),
            "cdrom" : iso_file
        };
        addTemplate(data);
    });

    $('#btn-template-url-create').click(function() {
        var iso_url = $('#iso_url').val();
        if (!kimchi.template_check_url(iso_url)) {
            kimchi.message.error(i18n['msg.invalid.url']);
            return;
        }
        var data = {
            "name" : kimchi.get_iso_name(iso_url),
            "cdrom" : iso_url
        };
        addTemplate(data);
    });

    $('#btn-iso-scan').click(function() {
        init_iso_field();
        if($('#iso_scan_shallow').prop('checked')) {
            kimchi.listIsos(function(result) {
                showIsoField(result);
            }, function() {
                kimchi.message.error(i18n['msg.fail.template.scan']);
            });
        } else if($('#iso_scan_deep').prop('checked')) {
            kimchi.listDeepScanIsos(function(result) {
                showIsoField(result);
            }, function() {
                kimchi.message.error(i18n['msg.fail.template.scan']);
            });
        }
    });

    $('#btn-template-iso-selecte-create').click(function() {
        var formData = $('#form-iso').serializeObject();
        if (formData.iso) {
            var length = 0;
            var successNum = 0;
            var addTemplate = function(isoInfo) {
                var data = {
                    "name" : 'Template' + new Date().getTime(),
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
    });

};

kimchi.template_check_url = function(url) {
    var strRegex = "^((https|http|ftp|ftps|tftp)?://)"
        + "?(([0-9a-z_!~*'().&=+$%-]+: )?[0-9a-z_!~*'().&=+$%-]+@)?"
        + "(([0-9]{1,3}\.){3}[0-9]{1,3}"
        + "|" + "([0-9a-z_!~*'()-]+\.)*"
        + "([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\."
        + "[a-z]{2,6})"
        + "(:[0-9]{1,4})?"
        + "(/[0-9a-zA-Z_!~*'().;?:@&=+$,%#-]+)$";
    var re = new RegExp(strRegex);
    if (url.constructor === String) {
        return re.test(url);
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
    if (/.iso$/.test(isoPath)) {
        return isoPath.substring(isoPath.lastIndexOf("/") + 1,
                isoPath.lastIndexOf(".")) + new Date().getTime();
    } else {
        return isoPath.substring(isoPath.lastIndexOf("/") + 1) +
        new Date().getTime();
    }
};
