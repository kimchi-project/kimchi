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

kimchi.select = function(id, options) {
    var listControl = $('#'+ id);
    var targetId = listControl.data('target');
    var labelId = listControl.data('label');
    var value = $('#' + targetId).val();
    var item;
    var itemTag = 'li';
    var selectedClass = 'active';
    $.each(options, function(index, option) {
        item = $('<' + itemTag + '></' + itemTag + '>');
        item.text(option.label);
        item.data('value', option.value);
        if(option.value === value) {
            item.addClass(selectedClass);
            $('#' + labelId).text(option.label);
        }
        listControl.append(item);
    });

    listControl.on('click', itemTag, function() {
        listControl.children().removeClass(selectedClass);
        $(this).addClass(selectedClass);
        $('#' + labelId).text($(this).text());
        var target = $('#' + targetId);
        var oldValue = target.val();
        var newValue = $(this).data('value');
        target.val(newValue);
        if(oldValue !== newValue) {
            target.change();
        }
    });
};
