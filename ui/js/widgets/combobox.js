/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function($) {
    $.widget('kimchi.combobox', {
        _create : function() {
            this.selectDiv = this.element;
            this.listControl = this.selectDiv.find('ul').first();
            this.listControl.html('');
            this.target = this.selectDiv.find('input').first();
            this.selectDiv.addClass('btn-select dropdown popable');
            this.target.addClass('input');
            this.target.width(this.selectDiv.width()+10);
            this.listControl.addClass('select-list');
            this.listControl.parent().addClass('popover');
        },

        setData : function(options) {
            var that = this;
            var value = this.target.val();
            var selectedClass = 'active';
            var itemTag = 'li';
            if (options.length > 0) {
                that.target.after($('<span class="arrow"></span>'));
                that.listControl.on('click', itemTag, function(e) {
                    that.listControl.children().removeClass(selectedClass);
                    $(this).addClass(selectedClass);
                    var oldValue = that.target.val();
                    var newValue = $(this).data('value');
                    that.target.val(newValue);
                    if (oldValue !== newValue) {
                        that.target.change();
                    }
                });

                that.selectDiv.click(function(e) {
                    that.listControl.html('');
                    var items = that._dataList(options);
                    $.each(items, function(index, item) {
                        that.listControl.append(item);
                    })
                });

                that.target.keyup(function(event) {
                    that.listControl.html('');
                    var items = that._dataList(options);
                    var temp = 0;
                    $.each(items, function(index, item) {
                        if (item.text().indexOf(that.target.val()) == 0) {
                            that.listControl.append(item);
                            temp++;
                        }
                    });
                    if (temp > 0 && that.listControl.html() !== '') {
                        that._open();
                    } else {
                        that._close();
                    }
                });
            }
        },

        value : function(value) {
            if (value === undefined) {
                return this.target.val();
            }
            this.target.val(value);
        },

        _dataList : function(options) {
            var item;
            var itemTag = 'li';
            var selectedClass = 'active';
            var items = [];
            var that = this;
            $.each(options, function(index, option) {
                item = $('<' + itemTag + '>' + option.label +'</' + itemTag + '>');
                item.data('value', option.value);
                if (option.value === that.target.val()) {
                    item.addClass(selectedClass);
                }
                items.push(item);
            });
            return items;
        },

        clear : function() {
            this.target.val("");
        },

        _open : function() {
            var isOpen = this.selectDiv.hasClass('open');
            if (!isOpen) {
                this.selectDiv.addClass('open');
            }
        },

        _close : function() {
            var isOpen = this.selectDiv.hasClass('open');
            if (isOpen) {
                this.selectDiv.removeClass('open');
            }
        },

        destroy : function() {
            this.selectDiv.removeClass('btn-select dropdown popable');
            this.target.removeClass('input');
            this.listControl.removeClass('select-list');
            this.listControl.parent().removeClass('popover');
            $.Widget.prototype.destroy.call(this);
        }
    });
}(jQuery));
