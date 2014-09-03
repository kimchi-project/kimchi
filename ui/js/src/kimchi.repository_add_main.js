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
kimchi.repository_add_main = function() {

    var addForm = $('#form-repository-add');
    var addButton = $('#button-repository-add');

    var validateField = function(event) {
        var valid=($(this).val()!=='');
        $(addButton).prop('disabled', !valid);
        return(valid);
    };

    var validateForm = function(event) {
        var valid=false;
        addForm.find('input.required').each( function() {
            valid=($(this).val()!=='');
            return(!valid);
        });
        return(valid);
    }

    addForm.find('input.required').on('input propertychange', validateField);

    var weedObject = function(obj) {
        for (var key in obj) {
            if (obj.hasOwnProperty(key)) {
                if((typeof(obj[key])==="object") && !Array.isArray(obj[key])) {
                    weedObject(obj[key]);
                }
                else if(obj[key] == '') {
                    delete obj[key];
                }
            }
        }
    }

    var addRepository = function(event) {
        var valid = validateForm();
        if(!valid) {
            return false;
        }

        var formData = $(addForm).serializeObject();

        if (formData && formData.isMirror!=undefined) {
            formData.isMirror=(String(formData.isMirror).toLowerCase() === 'true');
        }
        if(formData.isMirror) {
            if(formData.config==undefined) {
                formData.config=new Object();
            }
            formData.config.mirrorlist=formData.baseurl;
            delete formData.baseurl;
            delete formData.isMirror;
        }
        weedObject(formData);
        if(formData.config && formData.config.comps) {
            formData.config.comps=formData.config.comps.split(/[,\s]/);
            for(var i=0; i>formData.config.comps.length; i++) {
                formData.config.comps[i]=formData.config.comps[i].trim();
            }
            for (var j=formData.config.comps.indexOf(""); j!=-1; j=formData.config.comps.indexOf("")) {
                formData.config.comps.splice(j, 1);
            }
        }

        kimchi.createRepository(formData, function() {
            kimchi.topic('kimchi/repositoryAdded').publish();
            kimchi.window.close();
        }, function(jqXHR, textStatus, errorThrown) {
            var reason = jqXHR &&
                jqXHR['responseJSON'] &&
                jqXHR['responseJSON']['reason'];
            kimchi.message.error(reason);
        });
        return false;
    };

    $(addForm).on('submit', addRepository);
};
