/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014
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
kimchi.substitute = function(templateStr, data, tag) {
    tag = tag || /\{([^\}]+)\}/g;

    var escapeHtml = function(html) {
        return String(html)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    };

    return templateStr.replace(tag, function(matchResult, express) {
        var propertyArray = express.split('!');
        var defaultValue = propertyArray[1] || '';
        propertyArray = propertyArray[0].split('.');
        var value = data, i = 0, l = propertyArray.length, property;
        for (; i < l; i++) {
            property = propertyArray[i];
            if (value) {
                value = value[property];
            } else {
                break;
            }
        }
        return escapeHtml((value || value === 0) ? value : defaultValue);
    });
};
