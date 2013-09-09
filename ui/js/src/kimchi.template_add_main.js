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

    function init_iso_location_box() {
        $('#iso_location_box').hide();
        $('#iso_local').prop('checked', false);
        $('#iso_internet').prop('checked', false);
    }
    function init_iso_file_box() {
        $('#iso_file_box').hide();
        $('#iso_file').val('');
        $('#btn-template-iso-create').attr('disabled', 'disabled');
    }
    function init_iso_url_box() {
        $('#iso_url_box').hide();
        $('#iso_url').val('');
        $('#btn-template-url-create').attr('disabled', 'disabled');
    }

    $('#iso_file').on('input', function() {
        if ($('#iso_file').val()) {
            $('#btn-template-iso-create').removeAttr('disabled');
        } else {
            $('#btn-template-iso-create').attr('disabled', 'disabled');
        }
    });
    $('#iso_url').on('input', function() {
        if ($('#iso_url').val()) {
            $('#btn-template-url-create').removeAttr('disabled');
        } else {
            $('#btn-template-url-create').attr('disabled', 'disabled');
        }
    });

    $('#iso_specify').click(function() {
        $('#iso_location_box').slideDown();
        init_iso_field();
    });
    $('#iso_local').click(function() {
        $('#iso_file_box').slideDown();
        init_iso_url_box();
    });
    $('#iso_internet').click(function() {
        init_iso_file_box();
        $('#iso_url_box').slideDown();
    });

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
        kimchi.createTemplate(data, function() {
            kimchi.doListTemplates();
            kimchi.window.close();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
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
        kimchi.createTemplate(data, function() {
            kimchi.doListTemplates();
            kimchi.window.close();
        }, function() {
            burnet.message.error(data.responseJSON.reason);
        });
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
        + "(/[0-9a-z_!~*'().;?:@&=+$,%#-]+)$";
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
