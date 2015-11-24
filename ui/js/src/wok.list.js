/*
 * Project Wok
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
wok.widget.List = function(opts) {
    "use strict";
    this.opts = $.extend({}, this.opts, opts);
    this.createDOM();
    this.reload();
};

wok.widget.List.prototype = (function() {
    "use strict";
    var htmlStr = [
        '<div id="{id}-section" class="panel panel-default">',
            '<div class="panel-heading">',
            '</div>',
            '<div id="content-{id}" class="panel-body">',
                '<div id="{id}-container">',
                    '<div class="wok-list-message clearfix hidden">',
                        '<div class="alert alert-danger fade in" role="alert">',
                            '<p><strong>{message}</strong> ',
                            '<span class="detailed-text"></span></p>',
                            '<p><button class="btn btn-primary btn-xs retry-button">',
                                '{buttonLabel}',
                            '</button></p>',
                        '</div>',
                    '</div>',
                    '<div id="{id}-btn-group" class="btn-group wok-single-button hidden">',

                    '</div>',
                    '<div id="{id}" class="row clearfix">',
                        '<div class="wok-list-content">',
                            '<table class="wok-list-table table table-striped" id="list">',
                            '</table>',
                        '</div>',
                    '</div>',
                    '<div class="wok-list-mask hidden">',
                        '<div class="wok-list-loader-container">',
                            '<div class="wok-list-loading">',
                                '<div class="wok-list-loading-icon"></div>',
                                '<div class="wok-list-loading-text">',
                                    '{loading}',
                                '</div>',
                            '</div>',
                        '</div>',
                    '</div>',
                '</div>',
            '</div>',
        '</div>'
    ].join('');

    var getValue = function(name, obj) {
        var result;
        if (!Array.isArray(name)) {
            name = name.parseKey();
        }
        if (name.length !== 0) {
            var tmpName = name.shift();
            if (obj[tmpName] !== undefined) {
                result = obj[tmpName];
            }
            if (name.length !== 0) {
                result = getValue(name, obj[tmpName]);
            }
        }
        return (result);
    };


    var fillButton = function(btnContainer){
        var addOrGenerateBtn = this.opts.toolbarButtons[0];
        var singleBtnHTML = [
                '<a class="btn btn-primary" href="#"', (addOrGenerateBtn.id ? (' id="' + addOrGenerateBtn.id + '"') : ''),' role="button">',
                    addOrGenerateBtn.class ? ('<i class="' + addOrGenerateBtn.class) + '"></i> ' : '',
                    addOrGenerateBtn.label,
                '</a>'
            ].join('');
            var singleBtn = $(singleBtnHTML).appendTo(btnContainer);
            $(singleBtn).click(function(e) {
              e.preventDefault();
            });
            addOrGenerateBtn.onClick && singleBtn.on('click', addOrGenerateBtn.onClick);
    };

    var fillBody = function(container, fields) {

        var toolbarButtons = this.opts.toolbarButtons;
        var actionDropdownHtml;
        var data = this.data;
        var tbody = ($('tbody', container).length && $('tbody', container)) || $('<tbody></tbody>').appendTo(container);
        tbody.empty();
        if (typeof data !== 'undefined' && data.length > 0) {
            $.each(data, function(i, row) {
                var rowNode = $('<tr></tr>').appendTo(tbody);
                var columnNodeHTML;
                var columnData = '';
                var state = '';
                var styleClass = '';
                if (toolbarButtons) {
                    actionDropdownHtml = [
                        '<td>',
                            '<div class="dropdown menu-flat">',
                                '<button id="wok-dropdown-button-', i, '" class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown">',
                                    '<span class="edit-alt"></span>Actions<span class="caret"></span>',
                                '</button>',
                                '<ul class="dropdown-menu" role="menu" aria-labelledby="action-dropdown-menu-', i, '">',
                                '</ul>',
                            '</div>',
                        '</td>'
                    ].join('');
                }
                $.each(fields, function(fi, field) {
                    var value = getValue(field.name, row);
                    if (field.type === 'status' && field.name === 'enabled') {
                        styleClass = (value === true ? '' : ' disabled');
                        state = [
                            '<span class="wok-repository-status ',
                            value === true ? 'enabled' : 'disabled',
                            '"><i class="fa fa-power-off"></i></span>'
                        ].join('');
                    }
                    columnData += (field.type === 'name') ? ('<span class="wok-list-name">' + value.toString() + '</span>') : (field.type !== 'status' ? '<span class="wok-list-loading-icon-inline"></span><span class="wok-list-description">' + value.toString() + '</span>' : '');

                });
                columnNodeHTML = [
                    '<td>',
                        '<div class="wok-list-cell', styleClass, '">', state,
                            columnData,
                        '</div>',
                    '</td>'
                ].join('');
                $(columnNodeHTML).appendTo(rowNode);

                var actionMenuNode = $(actionDropdownHtml).appendTo(rowNode);

                $.each(toolbarButtons, function(i, button) {
                    var btnHTML = [
                        '<li role="presentation"', button.critical === true ? ' class="critical"' : '', '>',
                        '<a role="menuitem" tabindex="-1" data-dismiss="modal"', (button.id ? (' id="' + button.id + '"') : ''), (button.disabled === true ? ' class="disabled"' : ''),
                        '>',
                        button.class ? ('<i class="' + button.class) + '"></i>' : '',
                        button.label,
                        '</a></li>'
                    ].join('');
                    var btnNode = $(btnHTML).appendTo($('.dropdown-menu', rowNode));
                    button.onClick && btnNode.on('click', button.onClick);
                });
            });        
        } 
    };

    var stylingRow = function(row, className, add) {
        var index = $(row).index() + 1;
        $('tr', this.bodyContainer)
            .removeClass(className);
        if (add === false) {
            return;
        }
        $('tr:nth-child(' + index + ')', this.bodyContainer)
            .addClass(className);
    };

    var setBodyListeners = function() {
        if (this['opts']['rowSelection'] != 'disabled') {

            $('tr', this.bodyContainer).on('click', {
                grid: this
            }, function(event) {
                var grid = event.data.grid;
                if (!$(this).hasClass('generating')) {
                    grid.selectedIndex = $(this).index();
                    stylingRow.call(grid, this, 'selected');
                    grid['opts']['onRowSelected'] && grid['opts']['onRowSelected']();
                }
            });
        }
    };

    var setData = function(data) {
        this.data = data;
        fillBody.call(this, this.bodyContainer, this.opts.fields);
        setBodyListeners.call(this);
    };

    var getSelected = function() {
        return this.selectedIndex >= 0 ? this.data[this.selectedIndex] : null;
    };

    var showMessage = function(msg) {
        $('.detailed-text', this.messageNode).text(msg);
        $(this.messageNode).removeClass('hidden');
    };

    var hideMessage = function() {
        $(this.messageNode).addClass('hidden');
    };

    var reload = function() {
        var data = this.opts.data;
        if (!data) {
            return;
        }

        if ($.isArray(data)) {
            return this.setData(data);
        }

        if ($.isFunction(data)) {
            var loadData = data;
            $(this.maskNode).removeClass('hidden');
            loadData($.proxy(function(data) {
                this.setData(data);
                $(this.maskNode).addClass('hidden');
            }, this));
        }
    };

    var createDOM = function() {
        var containerID = this.opts.container;
        var container = $('#' + containerID);
        var gridID = this.opts.id;
        var data = this.opts.data;
        var rowSelection = this.opts.rowSelection || 'single';
        var domNode = $(wok.substitute(htmlStr, {
            id: gridID,
            loading: i18n.WOKGRD6001M,
            message: i18n.WOKGRD6002M,
            buttonLabel: i18n.WOKGRD6003M,
            detailedLabel: i18n.WOKGRD6004M
        })).appendTo(container);
        this.domNode = domNode;


        var titleContainer = $('.panel-heading', domNode);
        this.titleContainer = titleContainer;

        var title = this.opts.title;
        var titleNode = null;

        if (title) {
            titleNode = $('<h3 class="panel-title">' + title + '</h3>').appendTo(titleContainer);
        }

        var bodyContainer = $('.wok-list-table.table.table-striped', domNode);
        this.bodyContainer = bodyContainer;

        var singleButtonContainer = $('.wok-single-button', domNode);
        this.singleButtonContainer = singleButtonContainer;

        var gridBody = $('.wok-list-content', domNode);
        this.gridBody = gridBody;

        var maskNode = $('.wok-list-mask', domNode);
        this.maskNode = maskNode;

        var messageNode = $('.wok-list-message', domNode);
        this.messageNode = messageNode;


        fillButton.call(this,this.singleButtonContainer);

        $('.retry-button', domNode).on('click', {
            grid: this
        }, function(event) {
            event.data.grid.reload();
        });


    };

    return {
        opts: {
            container: null,
            id: null,
            rowSelection: 'single',
            onRowSelected: null,
            title: null,
            toolbarButtons: null,
            frozenFields: null,
            fields: null
        },
        createDOM: createDOM,
        setData: setData,
        getSelected: getSelected,
        reload: reload,
        showMessage: showMessage
    };
})();
