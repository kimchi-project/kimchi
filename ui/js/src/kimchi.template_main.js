/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2014
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

kimchi.doListTemplates = function() {
    $('.wok-mask').removeClass('hidden');
    kimchi.listTemplates(function(result) {
        if (result && result.length) {
            $('#noTemplates').hide();
            var listHtml = '';
            var templateHtml = $('#templateTmpl').html();
            $.each(result, function(index, value) {
                listHtml += wok.substitute(templateHtml, value);
            });
            $('.wok-vm-list').removeClass('hidden');
            $('#templates-container').removeClass('hidden');
            $('#templateList').html(listHtml);
            kimchi.templateBindClick();
            $('.wok-mask').fadeOut(300, function() {});
        } else {
            $('#templateList').html('');
            $('#noTemplates').show();
            $('.wok-vm-list').addClass('hidden');
            $('#templates-container').addClass('hidden');
            $('.wok-mask').fadeOut(300, function() {});
        }

        var options = {
            valueNames: ['name-filter', 'os-type-filter', 'os-version-filter', 'cpus-filter', 'memory-filter']
        };
        var templatesList = new List('templates-container', options);

    }, function(err) {
        wok.message.error(err.responseJSON.reason);
        $('.wok-mask').fadeOut(300, function() {
            $('.wok-mask').addClass('hidden');
        });
    });
};

kimchi.templateBindClick = function() {
    $('.template-edit a').on('click', function(event) {
        event.preventDefault();
        var templateName = $(this).data('template');
        kimchi.selectedTemplate = templateName;
        wok.window.open("plugins/kimchi/template-edit.html");
    });
    $('.template-clone a').on('click', function(event) {
        event.preventDefault();
        kimchi.selectedTemplate = $(this).data('template');
        $('.wok-mask').removeClass('hidden');
        kimchi.cloneTemplate(kimchi.selectedTemplate, function() {
            kimchi.doListTemplates();
        }, function(err) {
            wok.message.error(err.responseJSON.reason);
            kimchi.doListTemplates();
        });
    });
    $('.template-delete a').on('click', function(event) {
        event.preventDefault();
        var $template = $(this);
        var settings = {
            title: i18n['KCHAPI6001M'],
            content: i18n['KCHTMPL6003M'],
            confirm: i18n['KCHAPI6002M'],
            cancel: i18n['KCHAPI6003M']
        };
        wok.confirm(settings, function() {
            var templateName = $template.data('template');
            kimchi.deleteTemplate(templateName, function() {
                kimchi.doListTemplates();
            }, function(err) {
                wok.message.error(err.responseJSON.reason);
            });
        }, function() {});
    });

    $('#gallery-table-button').on('click', function(event) {
        if ($("#templates-grid").hasClass('wok-vm-list')) {
            $("#templates-grid").removeClass("wok-vm-list");
            $("#templates-grid").addClass("wok-vm-gallery");
            $("#gallery-table-button").html("View Table <i class='fa fa-angle-right'></i><i class='fa fa-angle-right'></i><i class='fa fa-angle-right'></i>");
        } else {
            $("#templates-grid").removeClass("wok-vm-gallery");
            $("#templates-grid").addClass("wok-vm-list");
            $("#gallery-table-button").html("View Gallery <i class='fa fa-angle-right'></i><i class='fa fa-angle-right'></i><i class='fa fa-angle-right'></i>");
        }
    });
}
kimchi.hideTitle = function() {
    $('#tempTitle').hide();
};

kimchi.template_main = function() {
    if (wok.tabMode['templates'] === 'admin') {
        $('.tools').attr('style', 'display');
        $("#template-add").on("click", function(event) {
            wok.window.open({
                url: 'plugins/kimchi/template-add.html',
                close: function() {
                    if (kimchi.deepScanHandler) {
                        kimchi.deepScanHandler.stop = true;
                    }
                }
            });
        });
    }

    kimchi.doListTemplates();
};