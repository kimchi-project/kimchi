/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwang@linux.vnet.ibm.com>
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
kimchi.main = function() {
    kimchi.popable();

    /**
     * Use Ajax to dynamically load a page without a page refreshing.
     * Handle arrow cursor animation, DOM node focus, and page content
     * rendering.
     */
    var loadPage = function(url) {
        /*
         * We setup an periodly reloading of VM list, which should be
         * removed when switching to non-guest pages.
         */
        kimchi.vmTimeout && clearTimeout(kimchi.vmTimeout);

        // Get the page content through Ajax and render it.
        $('#main').load(url);

        /*
         * We use the HTML file name for hash, like:
         * guests for guests.html, templates for templates.html.
         * Retrieve hash from the given URL and update URL hash
         * value to put an item in browsing history to make pages
         * be bookmark-able.
         */
        var hashString = url.substring(0, url.length - 5);
        location.hash = hashString;

        /*
         * Find the corresponding tab DOM node and animate the arrow
         * cursor to point to the tab.
         */
        var tab = $('#nav-menu a[href="' + url + '"]');
        var left = $(tab).parent().position().left;
        var width = $(tab).parent().width();
        $('.menu-arrow').stop().animate({
            left: left + width / 2 - 10
        });

        // Update the visual style of tabs; focus the selected one.
        $('#nav-menu a').removeClass('current');
        $(tab).addClass('current');
        $(tab).focus();
    };

    /*
     * Register click listener of tabs. Replace the default reloading
     * page behavior of <a> with Ajax loading.
     */
    $('#nav-menu a.item').on('click', function() {
        loadPage($(this).attr('href'));
        return false;
    });

    /*
     * If hash value is changed, then we know the user is intended to
     * load another page.
     */
    window.onhashchange = function() {
        var hashString = location.hash.substr(1);
        if(!hashString) {
            return;
        }

        var url = hashString + '.html';
        loadPage(url);
    };

    // Load i18n translation strings first and then render the page.
    $('#main').load('i18n.html', function() {
        /*
         * Initialize page content.
         * 1) If user types in the main page URL without hash, then we load
         *    VM list page by default, e.g., http://kimchi.company.com:8000;
         * 2) If user types a URL with hash, we load that page, e.g.,
         *    http://kimchi.company.com:8000/#template.
         */
        var hashString = (location.hash && location.hash.substr(1)) || 'guests';
        loadPage(hashString + '.html');
    });
};
