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
     //     $("#test-bar").menuFlat({
     //        content: [1,2,3,4,5,6], //Set content of the menu.
     //        icon: "icon-edit-alt",  //Set icon of the menu button.
     //        listIconList: ["icon-edit-alt","icon-edit-alt","icon-edit-alt","icon-edit-alt","icon-edit-alt","icon-user"]
     //                              //Set icons of the menu list.
     //                               // name is optional which set the name of the menu list.
     //    });
     //    $("#test-bar0").on("click", function() {
     //        alert("hello");
     //    });
     //    $("#test-bar1").on("click", function() {
     //        console.log("hello");
     //    });


 (function( $ ) {
    $.widget("wok.menuFlat", {

        options: {
            content: null,
            name: null,
            parentid: null,
            icon: null,
            listIconList: null
        },

        _create: function() {
            var that = this;
            var name = that.options.name || $(this.element).attr("id");
            var value = that.options.content;
            var icon = that.options.icon || "";
            var parentid = $(this.element).attr("id");
            $("#" + parentid).addClass("menu-content");
            that.options.parentid = parentid;
            var html = "<div class='menu-box' id='manu-" + name + "'>" +
                    "<span class='menu-icon-front " + icon + "'></span>" +
                    "<span class='menu-label'>"+ name + "</span>" +
                    "<span class='menu-icon icon-down-open'></span>" +
                    "</div>";
            $(html).appendTo(that.element);
            html = that._setValue(value);
            $(html).appendTo(that.element);
            $(".menu-box", "#" + parentid).on("click", that._toggleOpt);
            $(".menu-opt", "#" + parentid).on("click", that._toggleOpt);
            $(document).mouseup(function(e) {
                var container = $(".menu-opt");
                if(!container.is(e.target) && container.has(e.target).length === 0 && $(".menu-icon").hasClass("icon-up-open")) {
                    $(".menu-list", "#" + parentid).prop("style", "display:none");
                    $(".menu-icon", "#" + parentid).removeClass("icon-up-open");
                    $(".menu-icon", "#" + parentid).addClass("icon-down-open").css({
                        "background": "#4E4D4F"
                    });
                }
            });
        },

        _setValue: function(value) {
            var that = this;
            var name = that.options.name;
            var html = "<ul class='menu-list' name='" + name + "' style='display:none'>";
            var name = this.options.name || $(this.element).attr("id");
            $.each(value, function(index, data) {
                that.options.content[index] = data.toString();
                var liIcon = that.options.listIconList[index] || "";
                html += "<li id='" + name + index + "' class='menu-opt'>" +
                        "<span class='list-icon-front " + liIcon + "'></span>" +
                        "<span>" + data + "</span>" +
                        "</li>";
            });
            html += "</ul>"
            return html;
        },

        _toggleOpt: function() {
            var thisButton = $(this).parent().attr("id") || $(this).parent().parent().attr("id");
            if($(".menu-icon", "#" + thisButton).hasClass("icon-down-open")) {
                $(".menu-list", "#" + thisButton).prop("style", "display");
                $(".menu-icon", "#" + thisButton).removeClass("icon-down-open");
                $(".menu-icon", "#" + thisButton).addClass("icon-up-open").css({
                    "background": "#3A393B"
                });
            } else {
                $(".menu-list", "#" + thisButton).prop("style", "display:none");
                $(".menu-icon", "#" + thisButton).removeClass("icon-up-open");
                $(".menu-icon", "#" + thisButton).addClass("icon-down-open").css({
                    "background": "#4E4D4F"
                });
            }
        },

        _destroy: function() {
            this.element.remove();
        }
    });
 })(jQuery);
