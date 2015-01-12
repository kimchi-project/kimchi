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
//     $(".selector").checkboxFlat({
//         id: "t",  //Checkbox base id.
//         name: "test",  //Checkbox name.
//         content: ["apple", "banana", "orange", "cherry"],  //Contents of the checkbox set.
//         checked: [1,3]  //Set the checked item, which starts with number 1.
//     });
//     $(".selector").click(function() {
//         console.log($(".selector").checkboxFlat("value"));  //Get value of the checked checkbox.
//     });

 (function($) {
    $.widget("kimchi.checkboxFlat", {
        options: {
            id: "",
            name: "",
            content: [],
            checked: []
        },

        _create: function() {
            var that = this;
            var idBase = that.options.id;
            var name = that.options.name;
            var checked = that.options.checked;
            var content = that.options.content;
            var html = "";
            for (var i=1;i<content.length+1;i++) {
                if($.inArray(i,checked) < 0) {
                    html += "<div class='checkbox-item checkbox-inline icon-check-empty-1' id='" + idBase + i + "' name='" + name + "'></div>" +
                            "<label class='checkbox-label checkbox-inline' for='" + idBase + i + "'>" + content[i-1] + "</label>";
                } else {
                    html += "<div class='checkbox-item checkbox-inline icon-ok-squared' id='" + idBase + i + "' name='" + name + "'></div>" +
                            "<label class='checkbox-label checkbox-inline' for='" + idBase + i + "'>" + content[i-1] + "</label>";
                }
            }
            $(html).appendTo(that.element);
            $(".checkbox-item").on("click", function() {
                var tickID = $(this).attr("id");
                var tick = tickID.substring(idBase.length,tickID.length);
                if($(this).hasClass("icon-check-empty-1")) {
                    $(this).removeClass("icon-check-empty-1");
                    $(this).addClass("icon-ok-squared");
                    checked.push(Number(tick));
                } else {
                    $(this).removeClass("icon-ok-squared");
                    $(this).addClass("icon-check-empty-1");
                    checked.splice($.inArray(Number(tick),checked),1);
                }
            });
        },

        value: function() {
            var value = new Array();
            var vContent = this.options.content;
            var vChencked = this.options.checked;
            for(var i=0;i<vChencked.length;i++) {
                value.push(vContent[vChencked[i]-1]);
            }
            return value;
        },

        _destroy: function() {
            this.element.remove();
        }
    });
 })(jQuery);