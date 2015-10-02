/*
 * Project Wok
 *
 * Copyright IBM, Corp. 2015
 *
 * Code derived from Project Kimchi
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


// How to use:
//     $(".selector").selectmenuFlat({
//         content: [1,2,3,4,5,6],  //Set content of the select menu
//         selected: 2  // set the selected option, starts from "1"
//     });
//     $(".selector").selectmenuFlat("value", "4"); //Set value.
//     var t = $(".selector").selectmenuFlat("value");  //Get value
//     console.log(t);


 (function( $ ) {
    $.widget("wok.selectmenuFlat", {

        options: {
            content: null,
            name: null,
            selected: null,
            parentid: null
        },

        _create: function() {
            var that = this;
            var name = that.options.name || $(this.element).attr("id");
            var value = that.options.content;
            var parentid = $(this.element).attr("id");
            that.options.parentid = parentid;
            var html = "<div class='selected-box'>" +
                    "<input class='select-val'>" +
                    "<span class='select-label'></span>" +
                    "<span class='select-icon icon-down-open'></span>" +
                    "</div>";
            $(html).appendTo(that.element);
            html = that._setValue(value);
            $(html).appendTo(that.element);
            $("#" + parentid).addClass("select-content");
            var sel = that.options.selected || 1;
            sel = that.options.content[Number(sel) -1];
            that.options.selected = $.inArray(sel, that.options.content) + 1;
            $(".select-val", "#" + parentid).text(sel);
            $(".select-label", "#" + parentid).text(sel);
            $(".selected-box", "#" + parentid).on("click", this._toggleOpt);
            $(".selectmenu-opt", "#" + parentid).on("click", function() {
                var selectedText = $(this).text();
                that.options.selected = $.inArray(selectedText, that.options.content) +1;
                $(".selected-box .select-label", "#" + parentid).text(selectedText);
                $(".select-val", "#" + parentid).text(selectedText);
                $(".selectmenu-list", "#" + parentid).prop("style", "display:none");
                $(".select-icon", "#" + parentid).removeClass("icon-up-open");
                $(".select-icon", "#" + parentid).addClass("icon-down-open").css({
                    "border-left": "none"
                });
            });
            $(document).mouseup(function(e) {
                var container = $(".selectmenu-opt");
                if(!container.is(e.target) && container.has(e.target).length === 0 && $(".select-icon").hasClass("icon-up-open")) {
                    $(".selectmenu-list", "#" + parentid).prop("style", "display:none");
                    $(".select-icon", "#" + parentid).removeClass("icon-up-open");
                    $(".select-icon", "#" + parentid).addClass("icon-down-open").css({
                        "border-left": "none"
                    });
                }
            });
        },

        _setValue: function(value) {
            var that = this;
            var html = "<ul class='selectmenu-list' style='display:none'>";
            var name = this.options.name || $(this.element).attr("id");
            $.each(value, function(index, data) {
                that.options.content[index] = data.toString();
                html += "<li id='" + name + index + "' class='selectmenu-opt'>" + data + "</li>";
            });
            html += "</ul>";
            return html;
        },

        _toggleOpt: function() {
            var thisButton = $(this).parent().attr("id");
            if($(".select-icon", "#" + thisButton).hasClass("icon-down-open")) {
                $(".selectmenu-list", "#" + thisButton).prop("style", "display");
                $(".select-icon", "#" + thisButton).removeClass("icon-down-open");
                $(".select-icon", "#" + thisButton).addClass("icon-up-open").css({
                    "border-left": "1px solid #d8d8d8"
                });
            } else {
                $(".selectmenu-list", "#" + thisButton).prop("style", "display:none");
                $(".select-icon", "#" + thisButton).removeClass("icon-up-open");
                $(".select-icon", "#" + thisButton).addClass("icon-down-open").css({
                    "border-left": "none"
                });
            }
        },

        value: function(value) {
            var parentid = this.options.parentid;
            if(!value) {
                return $(".selected-box .select-val", "#" + parentid).text();
            }
            if (value <= this.options.content.length) {
                this.options.selected = value;
                var selectedText = this.options.content[value-1];
                $(".selected-box .select-label", "#" + parentid).text(selectedText);
                $(".selected-box .select-val", "#" + parentid).text(selectedText);
            }
        },

        _destroy: function() {
            this.element.remove();
        }
    });
 })(jQuery);
