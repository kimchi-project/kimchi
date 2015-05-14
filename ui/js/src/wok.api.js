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
var wok = {

    widget: {},

    /**
     * A wrapper of jQuery.ajax function to allow custom bindings.
     *
     * @param settings an extended object to jQuery Ajax settings object
     *   with some extra properties (see below)
     *
     *   resend: if the XHR has failed due to 401, the XHR can be resent
     *     after user being authenticated successfully by setting resend
     *     to true: settings = {resend: true}. It's useful for switching
     *     pages (Guests, Templates, etc.).
     *       e.g., the user wants to list guests by clicking Guests tab,
     *     but he is told not authorized and a login window will pop up.
     *     After login, the Ajax request for /vms will be resent without
     *     user clicking the tab again.
     *       Default to false.
     */
    requestJSON : function(settings) {
        settings['originalError'] = settings['error'];
        settings['error'] = null;
        settings['wok'] = true;
        return $.ajax(settings);
    },

    /**
     * Get the i18 strings.
     */
    getI18n: function(suc, err, url, sync) {
        wok.requestJSON({
            url : url ? url : 'i18n.json',
            type : 'GET',
            resend: true,
            dataType : 'json',
            async : !sync,
            success : suc,
            error: err
        });
    },

    login : function(settings, suc, err) {
        $.ajax({
            url : "login",
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json"
        }).done(suc).fail(err);
    },

    logout : function(suc, err) {
        wok.requestJSON({
            url : 'logout',
            type : 'POST',
            contentType : "application/json",
            dataType : "json"
        }).done(suc).fail(err);
    },

    listPlugins : function(suc, err, sync) {
        wok.requestJSON({
            url : 'plugins',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            async : !sync,
            success : suc,
            error : err
        });
     },
};
