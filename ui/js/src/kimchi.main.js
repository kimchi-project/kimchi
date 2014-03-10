/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
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
    var tabUrl = "/config/ui/tabs.xml";
    var DEFAULT_HASH = kimchi.getDefaultPage(tabUrl);
    kimchi.popable();

    var onLanguageChanged = function(lang) {
        kimchi.lang.set(lang);
        location.reload();
    };

    /**
     * Do the following setup:
     *   1) Clear any timing events.
     *   2) If the given URL is invalid (i.e., no corresponding href value in
     *      page tab list.), then clear location.href and inform the user;
     *
     *      Or else:
     *      Move the page tab indicator to the right position;
     *      Load the page content via Ajax.
     */
    var onKimchiRedirect = function(url) {
        /*
         * Find the corresponding tab node and animate the arrow indicator to
         * point to the tab. If nothing found, inform user the URL is invalid
         * and clear location.hash to jump to home page.
         */
        var tab = $('#nav-menu a[href="' + url + '"]');
        if (tab.length === 0) {
            kimchi.message.error.code('KCHAPI6001E');
            location.hash = '';
            return;
        }

        // Animate arrow indicator.
        var left = $(tab).parent().position().left;
        var width = $(tab).parent().width();
        $('.menu-arrow').stop().animate({
            left : left + width / 2 - 10
        });

        // Update the visual style of tabs; focus the selected one.
        $('#nav-menu a').removeClass('current');
        $(tab).addClass('current');
        $(tab).focus();

        // Load page content.
        loadPage(url);
    };

    /**
     * Use Ajax to dynamically load a page without a page refreshing. Handle
     * arrow cursor animation, DOM node focus, and page content rendering.
     */
    var loadPage = function(url) {
        // Get the page content through Ajax and render it.
        url && $('#main').load(url, function(responseText, textStatus, jqXHR) {});
    };

    /*
     * Update page content.
     * 1) If user types in the main page URL without hash, then we apply the
     *    default hash. e.g., http://kimchi.company.com:8000;
     * 2) If user types a URL with hash, then we publish an "redirect" event
     *    to load the page, e.g., http://kimchi.company.com:8000/#templates.
     */
    var updatePage = function() {
        // Parse hash string.
        var hashString = (location.hash && location.hash.substr(1));
        /*
         * If hash string is empty, then apply the default one;
         * or else, publish an "redirect" event to load the page.
         */
        if (!hashString) {
            location.hash = DEFAULT_HASH;
        }
        else {
            kimchi.topic('redirect').publish(hashString + '.html');
        }
    };

    /**
     * Register listeners including:
     * 1) Kimchi redirect event
     * 2) hashchange event
     * 3) Tab list click event
     * 4) Log-out button click event
     */
    var initListeners = function() {
        kimchi.topic('languageChanged').subscribe(onLanguageChanged);
        kimchi.topic('redirect').subscribe(onKimchiRedirect);

        /*
         * If hash value is changed, then we know the user is intended to load
         * another page.
         */
        window.onhashchange = updatePage;

        /*
         * Register click listener of tabs. Replace the default reloading page
         * behavior of <a> with Ajax loading.
         */
        $('#nav-menu').on('click', 'a.item', function(event) {
            var href = $(this).attr('href');
            location.hash = href.substring(0,href.length -5);
            /*
             * We use the HTML file name for hash, like: guests for guests.html
             * and templates for templates.html.
             *     Retrieve hash value from the given URL and update location's
             * hash part. It has 2 effects: one is to publish Kimchi "redirect"
             * event to trigger listener, the other is to put an entry into the
             * browser's address history to make pages be bookmark-able.
             */
            // Prevent <a> causing browser redirecting to other page.
            event.preventDefault();
        });

        // Perform logging out via Ajax request.


        $('#btn-logout').on('click', function() {
            kimchi.logout(function() {
                updatePage();
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            });
        });

        $('#btn-help').on('click', kimchi.getHelp);
    };

    // Load i18n translation strings first and then render the page.
    $('#main').load('i18n.html', function() {
        kimchi.addTabs(tabUrl);
        $(document).bind('ajaxError', function(event, jqXHR, ajaxSettings, errorThrown) {
            if (!ajaxSettings['kimchi']) {
                return;
            }

            if (jqXHR['status'] === 401) {
                kimchi.user.showUser(false);
                kimchi.previousAjax = ajaxSettings;
                $(".empty-when-logged-off").empty();
                $(".remove-when-logged-off").remove();
                kimchi.window.open({
                    url: 'login-window.html',
                    id: 'login-window-wrapper'
                });
                return;
            }

            ajaxSettings['originalError'] && ajaxSettings['originalError'](jqXHR);
        });

        kimchi.user.showUser(true);
        initListeners();
        updatePage();
    });
};

kimchi.addTabs = function(url) {
    var tabsHtml = kimchi.getTabHtml(url);
    $('#nav-menu').prepend(tabsHtml);
    kimchi.addExtTabs();
};

kimchi.addExtTabs = function() {
    kimchi.listPlugins(function(results) {
        for ( var i = 0; i < results.length; i++) {
            var tabsHtml = kimchi.getTabHtml("/plugins/" + results[i] + "/ui/config/tab-ext.xml");
            $('#nav-menu').append(tabsHtml);
        }
    });
};

kimchi.getDefaultPage = function(url) {
    var defautLocation = "";
    $.ajax({
        url : url,
        async : false,
        success : function(xmlData) {
            var tab = $(xmlData).find('tab').first();
            var path = tab.find('path').text();
            if (path) {
                defautLocation = path.substring(0, path.length - 5);
            }
        }
    });
    return defautLocation;
};

kimchi.getTabHtml = function(url) {
    var tabsHtml = "";
    $.ajax({
        url : url,
        async : false,
        success : function(xmlData) {
            $(xmlData).find('tab').each(function() {
                var $tab = $(this);
                var titleKey = $tab.find('title').text();
                var title = i18n[titleKey];
                var path = $tab.find('path').text();
                tabsHtml += "<li><a class='item' href=" + path + ">" + title + "</a></li>";
            });
        }
    });
    return tabsHtml;
};

kimchi.getHelp = function(e) {
        var url=window.location.hash;
        url = url.replace("#tabs","/help");
        if (url == "/help")
            url=url+"/index.html"
        else
            url=url+".html";

        window.open(url, "Kimchi Help");
        e.preventDefault();
};
