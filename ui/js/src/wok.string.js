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

Object.defineProperty(String.prototype, "parseKey", {
    value: function(parsedKey) {
        try {
            if (!Array.isArray(parsedKey)) {
                parsedKey=[];
            }
        }
        catch (err) {
            parsedKey=[];
        }
        var openBracket=this.indexOf("[");
        if (openBracket!=-1) {
            var id=this.slice(0, openBracket);
            parsedKey.push(id);
            var closeBracket=this.lastIndexOf("]");
            if (closeBracket==-1) {
                closeBracket=this.length;
            }
            var tmpName=this.slice(openBracket+1,closeBracket);
            tmpName.parseKey(parsedKey);
        }
        else {
            parsedKey.push(this);
        }
        return(parsedKey);
        }
});
