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
 *      $(".selector").dialogFlat({
 *          title: "Demo",  //Title of the dialog.
 *          confirmText: "Ok",  //Text of the confirm button, "Ok" is the default value.
 *          cancelText: "Cancel",  //Text of the cancel button.
 *          width: "300",  //Width of the dialog, "px" is the default unit.
 *          height: "500",  //Height of the dialog, "px" is the default unit.
 *          confirmFunc: function() {
 *              //Function after confirm
 *          }
 *      });
 */

(function( $ ) {
    $.widget("kimchi.dialogFlat", {
        options: {
            title: "",
            autoOpen: true,
            confirmText: "Ok",
            cancelText: "Cancel",
            confirmFunc: null,
            height: "150",
            width: "150"
        },

        _create: function() {
            var that = this;
            var w = that.options.width;
            var h = that.options.height;
            $(".body").addClass("style:'opacity:0.5'");
            that._open();
            that._setSize(w, h);
            $(".dialog-container .dialog-cancel").on("click", that._destroy);
            $(".dialog-container .dialog-okay").on("click", function() {
                that._trigger("confirmFunc");
                that._destroy();
            });
        },

        _open: function() {
            var cfmTxt = this.options.confirmText;
            var celTxt = this.options.cancelText;
            var titleTxt = this.options.title;
            var html =
            "<div id='dialog-overlay'></div>" +
            "<div class='dialog-border-grey'>" +
                "<div class='dialog-container'>" +
                    "<div class='dialog-title h1 dark-gray'>" + titleTxt + "</div>" +
                    "<div class='dialog-body'>dafafdafdas</div>" +
                    "<div class='dialog-footer'>" +
                        "<div class='dialog-button dialog-okay'>" + cfmTxt + "</div>" +
                        "<div class='dialog-button dialog-cancel'>" + celTxt + "</div>" +
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
                $("#dialog-overlay").css({
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

        _setSize: function(width, height) {
            var wid = width + "px";
            var hei = height + "px";
            var cHeight = (height - 4) + "px";
            var bHeight = (height - 54) + "px";
            var tWidth = (width - 25) + "px";
            $(".dialog-border-grey").css({
                "width": wid,
                "height": hei
            });
            $(".dialog-container").css({
                "height": cHeight
            });
            $(".dialog-container .dialog-body").css({
                "height": bHeight
            });
            $(".dialog-container .dialog-title").css({
                "width": tWidth
            });
        },

        _destroy: function() {
            $(".dialog-border-grey").remove();
            $("#dialog-overlay").remove();
        }
    });
})(jQuery);