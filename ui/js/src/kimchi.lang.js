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
kimchi.lang = {
    all: function() {
        return {
          'en_US': 'English (US)',
          'zh_CN': '中文（简体）',
          'pt_BR': 'Português (Brasil)',
          'de_DE': 'Deutsch (Deutschland)',
          'es_ES': 'Español (España)',
          'fr_FR': 'Français (France)',
          'it_IT': 'Italiano (Italia)',
          'ja_JP': '日本語 (日本)',
          'ko_KR': '한국어 (대한민국)',
          'ru_RU': 'Русский (Россия)',
          'zh_TW': '中文（繁體）'
        };
    },

    /**
     * Language is determined by the following sequence:
     * 1) Cookie setting; or if not set ->
     * 2) HTML DOM lang attribute; or if not set ->
     * 3) DEFAULT (en_US).
     */
    get: function() {
        return kimchi.cookie.get('kimchiLang') ||
            $('html').prop('lang') ||
            'en_US';
    },

    set: function(lang) {
        kimchi.cookie.set('kimchiLang', lang, 365);
    }
};
