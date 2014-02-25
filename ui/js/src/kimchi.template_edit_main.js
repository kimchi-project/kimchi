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
kimchi.template_edit_main = function() {
    var templateEditForm = $('#form-template-edit');
    var origDisks;
    $('#template-name', templateEditForm).val(kimchi.selectedTemplate);
    kimchi.retrieveTemplate(kimchi.selectedTemplate, function(template) {
        origDisks =  template.disks;
        for ( var prop in template) {
            $('input[name="' + prop + '"]', templateEditForm).val(template[prop]);
        }
        var disks = template.disks;
        $('input[name="disks"]').val(disks[0].size);
        kimchi.listStoragePools(function(result) {
            var options = [];
            if (result && result.length) {
                $.each(result, function(index, storagePool) {
                    if(storagePool.type !== 'kimchi-iso') {
                        options.push({
                            label: storagePool.name,
                            value: '/storagepools/' + storagePool.name
                        });
                    }
                });
            }
            kimchi.select('template-edit-storagePool-list', options);
        });
        kimchi.listNetworks(function(result) {
            if(result && result.length > 0) {
                var html = '';
                var tmpl = $('#tmpl-network').html();
                $.each(result, function(index, network) {
                    html += kimchi.template(tmpl, network);
                });
                $('#template-edit-network-list').html(html).show();
                if(template.networks && template.networks.length > 0) {
                    $('input[name="networks"]', templateEditForm).each(function(index, element) {
                        var value = $(element).val();
                        if(template.networks.indexOf(value) >= 0) {
                            $(element).prop('checked', true);
                        }
                    });
                }
            } else {
                $('#template-edit-network-list').hide();
            }
        });
    });

    $('#tmpl-edit-button-cancel').on('click', function() {
        kimchi.window.close();
    });

    $('#tmpl-edit-button-save').on('click', function() {
        var editableFields = [ 'name', 'cpus', 'memory', 'storagepool', 'disks'];
        var data = {};
        $.each(editableFields, function(i, field) {
            /* Support only 1 disk at this moment */
            if (field == 'disks') {
               origDisks[0].size = Number($('#form-template-edit [name="' + field + '"]').val());
               data[field] = origDisks;
            }
            else {
               data[field] = $('#form-template-edit [name="' + field + '"]').val();
            }
        });
        data['memory'] = Number(data['memory']);
        data['cpus']   = Number(data['cpus']);
        var networks = templateEditForm.serializeObject().networks;
        if (networks instanceof Array) {
            data.networks = networks;
        } else if (networks != null) {
            data.networks = [networks];
        } else {
            data.networks = [];
        }

        kimchi.updateTemplate($('#template-name').val(), data, function() {
            kimchi.doListTemplates();
            kimchi.window.close();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    });
};
