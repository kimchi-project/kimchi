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
        $(".wok-vm-list, .wok-vm-gallery").toggleClass("wok-vm-list wok-vm-gallery");
        $(".wok-list, .wok-gallery").toggleClass("wok-list wok-gallery");
        var text = $('#gallery-table-button span.text').text();
        $('#gallery-table-button span.text').text(text == i18n['KCHTMPL6005M'] ? i18n['KCHTMPL6004M'] : i18n['KCHTMPL6005M']);
    });

    $('.sort').on('click', function(event) {
        event.preventDefault();
        $('.filter-option').text($(this).text());
    });

}
kimchi.hideTitle = function() {
    $('#tempTitle').hide();
};

kimchi.template_main = function() {
    $('body').removeClass("wok-gallery").addClass("wok-list");
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
