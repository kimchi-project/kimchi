/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014-2015
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
kimchi.login_main = function() {

    var selectedLanguage = kimchi.lang.get();
    $('#userLang').val(selectedLanguage);

    $('#userLang').on('change', function() {
        kimchi.lang.set($(this).val());
        location.reload();
    });

    var query = window.location.search;
    var error = /.*error=(.*?)(&|$)/g.exec(query);
    if (error && error[1] == "sessionTimeout") {
        $("#messSession").show();
    }

    var userNameBox = $('#username');
    var passwordBox = $('#password');
    var loginButton = $('#btn-login');

    var login = function(event) {
        $("#login").hide();
        $("#logging").show();

        var userName = userNameBox.val();
        userName && kimchi.user.setUserName(userName);
        var settings = {
            username: userName,
            password: passwordBox.val()
        };

        kimchi.login(settings, function(data) {
            var query = window.location.search;
            var next  = /.*next=(.*?)(&|$)/g.exec(query);
            if (next) {
                var next_url = decodeURIComponent(next[1]);
            }
            else {
                var lastPage = kimchi.cookie.get('lastPage');
                var next_url = lastPage ? lastPage.replace(/\"/g,'') : "/";
            }
            kimchi.cookie.set('roles',JSON.stringify(data.roles));
            window.location.replace(window.location.pathname.replace(/\/+login.html/, '') + next_url)
        }, function() {
            $("#messUserPass").show();
            $("#messSession").hide();
            $("#logging").hide();
            $("#login").show();
        });

        return false;
    };

    $('#btn-login').bind('click', login);
};
