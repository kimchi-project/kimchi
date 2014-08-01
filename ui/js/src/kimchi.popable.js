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
kimchi.popable = function() {
    $(document).click(function(e) {
        $('.popable').each(function(i, n) {
            n === e.target || $.contains(n, e.target) ||
                $('.popover', n).toggle(false);
        });
     });
     $(document).on('click', '.popable', function(e) {
        var popup = $('.popover', this)[0];
        $(popup).toggle();

        // Scroll the popup menu into viewport if invisible.
        !$(popup).is(':visible') ||
            kimchi.isElementInViewport(popup) ||
            popup.scrollIntoView();
    });
};
