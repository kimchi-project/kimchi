/*
 * Project Wok
 *
 * Copyright IBM, Corp. 2013-2015
 *
 * Code derived from Project Kimchi
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
wok.widget.Grid = function(opts) {
    "use strict";
    this.opts = $.extend({}, this.opts, opts);
    this.createDOM();
    this.reload();
};

wok.widget.Grid.prototype = (function() {
    "use strict";
    var htmlStr = [
        '<div id="{id}" class="grid wok-grid">',
            '<div class="wok-grid-message hidden">',
                '<div class="alert alert-danger fade in" role="alert">',
                    '<p><strong>{message}</strong> ',
                    '<span class="detailed-text"></span></p>',
                    '<p><button class="btn btn-primary btn-xs retry-button">',
                        '{buttonLabel}',
                    '</button></p>',
                '</div>',
            '</div>',
            '<div class="grid-content wok-grid-content">',
                    '<table class="wok-table table table-striped">',
                        '<thead class="wok-grid-header-container"></thead>',
                        '<tbody class="wok-grid-body-container">',
                        '</tbody>',
                    '</table>',
            '</div>',
            '<div class="wok-grid-mask hidden">',
                '<div class="wok-grid-loader-container">',
                    '<div class="wok-grid-loading">',
                        '<div class="wok-grid-loading-icon"></div>',
                        '<div class="wok-grid-loading-text">',
                            '{loading}',
                        '</div>',
                    '</div>',
                '</div>',
            '</div>',
        '</div>'
    ].join('');

    var setupHeaders = function(header, body, fields) {
        var colGroup = $('<colgroup></colgroup>').appendTo(header);
        var headerRow = $('<tr></tr>').appendTo(header);
        $.each(fields || [], function(i, field) {
            $('<col class="' +
                field['class'] +
            '"/>')
                .appendTo(colGroup);
            $('<th><div class="wok-text-header">' +
                field['label'] +
            '</div></th>').appendTo(headerRow);
        });

        var totalWidth = 0;
        return totalWidth;
    };

    var getValue = function(name, obj) {
        var result;
        if(!Array.isArray(name)) {
            name=name.parseKey();
        }
        if(name.length!==0) {
            var tmpName=name.shift();
            if(obj[tmpName]!==undefined) {
                    result=obj[tmpName];
            }
            if(name.length!==0) {
                    result=getValue(name,obj[tmpName]);
            }
        }
        return(result);
    };

    var fillBody = function(container, fields) {
        var data = this.data;
        $.each(data, function(i, row) {
            var rowNode = $('<tr></tr>').appendTo(container);
            $.each(fields, function(fi, field) {
                var value = getValue(field['name'], row);
                $('<td><div class="wok-cell-text"' + (field['makeTitle'] === true ? ' title="' + value + '"' : '' ) + '>' + value.toString() + '</div></td>'
                ).appendTo(rowNode);
            });
        });
    };

    var stylingRow = function(row, className, add) {
        var index = $(row).index() + 1;
        $('tr', this.bodyContainer)
            .removeClass(className);

        if(add === false) {
            return;
        }

        $('tr:nth-child(' + index + ')', this.bodyContainer)
            .addClass(className);
    };

    var setBodyListeners = function() {
        if(this['opts']['rowSelection'] !== 'disabled') {
            $('tr', this.gridBody).on('mouseover', {
                grid: this
            }, function(event) {
                if (! $(this).hasClass('no-hover')) {
                    stylingRow.call(event.data.grid, this, 'hover');
                }
            });

            $('tr', this.gridBody).on('mouseout', {
                grid: this
            }, function(event) {
                stylingRow.call(event.data.grid, this, 'hover', false);
            });

            $('tr', this.gridBody).on('click', {
                grid: this
            }, function(event) {
                var grid = event.data.grid;
                grid.selectedIndex = $(this).index();
                stylingRow.call(grid, this, 'selected');
                grid['opts']['onRowSelected'] && grid['opts']['onRowSelected']();
            });
        }

    };

    var setData = function(data) {
        this.data = data;
        fillBody.call(this, this.bodyContainer, this['opts']['fields']);
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
        var data = this['opts']['data'];
        if(!data) {
            return;
        }

        $(this.messageNode).addClass('hidden');

        if($.isArray(data)) {
            return this.setData(data);
        }

        if($.isFunction(data)) {
            var loadData = data;
            $(this.maskNode).removeClass('hidden');
            loadData($.proxy(function(data) {
                this.setData(data);
                $(this.maskNode).addClass('hidden');
            }, this));
        }
    };

    var createDOM = function() {
        var containerID = this['opts']['container'];
        var container = $('#' + containerID);
        var gridID = this['opts']['id'];
        var rowSelection = this['opts']['rowSelection'] || 'single';
        var domNode = $(wok.substitute(htmlStr, {
            id: gridID,
            loading: i18n['WOKGRD6001M'],
            message: i18n['WOKGRD6002M'],
            buttonLabel: i18n['WOKGRD6003M'],
            detailedLabel: i18n['WOKGRD6004M']
        })).appendTo(container);
        this.domNode = domNode;

        var theTable = $('.wok-table', domNode);
        var theContainer = $('.wok-grid-content', domNode);
        var headerContainer = $('.wok-grid-header-container', domNode);
        var bodyContainer = $('.wok-grid-body-container', domNode);
        setupHeaders(headerContainer, bodyContainer, this['opts']['fields']);
        this.theTable = theTable;
        this.theContainer = theContainer;
        this.headerContainer = headerContainer;
        this.bodyContainer = bodyContainer;

        var height = domNode.height();
        var width = domNode.width();

        var title = this['opts']['title'];
        var titleNode = null;
        if(title) {
            titleNode = $('<caption class="sr-only">' + title + '</caption>').prependTo(theTable);
        }

        var toolbarButtons = this['opts']['toolbarButtons'];
        var toolbarNode = null;
        var btnHTML, dropHTML = [];
        if(toolbarButtons) {
            toolbarNode = $('<div class="btn-group"></div>');
            toolbarNode.prependTo(theContainer);
            if(toolbarButtons.length > 1) {
                dropHTML = ['<div class="dropdown menu-flat">',
                    '<button id="wok-dropdown-button-', containerID, '" class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown">',
                    '<span class="edit-alt"></span>Actions<span class="caret"></span>',
                    '</button>',
                    '<ul class="dropdown-menu"></ul>',
                    '</div>'
                ].join('');
                $(dropHTML).appendTo(toolbarNode);
                $.each(toolbarButtons, function(i, button) {
                    btnHTML = [
                        '<li role="presentation"', button.critical === true ? ' class="critical"' : '', '><a data-toggle="modal"',
                        button.id ? (' id="' + button.id + '"') : '',
                        ' class="', button.disabled === true ? ' disabled' : '', '">',
                        button.class ? ('<i class="' + button.class) + '"></i>' : '',
                        button.label,
                        '</a></li>'
                    ].join('');
                    var btnNode = $(btnHTML).appendTo(toolbarNode[0].children[0].children[1]);
                    button.onClick && btnNode.on('click', button.onClick);
                });
            }else {
                $.each(toolbarButtons, function(i, button) {
                    btnHTML = [
                        '<button data-dismiss="modal" ',
                            button['id'] ? (' id="' + button['id'] + '"') : '',
                            ' class="btn btn-primary',
                                button['class'] ? (' ' + button['class']) : '',
                                '"',
                                button['disabled'] === true ? ' disabled' : '',
                                '>',
                                button['label'],
                        '</button>'
                    ].join('');
                    var btnNode = $(btnHTML).appendTo(toolbarNode);
                    button['onClick'] &&
                        btnNode.on('click', button['onClick']);
                });      
            }

        }

        // var domHeight = domNode && $(domNode).height() || 0;
        // var toolbarHeight = toolbarNode && $(toolbarNode).height() || 0;
        // var maskHeight = domHeight - toolbarHeight;

        // var maskContainer = $('.wok-grid-loader-container',domNode);
        // maskContainer.css({'top': toolbarHeight+'px', 'height': maskHeight+'px'});
        // this.maskContainer = maskContainer;

        var maskNode = $('.wok-grid-mask', domNode);
        this.maskNode = maskNode;

        var messageNode = $('.wok-grid-message', domNode);
        this.messageNode = messageNode;

        //fixTableLayout.call(this);

        var gridBody = $('.wok-grid-body', domNode);
        this.gridBody = gridBody;

        var data = this['opts']['data'];

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
            fields: null
        },
        createDOM: createDOM,
        setData: setData,
        getSelected: getSelected,
        reload: reload,
        //destroy: destroy,
        showMessage: showMessage
    };
})();
