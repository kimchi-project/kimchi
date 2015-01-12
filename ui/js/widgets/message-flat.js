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

/* How to use:
*      $(".selector").messageFlat({
*          contentMain: "This is a test",  //Content you are going to add
*          contentConfirm: "Sure?"  //Content that inform user whether they want to continue.
*                                  //Default value is: "Are you sure you want to go on?"
*          confirm: function() {
*              //Function after confirm
*          }
*      });
*/

(function( $ ) {
    $.widget("kimchi.messageFlat", {
        options: {
            autoOpen: true,
            contentMain: null,
            contentConfirm: "Are you sure you want to go on?",
            confirm: null
        },

        _create: function() {
            var that = this;
            var msg = that.options.contentMain;
            var cfm = that.options.contentConfirm;
            $(".body").addClass("style:'opacity:0.5'");
            that._open();
            $(".message-type-icon").addClass("icon-help-circled-1");
            $(".message-dialog .message-content .message-main").text(msg);
            $(".message-dialog .message-confirm-info").text(cfm);
            $(".message-dialog .message-cancel").on("click", that.destroy);
            $(".message-dialog .message-okay").on("click", function() {
                that._trigger("confirm");
                that.destroy();
            });
        },

        _open: function() {
            var html =
            "<div id='overlay'></div>" +
            "<div class='border-grey'>" +
                "<div class='message-dialog'>" +
                    "<div class='message-content'>" +
                        "<div class='message-inline message-type-icon'></div>" +
                        "<div class='message-inline message-main'></div>" +
                    "</div>" +
                    "<div class='message-confirm-info'></div>" +
                    "<div class='message-footer'>" +
                        "<div class='message-button message-okay'>Ok</div>" +
                        "<div class='message-button message-cancel'>Cancel</div>" +
                    "</div>" +
                "</div>" +
            "</div>";
            if (this.options.autoOpen) {
                $(html).appendTo($("body"));
                var pageWidth = window.screen.width;
                var pageHeight = window.screen.height;
                var pageLeft = document.screenLeft
                var pageTop = document.screenTop;
                var topOffset = "-" + pageHeight + "px";
                console.log(topOffset);
                $("#overlay").css({
                    "opacity": "0.5",
                    "Left": pageLeft,
                    "Top": pageTop,
                    "background-color": "white",
                    "width": pageWidth,
                    "height": pageHeight,
                    "margin-top": topOffset,
                    "overflow": "hidden"
                });
            }
        },

        destroy: function() {
            $(".border-grey").remove();
            $("#overlay").remove();
        }
    });
})(jQuery);