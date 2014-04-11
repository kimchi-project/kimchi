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

Object.defineProperty(Object.prototype, "getDeepValue", {
    value: function(key) {
        var result=undefined;
        try {
            if(!Array.isArray(key)) {
                key=key.parseKey();
            }
            if(key.length!=0) {
                var tmpName=key.shift();
                if(this[tmpName]!=undefined) {
                    result=this[tmpName];
                }
                if(key.length!=0) {
                    result=result.getDeepValue(key);
                }
            }
        }
        catch (err) {
            //do nothing
        }
        return(result);
        }
});

Object.defineProperty(Object.prototype, "setDeepValue", {
    value: function(key, val) {
        var keys;
        if(Array.isArray(key)) {
            keys=key;
        }
        else {
            keys=key.parseKey();
        }
        if(keys.length!=0) {
            var key=keys.shift();
            if(keys.length==0) {
                if(this[key]==undefined) {
                    this[key]=val;
                }
                else if(Array.isArray(this[key])){
                    this[key].push(val);
                }
                else {
                    var tmpArray=[]
                    tmpArray.push(this[key]);
                    tmpArray.push(val);
                    this[key]=tmpArray;
                }
            }
            else {
                if(this[key]==undefined) {
                    this[key]=new Object();
                    this[key].setDeepValue(keys,val);
                }
                else if(Array.isArray(this[key])){
                    var tmpO=new Object();
                    this[key].push(tmpO);
                    tmpO.setDeepValue(keys,val);
                }
                else {
                   this[key].setDeepValue(keys,val);
                }
            }
        }
        return(this);
    }
});
