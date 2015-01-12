/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2015
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

$(function(){
$.widget("kimchi.grid", {
    options: {
        enableSorting: true
    },
    _create: function() {
        var that = this;
        this.element.addClass('grid');
        var head = $(this.element.children().get(0));
        var body = $(this.element.children().get(1));
        head.addClass('header c1 bold grey');
        if(this.options.enableSorting){
            head.children().each(function(){
                var addSorting = "<span>"+$(this).html()+"</span>";
                addSorting += "<span><div class='icon-angle-up sort-up'></div><div class='icon-angle-down sort-down'></div></span>";
                $(this).empty().append(addSorting);
            });
        }
        $('.icon-angle-up', head).click(function(){
            that.sort(head.children().index($(this).parent().parent()), true);
        });
        $('.icon-angle-down', head).click(function(){
            that.sort(head.children().index($(this).parent().parent()), false);
        });
        body.addClass('body c1 normal dark-grey');
        body.children().addClass('row');
        this._setRowBackgroud();
    },
    _setRowBackgroud: function(){
        var i=0, classes=['odd', 'even'];
        $(this.element.children().get(1)).children().each(function(){
            $(this).removeClass('odd');
            $(this).removeClass('even');
            $(this).addClass(classes[i]);
            i = i==0?1:0;
        });
    },
    sort: function(column, assending) {
        var head = $(this.element.children().get(0));
        $('.icon-up-dir', head).removeClass('icon-up-dir').addClass('icon-angle-up');
        $('.icon-down-dir', head).removeClass('icon-down-dir').addClass('icon-angle-down');
        var columnCell = $(head.children().get(column));
        if(assending){
            $('.icon-angle-up', columnCell).removeClass('icon-angle-up').addClass('icon-up-dir');
        }else{
            $('.icon-angle-down', columnCell).removeClass('icon-angle-down').addClass('icon-down-dir');
        }
        var container = $(this.element.children().get(1));
        var nodes = [];
        container.children().each(function(){
            nodes.push($(this));
        });
        nodes.sort(function(a, b){
            aVal = $(a.children().get(column)).attr('val');
            bVal = $(b.children().get(column)).attr('val');
            return aVal.localeCompare(bVal);
        });
        if(!assending) nodes.reverse();
        container.empty();
        for(var i=0;i<nodes.length;i++){
            container.append(nodes[i]);
        }
        this._setRowBackgroud();
    },
    filter: function(keyword) {
        keyword = keyword.toLowerCase();
        var container = $(this.element.children().get(1));
        container.children().each(function(){
            var hide = true;
            $(this).children().each(function(){
                if($(this).attr('val')&&$(this).attr('val').toLowerCase().indexOf(keyword)!=-1){
                    hide = false;
                    return false;
                }
            });
            $(this).css('display', hide?'none':'');
        });
        this._setRowBackgroud();
    },
    addRow: function(rowNode){
        $(rowNode).addClass('row');
        this._setRowBackgroud();
    },
    deleteRow: function(rowNode){
        $(rowNode).remove();
        this._setRowBackgroud();
    },
    _destroy: function() {
        this.element.removeClass('grid');
        var head = $(this.element.children().get(0));
        var body = $(this.element.children().get(1));
        head.removeClass('header c1 bold grey');
        if(this.options.enableSorting){
            head.children().each(function(){
                var oriContent = $($(this).children().get(0)).html()
                $(this).empty().append(oriContent);
            });
        }
        body.removeClass('body c1 normal dark-grey');
        body.children().removeClass('row odd even');
    }
});
});
