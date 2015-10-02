/*
 * Project Wok
 *
 * Copyright IBM, Corp. 2015
 *
 * Code derived from Project Kimchi
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

/*
* Usage:
        $(selector).messagebarFlat({
            content: "Test",  //message you want to show in the messagebar
            color: "red",  //Three color supported: "red", "yellow" and "green",
            dismissTime: 3000  //when set to "never", the messagebar will never disappear.
                               // Or setting it to numbers for the dismiss time you want to delay.
        });
*/

(function($) {
    $.widget("wok.messagebarFlat", {
        options : {
            content : null,
            color : "red",
            dismissTime: 3000
        },

        _create: function() {
            var now = this._getTime();
            var that = this;
            $("<div class='messagebar'><span class='messageHead'></span>" +
                "<span class='messagebar-text'> " + this.options.content +":     " + now + "</span></div>")
                .addClass(this.options.color)
                .appendTo(that.element);
            $(".messageHead").addClass("dark-" + this.options.color);
            $("<span class='messagebar-close icon-cancel-circled'></span>").on("click", function() {
                that.destroy();
            }).appendTo($(".messagebar"));
            var dismissDelay = this.options.dismissTime;
            if (dismissDelay != "never") {
                setTimeout(function() {
                    that.destroy()
                }, dismissDelay);
            }
        },

        _getTime: function() {
            var CT = new Date();
            var currentDate = CT.getDate() + "/" + CT.getMonth()+1 + "/" +CT.getFullYear();
            var currentTime = CT.getHours() + ":" + CT.getMinutes() + ":" + CT.getSeconds();
            var now = currentDate + "       " + currentTime;
            return now;
        },

        destroy: function() {
            var that = this;
            that.element.fadeOut("normal", function() {
                that.element.remove();
            });
        }
    });
})(jQuery);
