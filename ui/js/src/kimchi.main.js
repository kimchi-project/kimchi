/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2015
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
kimchi.tabMode = {};

kimchi.capabilities = undefined;
kimchi.getCapabilities(function(result) {
    kimchi.capabilities = result;

    if(kimchi.capabilities.federation=="on")
        $('#peers').removeClass('hide-content');
}, function() {
    kimchi.capabilities = {};
});

kimchi.main = function() {
    kimchi.isLoggingOut = false;
    kimchi.popable();

    var genTabs = function(tabs) {
        var tabsHtml = [];
        $(tabs).each(function(i, tab) {
            var title = tab['title'];
            var path = tab['path'];
            var mode = tab['mode'];
            if (mode != 'none') {
                var helpPath = kimchi.checkHelpFile(path);
                var disableHelp = (helpPath.length == 0 ? "disableHelp" : helpPath);
                tabsHtml.push(
                    '<li>',
                        '<a class="item ', disableHelp,'" href="', path, '">',
                            title,
                        '</a>',
                        '<input id="helpPathId" name="helpPath" value="' + helpPath + '" type="hidden"/>',
                    '</li>'
                );
            }
        });
        return tabsHtml.join('');
    };

    var parseTabs = function(xmlData) {
        var tabs = [];
        $(xmlData).find('tab').each(function() {
            var $tab = $(this);
            var titleKey = $tab.find('title').text();
            var title = i18n[titleKey] ? i18n[titleKey] : titleKey;
            var path = $tab.find('path').text();
            var roles = kimchi.cookie.get('roles');
            if (roles) {
                var role = JSON.parse(roles)[titleKey.toLowerCase()];
                var mode = $tab.find('[role="' + role + '"]').attr('mode');
                kimchi.tabMode[titleKey.toLowerCase()] = mode;
                tabs.push({
                    title: title,
                    path: path,
                    mode: mode
                });
            } else {
                document.location.href = 'login.html';
            }
        });

        return tabs;
    };

    var retrieveTabs = function(url) {
        var tabs;
        $.ajax({
            url : url,
            async : false,
            success : function(xmlData) {
                tabs = parseTabs(xmlData);
            }
        });
        return tabs;
    };

    var tabConfigUrl = 'config/ui/tabs.xml';
    var pluginConfigUrl = 'plugins/{plugin}/ui/config/tab-ext.xml';
    var pluginI18nUrl = 'plugins/{plugin}/i18n.json';
    var DEFAULT_HASH;
    var buildTabs = function(callback) {
        var tabs = retrieveTabs(tabConfigUrl);
        kimchi.listPlugins(function(plugins) {
            $(plugins).each(function(i, p) {
                var url = kimchi.substitute(pluginConfigUrl, {
                    plugin: p
                });
                var i18nUrl = kimchi.substitute(pluginI18nUrl, {
                    plugin: p
                });
                kimchi.getI18n(function(i18nObj){ $.extend(i18n, i18nObj)},
                               function(i18nObj){ //i18n is not define by plugin
                               }, i18nUrl, true);
                tabs.push.apply(tabs, retrieveTabs(url));
            });

            var defaultTab = tabs[1]

            var defaultTabPath = defaultTab && defaultTab['path']
            // Remove file extension from 'defaultTabPath'
            DEFAULT_HASH = defaultTabPath &&
                defaultTabPath.substring(0, defaultTabPath.lastIndexOf('.'))

            $('#nav-menu').append(genTabs(tabs));

            callback && callback();
        }, function(data) {
           kimchi.message.error(data.responseJSON.reason);
        }, true);
    };

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
        // Disable Help button according to selected tab
        if ($(tab).hasClass("disableHelp")) {
            $('#btn-help').css('cursor', "not-allowed");
            $('#btn-help').off("click");
        }
        else {
            $('#btn-help').css('cursor', "pointer");
            $('#btn-help').on("click", kimchi.openHelp);
        }
        // Load page content.
        loadPage(url);
    };

    /**
     * Use Ajax to dynamically load a page without a page refreshing. Handle
     * arrow cursor animation, DOM node focus, and page content rendering.
     */
    var loadPage = function(url) {
        // Get the page content through Ajax and render it.
        url && $('#main').load(url, function(responseText, textStatus, jqXHR) {
            if (jqXHR['status'] === 401 || jqXHR['status'] === 303) {
                var isSessionTimeout = jqXHR['responseText'].indexOf("sessionTimeout")!=-1;
                document.location.href= isSessionTimeout ? 'login.html?error=sessionTimeout' : 'login.html';
                return;
            }
        });
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
     * 5) About button click event
     * 6) Help button click event
     * 7) Peers button click event
     */
    var searchingPeers = false;
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
            // Remove file extension from 'href'
            location.hash = href.substring(0,href.lastIndexOf('.'))
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
                kimchi.isLoggingOut = true;
                document.location.href = "login.html";
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            });
        });

        // Set handler for about button
        $('#btn-about').on('click', function(event) {
            kimchi.window.open({"content": $('#about-tmpl').html()});
            event.preventDefault();
            });

        // Set handler for help button
        $('#btn-help').on('click', kimchi.openHelp);

        // Set handler to peers drop down
        $('#peers').on('click', function() {

            // Check if any request is in progress
            if ($('.popover', '#peers').is(':visible') || searchingPeers == true)
                return

            $('#search-peers').show();
            $('#no-peers').addClass('hide-content');
            $('a', '#peers').remove();

            searchingPeers = true;

            kimchi.getPeers(function(data){
                $('#search-peers').hide();
                if (data.length == 0)
                    $('#no-peers').removeClass('hide-content');

                for(var i=0; i<data.length; i++){
                    $('.dropdown', '#peers').append("<a href='"+data[i]+"' target='_blank'>"+data[i]+"</a>");
                }
                searchingPeers = false;
            });
        });
    };

    var initUI = function() {
        $(document).bind('ajaxError', function(event, jqXHR, ajaxSettings, errorThrown) {
            if (!ajaxSettings['kimchi']) {
                return;
            }

            if (jqXHR['status'] === 401) {
                var isSessionTimeout = jqXHR['responseText'].indexOf("sessionTimeout")!=-1;
                kimchi.user.showUser(false);
                kimchi.previousAjax = ajaxSettings;
                $(".empty-when-logged-off").empty();
                $(".remove-when-logged-off").remove();
                document.location.href= isSessionTimeout ? 'login.html?error=sessionTimeout' : 'login.html';
                return;
            }
            else if((jqXHR['status'] == 0) && ("error"==jqXHR.statusText) && !kimchi.isLoggingOut) {
                kimchi.message.error(i18n['KCHAPI6007E'].replace("%1", jqXHR.state()));
            }
            if(ajaxSettings['originalError']) {
                ajaxSettings['originalError'](jqXHR, jqXHR.statusText, errorThrown);
            }
        });

        kimchi.user.showUser(true);
        initListeners();
        updatePage();
    };

    // Load i18n translation strings first and then render the page.
    kimchi.getI18n(
        function(i18nStrings){ //success
            i18n = i18nStrings;
            buildTabs(initUI);
            },
        function(data){ //error
            kimchi.message.error(data.responseJSON.reason);
            });
};


kimchi.checkHelpFile = function(path) {
    var lang = kimchi.lang.get();
    var url = ""
    // Find help page path according to tab name
    if (/^tabs/.test(path))
        url = path.replace("tabs", "help/" + lang);
    else if (/^plugins/.test(path))
        url = path.slice(0, path.lastIndexOf('/')) + "help/" + lang + path.slice(path.lastIndexOf('/'));
    // Checking if help page exist.
    $.ajax({
        url: url,
        async: false,
        error: function() { url = ""; },
        success: function() { }
    });
    return url;
};


kimchi.openHelp = function(e) {
    var tab = $('#nav-menu a.current');
    var url = $(tab).parent().find("input[name='helpPath']").val();
    window.open(url, "Kimchi Help");
    e.preventDefault();
};
