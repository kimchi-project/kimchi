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
(function($) {
    $.fn.serializeObject = function() {
        var formDataArray = $(this).serializeArray();
        var formData = {};
        $.each(formDataArray, function(index, data) {
            var names=kimchi.form.parseFormName(data.name);
            kimchi.form.assignValue(names,data.value,formData);
        });
        return formData;
    };
}(jQuery));

kimchi.form = {};
kimchi.form.assignValue = function(names, value, obj) {
    var result=value;

    if(names.length!=0) {
        result=obj;
        var name=names.shift();
        if(!result) {
            result={};
        }
        if(!result[name]) {
            result[name]=kimchi.form.assignValue(names,value);
        }
        else if(names.length==0) {
            if(Array.isArray(result[name])){
                result[name].push(value);
            }
            else {
                result[name]=[result[name],value];
            }
        }
        else {
            result[name]=kimchi.form.assignValue(names,value,result[name]);
        }
    }
    return(result);
}

kimchi.form.parseFormName = function(name, parsedName) {
    if (!parsedName) {
        parsedName=[];
    }
    if(!name || name=="") {
        return(parsedName);
    }
    var openBracket=name.indexOf("[");
    if (openBracket!=-1) {
        var id=name.slice(0, openBracket);
        parsedName.push(id);
        var closeBracket=name.lastIndexOf("]");
        if (closeBracket==-1) {
            closeBracket=name.length;
        }
        var tmpName=name.slice(openBracket+1,closeBracket);
        kimchi.form.parseFormName(tmpName,parsedName);
    }
    else {
        parsedName.push(name);
    }
    return(parsedName);
}
