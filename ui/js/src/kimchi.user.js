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
kimchi.user = (function() {
    var getUserName = function() {
        return kimchi.cookie.get('username');
    };

    var setUserName = function(userName) {
        kimchi.cookie.set('username', userName, 365);
    };

    var showUser = function(toShow) {
        if (toShow) {
            var userName = getUserName();
            userName && $('#user-name').text(userName);
            $('#user').removeClass('not-logged-in');
            return;
        }

        $('#user').addClass('not-logged-in');
    };

    return {
        getUserName: getUserName,
        setUserName: setUserName,
        showUser: showUser
    };
})();
