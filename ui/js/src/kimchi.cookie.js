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
kimchi.cookie = {
    set: function(key, value, expireDays) {
        value = encodeURIComponent(value);
        value += '; secure'
        if (expireDays) {
            var expireDate = new Date();
            expireDate.setDate(expireDate.getDate() + expireDays);
            value += '; expires=' + expireDate.toUTCString();
        }
        document.cookie = key + '=' + value;
    },

    get: function(key) {
        var cookieRe = new RegExp(';?\\\s*(' + key + ')=(\s*[^;]*);?', 'g');
        var match = cookieRe.exec(document.cookie);
        return match ? decodeURIComponent(match[2]) : undefined;
    },

    remove: function(key) {
        var utcString = new Date().toUTCString();
        document.cookie = key + '=; expires=' + utcString;
    }
};
