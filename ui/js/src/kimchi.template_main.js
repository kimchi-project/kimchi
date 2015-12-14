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
    kimchi.listTemplates(function(result) {
        if (result && result.length) {
            $('#noTemplates').hide();
            var listHtml = '<li class="wok-vm-header">' +
                '<span class="column-name">'+i18n['KCHTMPL6004M']+'</span><!--' +
                '--><span class="column-type">'+i18n['KCHTMPL6005M']+'</span><!--' +
                '--><span class="column-version">'+i18n['KCHTMPL6006M']+'</span><!--' +
                '--><span class="column-processors">'+i18n['KCHTMPL6007M']+'</span><!--' +
                '--><span class="column-memory">'+i18n['KCHTMPL6008M']+'</span><!-- ' +
                '--><span class="column-action" style="display:none">   ' +
                '    <span class="sr-only">'+i18n['KCHTMPL6009M']+'</span><!-- ' +
                '--></span> ' +
                '</li>';
            var templateHtml = $('#templateTmpl').html();
            $.each(result, function(index, value) {
                listHtml += wok.substitute(templateHtml, value);
            });
            $('#templateList').html(listHtml);
            kimchi.templateBindClick();
        } else {
            $('#templateList').html('');
            $('#noTemplates').show();
        }
        $('.wok-mask').addClass('hidden');
    }, function(err) {
        wok.message.error(err.responseJSON.reason);
        $('.wok-mask').addClass('hidden');
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