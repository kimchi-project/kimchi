/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2013-2016
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0invalid_indicator_template
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
                value.invalid_indicator = "invalid";
                if ($.isEmptyObject(value.invalid)) {
                    value.invalid_indicator = "valid";
                }
                if (typeof templateHtml !== 'undefined') {
                    listHtml += wok.substitute(templateHtml, value);
                }
            });
            $('ul#templates-grid').removeClass('hidden');
            $('#templates-container').removeClass('hidden');
            $('#templateList').html(listHtml);
            kimchi.templateBindClick();
            $('.wok-mask').fadeOut(300, function() {});
            $('.template-status[data-invalid="valid"]').hide();
        } else {
            $('#templateList').html('');
            $('#noTemplates').show();
            $('ul#templates-grid').addClass('hidden');
            $('#templates-container').addClass('hidden');
            $('.wok-mask').fadeOut(300, function() {});
        }

        var options = {
            valueNames: ['name-filter', 'os-type-filter', 'os-version-filter', 'cpus-filter', 'memory-filter']
        };
        var templatesList = new List('templates-container', options);
        $('[data-invalid="invalid"][data-toggle="tooltip"]').tooltip();
    }, function(err) {
        wok.message.error(err.responseJSON.reason);
        $('.wok-mask').fadeOut(300, function() {
            $('.wok-mask').addClass('hidden');
        });
    });
};

kimchi.toggleTemplatesGallery = function() {
    $(".wok-vm-list, .wok-vm-gallery").toggleClass("wok-vm-list wok-vm-gallery");
    $(".wok-list, .wok-gallery").toggleClass("wok-list wok-gallery");
    var text = $('#gallery-table-button span.text').text();
    $('#gallery-table-button span.text').text(text == i18n['KCHTMPL6005M'] ? i18n['KCHTMPL6004M'] : i18n['KCHTMPL6005M']);
    var buttonText = $('#gallery-table-button span.text').text();
    if (buttonText.indexOf("Gallery") !== -1) {
        // Currently in list view
        kimchi.setTemplateView("templateView", "list");
    } else {
        // Currently in gallery
        kimchi.setTemplateView("templateView", "gallery");
    }
};

kimchi.setTemplateView = function(name, value) {
    window.localStorage.setItem(name, value);
};

kimchi.readTemplateView = function(name) {
    var viewName = window.localStorage.getItem(name);
    if (viewName !== "") {
        return viewName;
    } else {
        return null;
    }
};

kimchi.showTemplateGallery = function() {
    $(".wok-vm-list").addClass("wok-vm-gallery");
    $(".wok-list").addClass("wok-gallery");
    $(".wok-vm-gallery").removeClass("wok-vm-list");
    $(".wok-gallery").removeClass("wok-list");
    $('#gallery-table-button span.text').text(i18n['KCHTMPL6004M']);
};

kimchi.showTemplateList = function() {
    $(".wok-vm-gallery").addClass("wok-vm-list");
    $(".wok-gallery").addClass("wok-list");
    $(".wok-vm-list").removeClass("wok-vm-gallery");
    $(".wok-list").removeClass("wok-gallery");
    $('#gallery-table-button span.text').text(i18n['KCHTMPL6005M']);
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
        kimchi.toggleTemplatesGallery();
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
    $('body').addClass('wok-list');
    var viewFound = kimchi.readTemplateView("templateView");
    if (viewFound) {
        if(viewFound === "gallery") {
            // should be showing gallery
            kimchi.showTemplateGallery();
        } else {
            // Should be showing list
            kimchi.showTemplateList();
       }
    } else {
        // Default to showing list
        kimchi.showTemplateList();
    }

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
