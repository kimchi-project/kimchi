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
    $.widget('kimchi.selectMenu', {

        _create : function() {
            this.selectDiv = this.element;
            this.listControl = this.selectDiv.find('ul').first();
            this.listControl.html('');
            this.target = this.selectDiv.find('input').first();
            this.label = this.selectDiv.find('span').first();
            this.selectDiv.addClass('btn dropdown popable');
            this.target.addClass('input');
            this.listControl.addClass('select-list');
            this.listControl.parent().addClass('popover');
        },

        setData : function (options) {
            var that = this;
            var value = this.target.val();
            var selectedClass = 'active';
            var itemTag = 'li';
            var item;
            that.listControl.find('li').remove();
            that.label.text("");
            that.target.val("");
            if (options.length > 0) {
                $.each(options, function(index, option) {
                    item = $('<' + itemTag + '>' + option.label +'</' + itemTag + '>');
                    item.data('value', option.value);
                    if(option.value === value) {
                        item.addClass(selectedClass);
                        that.label.text(option.label);
                        that.target.val(option.value);
                    }
                    that.listControl.append(item);
                });
                that.listControl.on('click', itemTag, function() {
                    that.listControl.children().removeClass(selectedClass);
                    $(this).addClass(selectedClass);
                    that.label.text($(this).text());
                    var oldValue = that.target.val();
                    var newValue = $(this).data('value');
                    that.target.val(newValue);
                    if(oldValue !== newValue) {
                        that.target.change();
                    }
                });
            }
        },

        value : function(data) {
            if (data === undefined) {
                return this.target.val();
            }
            this.target.val(data.value);
            this.label.val(data.label);
        },

        destroy : function() {
            this.selectDiv.removeClass('btn dropdown popable');
            this.target.removeClass('input');
            this.label.removeClass('input');
            this.listControl.removeClass('select-list');
            this.listControl.parent().removeClass('popover');
            $.Widget.prototype.destroy.call(this);
        }
    });
}(jQuery));
