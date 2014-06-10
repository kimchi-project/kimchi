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
kimchi.guest_edit_main = function() {
    var buttonContainer = $('#action-button-container');
    $('#guest-edit-tabs').tabs({
        beforeActivate: function(event, ui) {
            var deactivated = ui['newPanel'];
            if($(deactivated).attr('id') === 'form-guest-edit-general') {
                $(buttonContainer).removeClass('hidden');
            }
            else {
                $(buttonContainer).addClass('hidden');
            }
        }
    });

    var guestEditForm = $('#form-guest-edit-general');
    var saveButton = $('#guest-edit-button-save');

    var refreshCDROMs = function() {
        kimchi.listVMStorages({
            vm: kimchi.selectedGuest
        }, function(storages) {
            var container = $('#form-guest-edit-storage .body');
            $(container).empty();

            $.each(storages, function(index, storage) {
                storage['vm'] = kimchi.selectedGuest;
                rowHTML = $('#' + storage['type'] + '-row-tmpl').html();
                var templated = kimchi.substitute(rowHTML, storage);
                container.append(templated);
            });

            $('.replace', container).button({
                icons: {
                    primary: 'ui-icon-pencil'
                },
                text: false
            });

            $('.detach', container).button({
                icons: {
                    primary: 'ui-icon-trash'
                },
                text: false
            });

            $('.save', container).button({
                icons: {
                    primary: 'ui-icon-disk'
                },
                text: false
            });

            $('.cancel', container).button({
                icons: {
                    primary: 'ui-icon-arrowreturnthick-1-w'
                },
                text: false
            });
        });
    };

    var initStorageListeners = function() {
        var container = $('#form-guest-edit-storage .body');
        var toggleCDROM = function(rowNode, toEdit) {
            $('button.replace,button.detach', rowNode)
                [(toEdit ? 'add' : 'remove') + 'Class']('hidden');
            $('button.save,button.cancel', rowNode)
                [(toEdit ? 'remove' : 'add') + 'Class']('hidden');
            var pathBox = $('.path input', rowNode)
                .prop('readonly', !toEdit);
            toEdit && pathBox.select();
        };

        var replaceCDROM = function(event) {
            event.preventDefault();
            kimchi.selectedGuestStorage = $(this).data('dev');
            $('.item', container).each(function(i, n) {
                toggleCDROM(n);
            });
            var rowNode = $('#cdrom-' + kimchi.selectedGuestStorage);
            toggleCDROM(rowNode, true);
        };

        $(container).on('click', 'button.replace', replaceCDROM);

        $(container).on('click', 'button.detach', function(e) {
            e.preventDefault();
            var settings = {
                title : i18n['KCHAPI6004M'],
                content : i18n['KCHVMCD6001M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            };

            var dev = $(this).data('dev');
            kimchi.confirm(settings, function() {
                kimchi.deleteVMStorage({
                    vm: kimchi.selectedGuest,
                    dev: dev
                }, function() {
                    kimchi.topic('kimchi/vmCDROMDetached').publish();
                });
            });
        });

        $(container).on('click', 'button.save', function(event) {
            event.preventDefault();
            var path = $('#cdrom-path-' + kimchi.selectedGuestStorage).val();
            var settings = {
                vm: kimchi.selectedGuest,
                dev: kimchi.selectedGuestStorage,
                path: path
            };

            kimchi.replaceVMStorage(settings, function(result) {
                kimchi.topic('kimchi/vmCDROMReplaced').publish({
                    result: result
                });
            }, function(result) {
                var errText = result['reason'] ||
                    result['responseJSON']['reason'];
                kimchi.message.error(errText);
            });
        });

        $(container).on('click', 'button.cancel', function(event) {
            event.preventDefault();
            var rowNode = $('#cdrom-' + kimchi.selectedGuestStorage);
            toggleCDROM(rowNode);
        });
    };

    var setupInterface = function() {
        $(".add", "#form-guest-edit-interface").button({
            icons: { primary: "ui-icon-plusthick" },
            text: false
        }).click(function(){
            addItem({
                mac: "",
                network: "",
                type: "network",
                viewMode: "hide",
                editMode: ""
            });
        });
        var toggleEdit = function(item, on){
            $("label", item).toggleClass("hide", on);
            $("select", item).toggleClass("hide", !on);
            $(".action-area", item).toggleClass("hide");
        };
        var addItem = function(data) {
            var itemNode = $.parseHTML(kimchi.substitute($('#interface-tmpl').html(),data));
            $(".body", "#form-guest-edit-interface").append(itemNode);
            $("select", itemNode).append(networkOptions);
            if(data.network!==""){
                $("select", itemNode).val(data.network);
            }
            $(".edit", itemNode).button({
                disabled: true,
                icons: { primary: "ui-icon-pencil" },
                text: false
            }).click(function(){
                toggleEdit($(this).parent().parent(), true);
            });
            $(".delete", itemNode).button({
                icons: { primary: "ui-icon-trash" },
                text: false
            }).click(function(){
                var item = $(this).parent().parent();
                kimchi.deleteGuestInterface(kimchi.selectedGuest, item.prop("id"), function(){
                    item.remove();
                });
            });
            $(".save", itemNode).button({
                icons: { primary: "ui-icon-disk" },
                text: false
            }).click(function(){
                var item = $(this).parent().parent();
                var interface = {
                    network: $("select", item).val(),
                    type: "network"
                };
                var postUpdate = function(){
                    $("label", item).text(interface.network);
                    toggleEdit(item, false);
                };
                if(item.prop("id")==""){
                    kimchi.createGuestInterface(kimchi.selectedGuest, interface, function(data){
                        item.prop("id", data.mac);
                        postUpdate();
                    });
                }else{
                    kimchi.updateGuestInterface(kimchi.selectedGuest, item.prop("id"), interface, function(){
                        postUpdate();
                    });
                }
            });
            $(".cancel", itemNode).button({
                icons: { primary: "ui-icon-arrowreturnthick-1-w" },
                text: false
            }).click(function(){
                var item = $(this).parent().parent();
                $("label", item).text()==="" ? item.remove() : toggleEdit(item, false);
            });
        };
        var networkOptions = "";
        kimchi.listNetworks(function(data){
            for(var i=0;i<data.length;i++){
                var isSlected = i==0 ? " selected" : "";
                networkOptions += "<option"+isSlected+">"+data[i].name+"</option>";
            }
            kimchi.getGuestInterfaces(kimchi.selectedGuest, function(data){
                for(var i=0;i<data.length;i++){
                    data[i].viewMode = "";
                    data[i].editMode = "hide";
                    addItem(data[i]);
                }
            });
        });
    };

    var initContent = function(guest) {
        guest['icon'] = guest['icon'] || 'images/icon-vm.png';
        $('#form-guest-edit-general').fillWithObject(guest);

        refreshCDROMs();

        $('#guest-edit-attach-cdrom-button').button({
            icons: {
                primary: "ui-icon-plusthick"
            },
            text: false
        }).click(function(event) {
            event.preventDefault();
            kimchi.window.open("guest-storage-add.html");
        });

        var onAttached = function(params) {
            refreshCDROMs();
        };
        var onReplaced = function(params) {
            refreshCDROMs();
        };
        var onDetached = function(params) {
            refreshCDROMs();
        };

        initStorageListeners();

        setupInterface();

        kimchi.topic('kimchi/vmCDROMAttached').subscribe(onAttached);
        kimchi.topic('kimchi/vmCDROMReplaced').subscribe(onReplaced);
        kimchi.topic('kimchi/vmCDROMDetached').subscribe(onDetached);

        kimchi.clearGuestEdit = function() {
            kimchi.topic('kimchi/vmCDROMAttached').unsubscribe(onAttached);
            kimchi.topic('kimchi/vmCDROMReplaced').unsubscribe(onReplaced);
            kimchi.topic('kimchi/vmCDROMDetached').unsubscribe(onDetached);
        };
    };

    kimchi.retrieveVM(kimchi.selectedGuest, initContent);

    var submitForm = function(event) {
        $(saveButton).prop('disabled', true);
        var data=$('#form-guest-edit-general').serializeObject();
        if(data['memory']!=undefined) {
            data['memory'] = Number(data['memory']);
        }
        if(data['cpus']!=undefined) {
            data['cpus']   = Number(data['cpus']);
        }

        kimchi.updateVM(kimchi.selectedGuest, data, function() {
            kimchi.listVmsAuto();
            kimchi.window.close();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
            $(saveButton).prop('disabled', false);
        });

        event.preventDefault();
    };

    $(guestEditForm).on('submit', submitForm);
    $(saveButton).on('click', submitForm);
};
