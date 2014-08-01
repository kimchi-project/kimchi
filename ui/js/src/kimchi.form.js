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

(function($) {
    $.fn.serializeObject = function() {
        var formDataArray = $(this).serializeArray();
        var formData = new Object();
        $.each(formDataArray, function(index, data) {
            formData.setDeepValue(data.name, data.value);
        });
        return formData;
    };
}(jQuery));

(function($) {
    $.fn.fillWithObject = function(obj) {
        $(this).find("input").each(function(){
            switch($(this).attr('type')) {
                case 'text':
                    $(this).val(obj.getDeepValue($(this).attr("name")));
                    break;
                case 'radio':
                case 'checkbox':
                    var a=String($(this).val());
                    var b=String(obj.getDeepValue($(this).attr("name")));
                    $(this).prop("checked",(a==b));
                    break;
                default:
                    break;
                }
            });
     };
}(jQuery));
