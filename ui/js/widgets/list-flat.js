/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2015
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
    //     $(".test-bar").listFlat({
    //         title: "Hello World"  //Set title.
    //     });
    //     $(".test-bar").listFlat("addItem", "Hello", "2015", "icon-user", "button1");
    //             //Add one item of the list, parameters are: name, info, icon and button-id


 (function($) {

    $.widget("kimchi.listFlat", {

        options: {
            title: null
        },

        _create: function() {
            var that = this;
            var listTitle = that.options.title;
            var titleTrim = listTitle.replace(/\s*/g, "");
            var html = "";
            html += "<div class='list-titlef'>" + listTitle + "</div>" +
                    "<div class='list-content' id='list" + titleTrim + "'></div>";
            $(html).appendTo(that.element);
        },

        _getTitle: function() {
            return this.options.title;
        },

        addItem: function(name, detail, icon, id) {
            var title = this._getTitle().replace(/\s/g, "");
            var usedIcon = icon || "";
            var html = "";
            html += "<div class='list-item'>" +
                        "<span class='list-inline list-item-icon " + usedIcon + "'></span>" +
                        "<span class='list-inline list-item-info'>"+
                            "<div class='list-item-name'>" + name + "</div>" +
                            "<div class='list-item-detail'>" + detail + "</div>" +
                        "</span>" +
                        "<span class='list-inline list-item-button' id='" + id + "'></span>" +
                    "</div>";
            $(html).appendTo($("#list" + title));
            $.each($(".list-item"), function(index, data) {
                if(index%2 >0) {
                    $(this).addClass("list-item-even");
                } else {
                    $(this).addClass("list-item-odd");
                }
            })
            console.log("title");
        },

        _destory: function() {
            this.element.remove();
        }
    });
 })(jQuery);