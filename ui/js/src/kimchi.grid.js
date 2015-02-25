/*
 * Project Kimchi
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
kimchi.widget.Grid = function(opts) {
    this.opts = $.extend({}, this.opts, opts);
    this.createDOM();
    this.reload();
};

kimchi.widget.Grid.prototype = (function() {
    var htmlStr = [
        '<div id="{id}" class="grid">',
            '<div class="grid-content">',
                '<div class="grid-header">',
                    '<div class="grid-frozen-header-view">',
                        '<table class="grid-frozen-header-container">',
                        '</table>',
                    '</div>',
                    '<div class="grid-header-view">',
                        '<div class="grid-header-wrapper">',
                            '<table class="grid-header-container">',
                            '</table>',
                        '</div>',
                    '</div>',
                '</div>',
                '<div class="grid-body">',
                    '<div class="grid-frozen-body-view">',
                        '<div class="grid-frozen-body-wrapper">',
                            '<table class="grid-frozen-body-container">',
                            '</table>',
                        '</div>',
                    '</div>',
                    '<div class="grid-body-view">',
                        '<div class="grid-body-wrapper">',
                            '<table class="grid-body-container">',
                            '</table>',
                        '</div>',
                    '</div>',
                '</div>',
                '<div class="grid-resizer-leftmost hidden"></div>',
                '<div class="grid-resizer hidden"></div>',
            '</div>',
            '<div class="grid-footer"></div>',
            '<div class="grid-mask hidden">',
                '<div class="grid-loading">',
                    '<div class="grid-loading-icon"></div>',
                    '<div class="grid-loading-text">',
                        '{loading}',
                    '</div>',
                '</div>',
            '</div>',
            '<div class="grid-message hidden">',
                '<div class="grid-message-text">',
                    '{message}',
                    '<button class="retry-button btn-small">',
                        '{buttonLabel}',
                    '</button>',
                '</div>',
                '<div class="detailed-title">',
                    '{detailedLabel}',
                '</div>',
                '<div class="detailed-text"></div>',
            '</div>',
        '</div>'
    ].join('');

    var CONTAINER_NORMAL = 0, CONTAINER_FROZEN = 1;

    var setupHeaders = function(header, body, fields) {
        var colGroup = $('<colgroup></colgroup>').appendTo(header);
        var headerHeader = $('<thead></thead>');
        var headerRow = $('<tr></tr>').appendTo(headerHeader);
        $.each(fields || [], function(i, field) {
            $('<col class="' +
                field['class'] +
            '"/>')
                .appendTo(colGroup);
            $('<th><div class="cell-text-wrapper">' +
                field['label'] +
            '</div></th>').appendTo(headerRow);
        });
        headerHeader.appendTo(header);

        var totalWidth = 0;
        $('col', colGroup).each(function(index, col) {
            var width = $(col).width();
            totalWidth += width;
            $(col).css('width', width + 'px');
        });
        $(body).append(colGroup.clone());
        return totalWidth;
    };

    var getValue = function(name, obj) {
        var result=undefined;
        if(!Array.isArray(name)) {
            name=name.parseKey();
        }
        if(name.length!=0) {
            var tmpName=name.shift();
            if(obj[tmpName]!=undefined) {
                    result=obj[tmpName];
            }
            if(name.length!=0) {
                    result=getValue(name,obj[tmpName]);
            }
        }
        return(result);
    };

    var fillBody = function(container, fields) {
        var data = this.data;
        var tbody = ($('tbody', container).length && $('tbody', container))
            || $('<tbody></tbody>').appendTo(container);
        tbody.empty();
        $.each(data, function(i, row) {
            var rowNode = $('<tr></tr>').appendTo(tbody);
            $.each(fields, function(fi, field) {
                var value = getValue(field['name'], row);
                $('<td><div class="cell-text-wrapper"' +
                    (field['makeTitle'] === true
                        ? ' title="' + value + '"'
                        : ''
                    ) + '>' + value.toString() + '</div></td>'
                ).appendTo(rowNode);
            });
        });
    };

    var fixTableLayout = function(style) {
        $.each([
            this.frozenHeaderContainer,
            this.headerContainer,
            this.frozenBodyContainer,
            this.bodyContainer
        ], function(i, tableNode) {
            $(tableNode).css('table-layout', style || 'fixed');
        });
    };

    var initResizing = function(event) {
        var resizer = event.data.resizer;
        var pageX = event.pageX;
        var tailPos = $(this).width() + $(this).offset()['left'];
        var atResizer = Math.abs(pageX - tailPos) <= 2;
        var isResizing = !$(resizer).hasClass('hidden');
        $('body')[(atResizer || isResizing)
            ? 'addClass'
            : 'removeClass'
        ]('resizing');
    };

    var clearResizing = function(event) {
        $(event.data.resizer).hasClass('hidden') &&
            $('body').removeClass('resizing');
    };

    var stylingRow = function(row, className, add) {
        var index = $(row).index() + 1;
        $('tr', this.frozenBodyContainer)
            .removeClass(className);
        $('tr', this.bodyContainer)
            .removeClass(className);

        if(add === false) {
            return;
        }

        $('tr:nth-child(' + index + ')', this.frozenBodyContainer)
            .addClass(className);
        $('tr:nth-child(' + index + ')', this.bodyContainer)
            .addClass(className);
    };

    var setBodyListeners = function() {
        if(this['opts']['rowSelection'] != 'disabled') {
            $('tr', this.gridBody).on('mouseover', {
                grid: this
            }, function(event) {
                if (! $(this).hasClass('no-hover'))
                    stylingRow.call(event.data.grid, this, 'hover');
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

        $('.grid-body-view', this.domNode).on('scroll', {
            grid: this
        }, function(event) {
            var grid = event.data.grid;
            $('.grid-header .grid-header-view', grid.domNode)
                .prop('scrollLeft', this.scrollLeft);
            $('.grid-body .grid-frozen-body-view', grid.domNode)
                .prop('scrollTop', this.scrollTop);
        });
    };

    var setData = function(data) {
        this.data = data;
        fillBody.call(this, this.frozenBodyContainer, this['opts']['frozenFields']);
        fillBody.call(this, this.bodyContainer, this['opts']['fields']);
        setBodyListeners.call(this);
    };

    var getSelected = function() {
        return this.selectedIndex >= 0
            ? this.data[this.selectedIndex]
            : null;
    };

    var startResizing = function(container, event) {
        var grid = event.data.grid;
        kimchi.widget.Grid.beingResized = grid;
        if(!($('body').hasClass('resizing')
                && $(grid.resizer).hasClass('hidden'))) {
            return;
        }

        grid.columnBeingResized = container;
        var pageX = event.pageX;
        var gridOffsetX = grid.domNode.offset()['left'];
        var leftmostOffsetX = $(container).offset()['left'] - gridOffsetX;
        var left = pageX - gridOffsetX;
        var contentHeight = $('.grid-content', grid.domNode).height();
        $(grid.resizerLeftmost).css({
            left: leftmostOffsetX + 'px',
            height: contentHeight + 'px'
        });
        $(grid.resizer).css({
            left: left + 'px',
            height: contentHeight + 'px'
        });
        $(grid.resizerLeftmost).removeClass('hidden');
        $(grid.resizer).removeClass('hidden');
        event.preventDefault();
    };

    var endResizing = function(event) {
        var grid = kimchi.widget.Grid.beingResized;
        if(!$('body').hasClass('resizing')) {
            return;
        }
        $(grid.resizerLeftmost).addClass('hidden');
        $(grid.resizer).addClass('hidden');
        $('body').removeClass('resizing');
        var leftmostOffset = $(grid.columnBeingResized).offset()['left'];
        var left = event.pageX;
        if(leftmostOffset > left) {
            return;
        }
        resizeColumnWidth.call(
            grid,
            $(grid.columnBeingResized).index(),
            left - leftmostOffset
        );
        fixTableLayout.call(grid);
        grid.columnBeingResized = null;
        kimchi.widget.Grid.beingResized = null;
    };

    var resizeColumnWidth = function(index, width) {
        var width = Math.ceil(width);
        var widthArray = [];
        var totalWidth = 0;
        var header = this.headerContainer;
        var body = this.bodyContainer;
        if(this.containerBeingResized === CONTAINER_FROZEN) {
            header = this.frozenHeaderContainer;
            body = this.frozenBodyContainer;
        }
        $('col', header).each(function(i, colNode) {
            var w = index === i ? width : $(colNode).width();
            widthArray.push(w);
            totalWidth += w;
        });
        $.each([header, body], function(i, container) {
            container.css({
                'table-layout': 'fixed',
                width: totalWidth + 'px'
            });
            $('col:nth-child(' + (index + 1) + ')', container).css({
                width: width + 'px'
            });
        });

        if(this.containerBeingResized === CONTAINER_FROZEN) {
            var headerView = $('.grid-header-view', this.domNode);
            var bodyView = $('.grid-body-view', this.domNode);
            $.each([headerView, bodyView], function(i, view) {
                view.css({
                    left: totalWidth + 'px'
                });
            });
        }
    };

    var positionResizer = function(event) {
        var grid = event.data.grid;
        if($(grid.resizer).hasClass('hidden')) {
            return;
        }

        var pageX = event.pageX;
        var gridOffsetX = $(grid.domNode).offset()['left'];
        var leftMost = $(grid.resizerLeftmost).position()['left'];
        var offsetX = pageX - gridOffsetX;
        offsetX = offsetX >= leftMost ? offsetX : leftMost;
        $(grid.resizer).css('left', offsetX + 'px');
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

    var destroy = function() {
        $('body').off('mousemove.grid#' + this['opts']['id'], positionResizer);
        $('body').off('mouseup.grid#' + this['opts']['id'], endResizing);
    };

    var createDOM = function() {
        var containerID = this['opts']['container'];
        var container = $('#' + containerID);
        var gridID = this['opts']['id'];
        var rowSelection = this['opts']['rowSelection'] || 'single';
        var domNode = $(kimchi.substitute(htmlStr, {
            id: gridID,
            loading: i18n['KCHGRD6001M'],
            message: i18n['KCHGRD6002M'],
            buttonLabel: i18n['KCHGRD6003M'],
            detailedLabel: i18n['KCHGRD6004']
        })).appendTo(container);
        this.domNode = domNode;

        var height = domNode.height();
        var width = domNode.width();

        var title = this['opts']['title'];
        var titleNode = null;
        if(title) {
            titleNode = $('<div class="grid-caption">' + title + '</div>')
                .prependTo(domNode);
        }

        var toolbarButtons = this['opts']['toolbarButtons'];
        var toolbarNode = null;
        if(toolbarButtons) {
            toolbarNode = $('<div class="grid-toolbar"></div>');
            if(titleNode) {
                titleNode.after(toolbarNode);
            }
            else {
                toolbarNode.prependTo(domNode);
            }

            $.each(toolbarButtons, function(i, button) {
                var btnHTML = [
                    '<button',
                        button['id'] ? (' id="' + button['id'] + '"') : '',
                        ' class="grid-toolbar-button',
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

        var frozenHeaderContainer = $('.grid-frozen-header-container', domNode);
        var frozenBodyContainer = $('.grid-frozen-body-container', domNode);
        var frozenWidth = setupHeaders(
                frozenHeaderContainer,
                frozenBodyContainer,
                this['opts']['frozenFields']
        );
        this.frozenHeaderContainer = frozenHeaderContainer;
        this.frozenBodyContainer = frozenBodyContainer;

        var headerContainer = $('.grid-header-container', domNode);
        var bodyContainer = $('.grid-body-container', domNode);
        setupHeaders(headerContainer, bodyContainer, this['opts']['fields']);
        this.headerContainer = headerContainer;
        this.bodyContainer = bodyContainer;

        fixTableLayout.call(this, 'auto');

        var gridContentNode = $('.grid-content', domNode);
        var captionHeight = titleNode && $(titleNode).height() || 0;
        var toolbarHeight = toolbarNode && $(toolbarNode).height() || 0;
        gridContentNode.css('top', (captionHeight + toolbarHeight) + 'px');

        var maskNode = $('.grid-mask', domNode);
        maskNode.css('top', captionHeight + 'px');
        this.maskNode = maskNode;

        var messageNode = $('.grid-message', domNode);
        messageNode.css('top', captionHeight + 'px');
        this.messageNode = messageNode;

        var headerView = $('.grid-header-view', domNode);
        var bodyView = $('.grid-body-view', domNode);
        headerView.css('left', (frozenWidth) + 'px');
        bodyView.css('left', (frozenWidth) + 'px');

        var bodyWidth = width - frozenWidth;
        headerContainer.css('width', bodyWidth + 'px');
        bodyContainer.css('width', bodyWidth + 'px');

        fixTableLayout.call(this);

        var gridBody = $('.grid-body', domNode);
        this.gridBody = gridBody;
        this.resizerLeftmost = $('.grid-resizer-leftmost', domNode);
        this.resizer = $('.grid-resizer', domNode);
        var gridHeader = $('.grid-header', domNode);
        $('th', gridHeader).on('mouseover mousemove', {
            resizer: this.resizer
        }, initResizing);

        $('th', gridHeader).on('mouseout', {
            resizer: this.resizer
        }, clearResizing);

        this.containerBeingResized = CONTAINER_NORMAL;
        $('th', frozenHeaderContainer).on('mousedown', {
            grid: this
        }, function(event) {
                event.data.grid.containerBeingResized = CONTAINER_FROZEN;
                startResizing(this, event);
        });
        $('th', headerContainer).on('mousedown', {
            grid: this
        }, function(event) {
                event.data.grid.containerBeingResized = CONTAINER_NORMAL;
                startResizing(this, event);
        });

        $('body').on('mousemove.grid#' + this['opts']['id'], {
            grid: this
        }, positionResizer);
        $('body').on('mouseup.grid#' + this['opts']['id'], endResizing);

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
            frozenFields: null,
            fields: null
        },
        createDOM: createDOM,
        setData: setData,
        getSelected: getSelected,
        reload: reload,
        destroy: destroy,
        showMessage: showMessage
    };
})();
