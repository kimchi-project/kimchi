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

/*
 *  //How to use:
 *  $(".selector").radioFlat({
 *     id: "t",  //Base id of the radio set.
 *     name: "test",  //name of the radio.
 *     whichChecked: 2,  //First selected position, starts from 1.
 *     content: ["apple", "banana", "orange", "cherry"] //set the content array.
 *  });
 *
 *
 *  $(".test-bar").click(function() {
 *     console.log($(".test-bar").radioFlat("value"));  //this is how to get the value of selected radio value
 *  });
 *
 *
 *
 */

 (function($) {

    $.widget("wok.radioFlat", {
        options: {
            id: "",
            name: "",
            whichChecked: "",
            content:[],
        },

        _create: function() {
            var that = this;
            var radioName = this.options.name;
            var labelID = this.options.id;
            var checked = this.options.whichChecked;
            var num = Number(this.options.content.length);
            var html ="";
            if(num >0) {
                for(var i=1;i < num+1;i++) {
                    var tmpLabelID = labelID + i;
                    html += "<div class='icon-circle-empty inline-radio radio-label' id='" + tmpLabelID + "'></div>" +
                            "<label class='radio-content inline-radio' for='" + tmpLabelID + "'>" + that.options.content[i-1] + "</label>";
                }
                $(html).appendTo(that.element);
                $("#" + labelID + checked).attr("checked", "true");
                $("#" + labelID + checked).removeClass("icon-circle-empty");
                $("#" + labelID + checked).addClass("icon-dot-circled");
            }
            $(".radio-label").on("click", function() {
                $(".radio-label").removeClass("icon-dot-circled");
                $(".radio-label").addClass("icon-circle-empty");
                $(".radio-label").removeAttr("checked");
                $(this).removeClass("icon-circle-empty");
                $(this).addClass("icon-dot-circled");
                $(this).attr("checked", "true");
                var thisID = $(this).attr("id");
                that.options.whichChecked = thisID.substring(labelID.length,thisID.length);
            });
        },

        value: function() {
            var value = Number(this.options.whichChecked) -1;
            return this.options.content[value];
        },

        _destroy: function() {
            this.element.remove();
        }
    });
 })(jQuery);
