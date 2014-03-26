/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
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
kimchi.widget.Grid = function(params) {
    var containerID = params['container'];
    var container = $('#' + containerID);
    var gridID = params['id'];
    var rowSelection = params['rowSelection'] || 'single';
    var rowListener = params['onRowSelected'];
    var htmlStr = [
      '<div id="', gridID, '" class="grid">',
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
                    i18n['KCHGRD6001M'],
                '</div>',
            '</div>',
        '</div>',
        '<div class="grid-message hidden">',
          '<div class="grid-message-text">',
            i18n['KCHGRD6002M'],
            '<button class="retry-button btn-small">',
              i18n['KCHGRD6003M'],
            '</button>',
          '</div>',
          '<div class="detailed-title">',
            i18n['KCHGRD6004M'],
          '</div>',
          '<div class="detailed-text"></div>',
        '</div>',
      '</div>'
    ];

    var gridNode = $(htmlStr.join(''))
        .appendTo(container);

    var height = gridNode.height();
    var width = gridNode.width();

    var title = params['title'];
    var titleNode = null;
    if(title) {
        titleNode = $('<div class="grid-caption">' + title + '</div>')
            .prependTo(gridNode);
    }

    var toolbarButtons = params['toolbarButtons'];
    var toolbarNode = null;
    if(toolbarButtons) {
        toolbarNode = $('<div class="grid-toolbar"></div>');
        if(titleNode) {
            titleNode.after(toolbarNode);
        }
        else {
            toolbarNode.prependTo(gridNode);
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
        $('col', header).each(function(index, col) {
            var width = $(col).width();
            totalWidth += width;
            $(col).css('width', width + 'px');
        });
        $('colgroup', header).clone().appendTo(body);
        return totalWidth;
    };

    var frozenHeaderContainer = $('.grid-frozen-header-container', gridNode);
    var frozenBodyContainer = $('.grid-frozen-body-container', gridNode);
    var frozenWidth = setupHeaders(
        frozenHeaderContainer,
        frozenBodyContainer,
        params['frozenFields']
    );

    var headerContainer = $('.grid-header-container', gridNode);
    var bodyContainer = $('.grid-body-container', gridNode);
    setupHeaders(headerContainer, bodyContainer, params['fields']);

    $.each([
        frozenHeaderContainer,
        headerContainer,
        frozenBodyContainer,
        bodyContainer
    ], function(i, tableNode) {
        $(tableNode).css('table-layout', 'auto');
    });

    var gridContentNode = $('.grid-content', gridNode);
    var captionHeight = titleNode && $(titleNode).height() || 0;
    var toolbarHeight = toolbarNode && $(toolbarNode).height() || 0;
    gridContentNode.css('top', (captionHeight + toolbarHeight) + 'px');

    var maskNode = $('.grid-mask', gridNode);
    maskNode.css('top', captionHeight + 'px');

    var messageNode = $('.grid-message', gridNode);
    messageNode.css('top', captionHeight + 'px');


    var getValue = function(name, obj) {
    var result=undefined;
    if(!Array.isArray(name)) {
        name=kimchi.form.parseFormName(name);
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

    var fillBody = function(container, fields, data) {
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

    var frozenHeaderView = $('.grid-frozen-header-view', gridNode);
    var headerView = $('.grid-header-view', gridNode);
    var bodyView = $('.grid-body-view', gridNode);
    headerView.css('left', (frozenWidth) + 'px');
    bodyView.css('left', (frozenWidth) + 'px');

    var bodyWidth = width - frozenWidth;
    headerContainer.css('width', bodyWidth + 'px');
    bodyContainer.css('width', bodyWidth + 'px');

    var fixTableLayout = function() {
        $.each([
            frozenHeaderContainer,
            headerContainer,
            frozenBodyContainer,
            bodyContainer
        ], function(i, tableNode) {
            $(tableNode).css('table-layout', 'fixed');
        });
    };
    fixTableLayout();

    var gridHeader = $('.grid-header', gridNode);
    $('th', gridHeader).on('mouseover mousemove', function(event) {
        var pageX = event.pageX;
        var tailPos = $(this).width() + $(this).offset()['left'];
        var atResizer = Math.abs(pageX - tailPos) <= 2;
        var isResizing = !resizer.hasClass('hidden');
        $('body')[(atResizer || isResizing)
            ? 'addClass'
            : 'removeClass'
        ]('resizing');
    });

    $('th', gridHeader).on('mouseout', function(event) {
        resizer.hasClass('hidden') &&
            $('body').removeClass('resizing');
    });

    var gridBody = $('.grid-body', gridNode);
    var contentHeight = gridContentNode.height();
    var resizerLeftmost = $('.grid-resizer-leftmost', gridNode);
    var resizer = $('.grid-resizer', gridNode);
    resizerLeftmost.css('height', contentHeight + 'px');
    resizer.css('height', contentHeight + 'px');

    var stylingRow = function(row, className, add) {
        var index = $(row).index() + 1;
        $('tr', frozenBodyContainer)
            .removeClass(className);
        $('tr', bodyContainer)
            .removeClass(className);

        if(add === false) {
            return;
        }

        $('tr:nth-child(' + index + ')', frozenBodyContainer)
            .addClass(className);
        $('tr:nth-child(' + index + ')', bodyContainer)
            .addClass(className);
    };

    var selectedIndex = -1;
    var setBodyListeners = function() {
        if(rowSelection != 'disabled') {
            $('tr', gridBody).on('mouseover', function(event) {
                stylingRow(this, 'hover');
            });

            $('tr', gridBody).on('mouseout', function(event) {
                stylingRow(this, 'hover', false);
            });

            $('tr', gridBody).on('click', function(event) {
                selectedIndex = $(this).index();
                stylingRow(this, 'selected');
                rowListener && rowListener();
            });
        }

        $('.grid-body-view', gridNode).on('scroll', function(event) {
            $('.grid-header .grid-header-view', gridNode)
                .prop('scrollLeft', this.scrollLeft);
            $('.grid-body .grid-frozen-body-view', gridNode)
                .prop('scrollTop', this.scrollTop);
        });
    };

    this.frozenFields = params['frozenFields'];
    this.fields = params['fields'];
    this.setData = function(data) {
        this.data = data;
        fillBody(frozenBodyContainer, this.frozenFields, data);
        fillBody(bodyContainer, this.fields, data);
        setBodyListeners();
    };

    this.getSelected = function() {
        return selectedIndex >= 0
            ? this.data[selectedIndex]
            : null;
    };

    var columnBeingResized = null;
    var CONTAINER_NORMAL = 0, CONTAINER_FROZEN = 1;
    var containerBeingResized = CONTAINER_NORMAL;
    var startResizing = function(container, event) {
        if(!($('body').hasClass('resizing') && resizer.hasClass('hidden'))) {
            return;
        }

        columnBeingResized = container;
        var pageX = event.pageX;
        var gridOffsetX = gridNode.offset()['left'];
        var leftmostOffsetX = $(container).offset()['left'] - gridOffsetX;
        var left = pageX - gridOffsetX;
        resizerLeftmost.css('left', leftmostOffsetX + 'px');
        resizer.css('left', left + 'px');
        resizerLeftmost.removeClass('hidden');
        resizer.removeClass('hidden');
        event.preventDefault();
    };

    var endResizing = function(event) {
        if(!$('body').hasClass('resizing')) {
            return;
        }
        resizerLeftmost.addClass('hidden');
        resizer.addClass('hidden');
        $('body').removeClass('resizing');
        var leftmostOffset = $(columnBeingResized).offset()['left'];
        var left = event.pageX;
        if(leftmostOffset > left) {
            return;
        }

        resizeColumnWidth(
            $(columnBeingResized).index(),
            left - leftmostOffset
        );
        fixTableLayout();
        columnBeingResized = null;
    };

    var resizeColumnWidth = function(index, width) {
        var width = Math.ceil(width);
        var widthArray = [];
        var totalWidth = 0;
        var header = headerContainer;
        var body = bodyContainer;
        if(containerBeingResized === CONTAINER_FROZEN) {
            header = frozenHeaderContainer;
            body = frozenBodyContainer;
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

        if(containerBeingResized === CONTAINER_FROZEN) {
            $.each([headerView, bodyView], function(i, view) {
                view.css({
                    left: totalWidth + 'px'
                });
            });
        }
    };

    $('th', frozenHeaderContainer).on('mousedown', function(event) {
        containerBeingResized = CONTAINER_FROZEN;
        startResizing(this, event);
    });
    $('th', headerContainer).on('mousedown', function(event) {
        containerBeingResized = CONTAINER_NORMAL;
        startResizing(this, event);
    });

    var positionResizer = function(event) {
        if(resizer.hasClass('hidden')) {
            return;
        }

        var pageX = event.pageX;
        var gridOffsetX = gridNode.offset()['left'];
        var leftMost = resizerLeftmost.position()['left'];
        var offsetX = pageX - gridOffsetX;
        offsetX = offsetX >= leftMost ? offsetX : leftMost;
        resizer.css('left', offsetX + 'px');
    };

    $('body').on('mousemove', positionResizer);
    $('body').on('mouseup', endResizing);

    this.showMessage = function(msg) {
        $('.detailed-text', messageNode).text(msg);
        $(messageNode).removeClass('hidden');
    };

    this.hideMessage = function() {
        $(messageNode).addClass('hidden');
    };

    this.destroy = function() {
        $('body').off('mousemove', positionResizer);
        $('body').off('mouseup', endResizing);
    };

    var data = params['data'];
    var self = this;
    var reload = function() {
        if(!data) {
            return;
        }

        $(messageNode).addClass('hidden');

        if($.isArray(data)) {
            self.setData(data);
            return;
        }

        if($.isFunction(data)) {
            var loadData = data;
            maskNode.removeClass('hidden');
            loadData(function(data) {
                self.setData(data);
                maskNode.addClass('hidden');
            });
        }
    };

    var reloadButton = $('.retry-button', gridNode);
    $(reloadButton).on('click', function(event) {
        reload();
    });

    this.reload = reload;
    reload();
};
