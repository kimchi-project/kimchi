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

        var userName = kimchi.user.getUserID();
        userName && $('#user-id').val(userName);

        var nodeToFocus = ! $('#user-id').val() ? $('#user-id') :
            (! $('#password').val() ? $('#password') : $('#btn-login'));

        $(nodeToFocus).focus();
    };

    var login = function(event) {

        if (!validateNonEmpty(['user-id', 'password'])) {
            return false;
        }

        $('#btn-login').text(i18n['KCHAUTH6002M']).prop('disabled', true);

        var userID = $('#user-id').val();
        userID && kimchi.user.setUserID(userID);
        var settings = {
            userid: userID,
            password: $("#password").val()
        };

        kimchi.login(settings, function() {
            var pAjax = kimchi.previousAjax;
            if (pAjax && true === pAjax['resend']) {
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
            $('#message-container').text(i18n['KCHAUTH6001E']);
            $('#btn-login').prop('disabled', false).text(i18n['KCHAUTH6001M']);
            placeCursor('user-id');
        });

        return false;
    };

    $('#form-login').on('submit', login);

    placeCursor();
};
