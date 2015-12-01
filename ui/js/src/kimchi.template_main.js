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
                '<span class="column-name">Template Name (ID)</span><!--' +
                '--><span class="column-type">OS</span><!--' +
                '--><span class="column-version">Version</span><!--' +
                '--><span class="column-processors">CPUs</span><!--' +
                '--><span class="column-memory">Memory</span><!-- ' +
                '--><span class="column-action" style="display:none">   ' +
                '    <span class="sr-only">Actions</span><!-- ' +
                '--></span> ' +
                '</li>';
            var templateHtml = $('#templateTmpl').html();
            $.each(result, function(index, value) {
                var isLocal;
                if (value.cdrom) {
                    isLocal = /^\//.test(value['cdrom']);
                } else {
                    for (var i = 0; i < value.disks.length; i++) {
                        if (value.disks[i].base) {
                            isLocal = /^\//.test(value.disks[i].base);
                            break;
                        }
                    }
                }
                if (isLocal) {
                    value.location = "plugins/kimchi/images/theme-default/icon-local.png";
                } else {
                    value.location = "plugins/kimchi/images/theme-default/icon-remote.png";
                }
                listHtml += wok.substitute(templateHtml, value);
            });
            $('#templateList').html(listHtml);
            kimchi.templateBindClick();
        } else {
            $('#templateList').html('');
            $('#noTemplates').show();
        }
        $('html').removeClass('processing');
    }, function(err) {
        wok.message.error(err.responseJSON.reason);
        $('html').removeClass('processing');
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
        $('html').addClass('processing');
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