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
kimchi.login_main = function() {

    var selectedLanguage = kimchi.lang.get();
    var languages = kimchi.lang.all();
    for(var k in languages) {
        var opt = $([
            '<option value="',
            k,
            '">',
            languages[k],
            '</option>'
        ].join('')).appendTo($('#language'));
        $(opt).prop('selected', selectedLanguage === k);
    }

    $('#language').on('change', function() {
        kimchi.topic('languageChanged').publish($(this).val());
    });

    var validateNonEmpty = function(idsArray) {
        for(var i = 0; i < idsArray.length; i++) {
            var id = idsArray[i];
            if (!$('#' + id).val()) {
                $('#' + id + '-msg').text(i18n['KCHAUTH6002E']);
                placeCursor(id);
                return false;
            }
            else {
                $('#' + id + '-msg').empty();
            }
        }

        return true;
    };

    var placeCursor = function(id) {
        if (id && $('#' + id).size() > 0) {
            $('#' + id).focus();
            return;
        }

        var userName = kimchi.user.getUserName();
        userName && $('#username').val(userName);

        var nodeToFocus = ! $('#username').val() ? $('#username') :
            (! $('#password').val() ? $('#password') : $('#btn-login'));

        $(nodeToFocus).focus();
    };

    var login = function(event) {

        if (!validateNonEmpty(['username', 'password'])) {
            return false;
        }

        $('#btn-login').text(i18n['KCHAUTH6002M']).prop('disabled', true);

        var userName = $('#username').val();
        userName && kimchi.user.setUserName(userName);
        var settings = {
            username: userName,
            password: $("#password").val()
        };

        kimchi.login(settings, function() {
            var pAjax = kimchi.previousAjax;
            var consoleURL = kimchi.cookie.get("console_uri");
            if (consoleURL) {
                var path = /.*\/(.*?)\?.*/g.exec(consoleURL)[1];
                var query = consoleURL.substr(consoleURL.indexOf("?") + 1);

                var proxy_port = /.*port=(.*?)(&|$)/g.exec(consoleURL)[1];
                var http_port = /.*kimchi=(.*?)(&|$)/g.exec(consoleURL);
                var kimchi_port = http_port ? http_port[1] : location.port;

                url = location.protocol + "//" + location.hostname;
                url += ":" + proxy_port + "/console.html?url=" + path;
                url += "&" + query;
                url += "&kimchi=" + kimchi_port;

                kimchi.cookie.remove("console_uri");
                window.location.replace(url)
            }
            else if (pAjax && true === pAjax['resend']) {
                pAjax['error'] = pAjax['originalError'];
                $.ajax(pAjax);
                kimchi.previousAjax = null;
            }
            else if(pAjax) {
                window.location.reload();
            }

            kimchi.user.showUser(true);
            kimchi.window.close();
        }, function() {
            kimchi.message.error.code('KCHAUTH6001E');
            $('#btn-login').prop('disabled', false).text(i18n['KCHAUTH6001M']);
            placeCursor('username');
        });

        return false;
    };

    $('#form-login').on('submit', login);

    placeCursor();
};
