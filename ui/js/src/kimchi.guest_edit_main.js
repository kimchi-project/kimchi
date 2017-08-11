/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2013-2017
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
    var authType;
    var formTargetId;
    var guestEditForm = $('#form-guest-edit-general');
    var saveButton = $('#guest-edit-button-save');
    var s390xArch = 's390x';
    var macvtapNetworks = "";
    var ovsNetworks = "";
    var networkOptions = "";

    clearTimeout(kimchi.vmTimeout);
    var bootOrderOptions = [];

    $('#modalWindow').on('hidden.bs.modal', function() {
        kimchi.setListVMAutoTimeout();
    });

    $('#guest-edit-window a[data-toggle="tab"]').on('show.bs.tab', function(tab) {
        tab.target; // newly activated tab
        tab.relatedTarget; // previous active tab
        var display_list = ['form-guest-edit-general', 'form-guest-edit-permission'];
        $(saveButton).prop('disabled', true);
        formTargetId = $(tab.target).data('id');
        var deactivated = $('form#' + formTargetId);
        if (display_list.indexOf($(deactivated).attr('id')) >= 0) {
            $(saveButton).prop('disabled', false);
        }
    });

    var submitForm = function(event) {

        var submit_map = {
            0: generalSubmit,
            3: permissionSubmit,
            6: processorSubmit
        };
        var currentTab = $('#guest-edit-window li.active a[data-toggle="tab"]').data('id');
        var toSubmit = parseInt($('#'+currentTab).index());
        var submitFun = submit_map[toSubmit];
        submitFun && submitFun(event);
        event.preventDefault();
    };

    $(guestEditForm).on('submit', submitForm);
    $(saveButton).on('click', submitForm);

    $('#guest-edit-window a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
        var target = $(this).attr('href');
        $(target).css('left', '-' + $(window).width() + 'px');
        var left = $(target).offset().left;
        $(target).css({
            left: left
        }).animate({
            "left": "0px"
        }, "10");
    });

    $('#guest-edit-window a[data-toggle="tab"]:first').tab('show');

    var refreshCDROMs = function() {
        kimchi.listVMStorages({
            vm: kimchi.selectedGuest
        }, function(storages) {
            var container = $('#form-guest-edit-storage .body');
            $(container).empty();
            $.each(storages, function(index, storage) {
                storage['vm'] = kimchi.selectedGuest;
                rowHTML = $('#' + storage['type'] + '-row-tmpl').html();
                var templated = wok.substitute(rowHTML, storage);
                container.append(templated);
            });

            if (kimchi.thisVMState === 'running') {
                $('.detach[data-type="cdrom"]', container).remove();
            }

        });
    };

    var initStorageListeners = function() {
        var container = $('#form-guest-edit-storage .body');
        var toggleCDROM = function(rowNode, toEdit) {
            $('button.replace,button.detach', rowNode)[(toEdit ? 'add' : 'remove') + 'Class']('hidden');
            $('button.save,button.cancel', rowNode)[(toEdit ? 'remove' : 'add') + 'Class']('hidden');
            var pathBox = $('.path input', rowNode)
                .prop('readonly', !toEdit);
            toEdit && pathBox.select();
            pathBox.val(pathBox.attr('value'));
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
                title: i18n['KCHAPI6004M'],
                content: i18n['KCHVMCD6001M'],
                confirm: i18n['KCHAPI6002M'],
                cancel: i18n['KCHAPI6003M']
            };
            if ($(this).data('type') === "disk") {
                settings['content'] = i18n['KCHVMCD6009M'];
            }

            var dev = $(this).data('dev');
            wok.confirm(settings, function() {
                kimchi.deleteVMStorage({
                    vm: kimchi.selectedGuest,
                    dev: dev
                }, function() {
                    wok.topic('kimchi/vmCDROMDetached').publish();
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
                wok.topic('kimchi/vmCDROMReplaced').publish({
                    result: result
                });
            }, function(result) {
                var errText = result['reason'] ||
                    result['responseJSON']['reason'];
                wok.message.error(errText, '#alert-modal-container');
            });
        });

        $(container).on('click', 'button.cancel', function(event) {
            event.preventDefault();
            var rowNode = $('#cdrom-' + kimchi.selectedGuestStorage);
            toggleCDROM(rowNode);
        });
    };

    var setupInterface = function() {
        $(".add", "#form-guest-edit-interface").on('click', function(evt) {
            evt.preventDefault();
            addItem({
                id: -1,
                mac: "",
                ips: "",
                network: "",
                type: "network",
                viewMode: "hide",
                editMode: ""
            });
        });
        var toggleEdit = function(item, on, itemId) {
          if(kimchi.hostarch === s390xArch){
              $("#label-mac-" + itemId, item).toggleClass("hide", on);
              $("#edit-mac-" + itemId, item).toggleClass("hide", !on);
              $("#label-network-" + itemId, item).toggleClass("hide", false);
              $("#label-type-" + itemId, item).toggleClass("hide", false);
              $("#label-mode-" + itemId, item).toggleClass("hide", false);
              $("select", item).toggleClass("hide", true);
              $(".bootstrap-select", item).toggleClass("hide", true);
              $(".action-area", item).toggleClass("hide");

          }else {

            $("#label-mac-" + itemId, item).toggleClass("hide", on);
            $("#edit-mac-" + itemId, item).toggleClass("hide", !on);
            $("#label-network-" + itemId, item).toggleClass("hide", false);
            $("select", item).toggleClass("hide", true);
            $(".bootstrap-select", item).toggleClass("hide", true);
            $(".action-area", item).toggleClass("hide");
          }
        };
        var addItem = function(data) {
            var oriID = data.id;
            if (data.id === -1) {
                data.id = $('#form-guest-edit-interface > .body').children().size();
            }
            if (data.ips === "" || data.ips === null || data.ips === undefined || data.ips.length === 0) {
                data.ips = i18n["KCHNET6001M"];
            } else {
                data.ips = data.ips;
            }
            if (kimchi.hostarch === s390xArch) {
                data.mode = (data.mode) ? data.mode : 'None';
                var itemNode = $.parseHTML(wok.substitute($('#interface-s390x-tmpl').html(), data));
                $(".body", "#form-guest-edit-interface").append(itemNode);

                $("select", "span.column-type", itemNode).empty().append(typeOptions);
                $("select", "span.column-mode", itemNode).empty().append(modeOptions);
                $("select", "span.column-network", itemNode).empty().append(macvtapNetworks);

                $("select", "span.column-type", itemNode).val(data.type);
                $("select", "span.column-network", itemNode).val(data.source);
                $("select", "span.column-mode", itemNode).val(data.mode);

            } else {
                var itemNode = $.parseHTML(wok.substitute($('#interface-tmpl').html(), data));
                $(".body", "#form-guest-edit-interface").append(itemNode);
                $("select", "span.column-network", itemNode).append(networkOptions);
            }

            $("select", itemNode).selectpicker({
                dropupAuto: false
            });


            $('.edit', itemNode).attr('disabled', kimchi.thisVMState === "running");
            $(".edit", itemNode).on('click', function(evt) {
                evt.preventDefault();
                toggleEdit($(this).closest('div'), true, data.id);
            });
            $(".delete", itemNode).on('click', function(evt) {
                evt.preventDefault();
                var item = $(this).parent().parent();
                kimchi.deleteGuestInterface(kimchi.selectedGuest, item.prop("id"), function() {
                    item.remove();
                });
            });
            $(".save", itemNode).on('click', function(evt) {
                evt.preventDefault();
                var item = $(this).parent().parent();

                if (kimchi.hostarch === s390xArch) {
                    if (item.prop("id") === "") { //adding new interface
                        switch ($("span.column-type select", item).val()) {
                            case 'macvtap':
                                var interface = {
                                    source: $("span.column-network select", item).val(),
                                        type: $("span.column-type select", item).val(),
                                        mac: $(":text", item).val(),
                                        ips: $(".ipText", item).val(),
                                        mode: $("span.column-mode select", item).val()
                                };
                                break;

                            case 'ovs':
                                var interface = {
                                    source: $("span.column-network select", item).val(),
                                        type: $("span.column-type select", item).val(),
                                        mac: $(":text", item).val(),
                                        ips: $(".ipText", item).val()
                                };
                                break;

                            case 'network':
                                var interface = {
                                    network: $("span.column-network select", item).val(),
                                        type: "network",
                                        mac: $(":text", item).val(),
                                        ips: $(".ipText", item).val()
                                };
                                break;
                        }
                    } else { //updating existing interface

                        switch ($("#label-type-" + data.id, item).text()) {
                            case 'macvtap':

                                var interface = {
                                    source: $("#label-network-" + data.id, item).text(),
                                        type: $("#label-type-" + data.id, item).text(),
                                        mac: $(":text", item).val(),
                                        ips: $(".ipText", item).val(),
                                        mode: $("#label-mode-" + data.id, item).text()
                                };
                                break;

                            case 'ovs':
                                var interface = {
                                    source: $("#label-network-" + data.id, item).text(),
                                        type: $("#label-type-" + data.id, item).text(),
                                        mac: $(":text", item).val(),
                                        ips: $(".ipText", item).val()
                                };
                                break;

                            case 'network':
                                var interface = {
                                    network: $("#label-network-" + data.id, item).text(),
                                        type: "network",
                                        mac: $(":text", item).val(),
                                        ips: $(".ipText", item).val()
                                };
                                break;
                        }

                    }
                } else { //in s86 arch
                    var interface = {
                        network: $("select", item).val(),
                            type: "network",
                            mac: $(":text", item).val(),
                            ips: $(".ipText", item).val()
                    };
                }

                var postUpdate = function(mac) {
                    $("#label-network-" + data.id, item).text(interface.network);
                    $("#label-mac-" + data.id, item).text(mac);
                    $("#edit-mac-" + data.id, item).val(mac);
                    toggleEdit(item, false, data.id);
                };

                var posts390xUpdate = function(result) {
                    switch(result.type){
                      case 'macvtap' :
                                      $("#label-type-" + data.id, item).text(result.type);
                                      $("#label-network-" + data.id, item).text(result.source);
                                      $("#label-mode-" + data.id, item).text(result.mode);
                           break;

                      case 'ovs' :
                                      $("#label-type-" + data.id, item).text(result.type);
                                      $("#label-network-" + data.id, item).text(result.source);
                                      $("#label-mode-" + data.id, item).text(i18n['KCHVMED6018M']);
                          break;

                      case 'network' :
                                      $("#label-type-" + data.id, item).text(result.type);
                                      $("#label-network-" + data.id, item).text(result.network);
                                      $("#label-mode-" + data.id, item).text(i18n['KCHVMED6018M']);
                            break;
                    }

                    $("#label-mac-" + data.id, item).text(result.mac);
                    $("#edit-mac-" + data.id, item).val(result.mac);
                    toggleEdit(item, false, data.id);
                };

                if (item.prop("id") === "") {
                    kimchi.createGuestInterface(kimchi.selectedGuest, interface, function(data) {
                        item.prop("id", data.mac);
                        if(kimchi.hostarch == s390xArch){
                          posts390xUpdate(data);
                        }else{
                          postUpdate(data.mac);
                        }
                    });
                } else {
                    if (item.prop('id') === interface.mac) {
                        toggleEdit(item, false, data.id);
                    } else {
                        kimchi.updateGuestInterface(kimchi.selectedGuest, item.prop('id'),
                            interface,
                            function(data) {
                                item.prop("id", data.mac);
                                postUpdate(data.mac);
                            });
                    }
                }
            });
            $(".cancel", itemNode).on('click', function(evt) {
                evt.preventDefault();
                var item = $(this).parent().parent();
                $("label", item).text() === "" ? item.remove() : toggleEdit(item, false, data.id);
            });

            if (kimchi.hostarch === s390xArch) {
                $("#interface-s390x-type-" + data.id).on('change', function() {
                    var itemNode = $(this).closest('div.item');
                    switch ($(this).val()) {
                        case 'macvtap':
                            $('#label-mode-' + data.id).addClass('hide');
                            $('span.column-mode .bootstrap-select', itemNode).toggleClass("hide", false);

                            $("span.column-network select", itemNode).empty().append(macvtapNetworks);
                            $("span.column-network select", itemNode).selectpicker('refresh');

                            break;
                        case 'ovs':
                            $('#label-mode-' + data.id).html(i18n['KCHVMED6018M']);
                            $('#label-mode-' + data.id).removeClass('hide');
                            $('span.column-mode .bootstrap-select', itemNode).toggleClass("hide", true);

                            $("span.column-network select", itemNode).empty().append(ovsNetworks);
                            $("span.column-network select", itemNode).selectpicker('refresh');
                            break;
                        case 'network':
                            $('#label-mode-' + data.id).html(i18n['KCHVMED6018M']);
                            $('#label-mode-' + data.id).removeClass('hide');
                            $('span.column-mode .bootstrap-select', itemNode).toggleClass("hide", true);

                            $("span.column-network select", itemNode).empty().append(networkOptions);
                            $("span.column-network select", itemNode).selectpicker('refresh');
                            break;
                    }
                });
                if (oriID === -1) {
                    $("#interface-s390x-type-" + data.id).trigger('change');
                }
            }

        };


        kimchi.listNetworks(function(data) {
            for (var i = 0; i < data.length; i++) {
                var isSlected = i === 0 ? " selected" : "";
                networkOptions += "<option" + isSlected + ">" + data[i].name + "</option>";
            }

            if (kimchi.hostarch === s390xArch) {

                kimchi.listmacvtapNetworks(function(data) {
                    for (var i = 0; i < data.length; i++) {
                        var isSlected = i === 0 ? ' selected="selected"' : "";
                        macvtapNetworks += "<option" + isSlected + ">" + data[i].name + "</option>";
                    }

                    kimchi.listovsNetworks(function(data) {
                        for (var i = 0; i < data.length; i++) {
                            var isSlected = i === 0 ? " selected" : "";
                            ovsNetworks += "<option" + isSlected + ">" + data[i] + "</option>";
                        }

                        kimchi.getGuestInterfaces(kimchi.selectedGuest, function(data) {
                            for (var i = 0; i < data.length; i++) {
                                data[i].viewMode = "";
                                data[i].editMode = "hide";
                                data[i].id = i;
                                addItem(data[i]);
                            }
                        });
                    });
                });
            } else {
                kimchi.getGuestInterfaces(kimchi.selectedGuest, function(data) {
                    for (var i = 0; i < data.length; i++) {
                        data[i].viewMode = "";
                        data[i].editMode = "hide";
                        data[i].id = i;
                        addItem(data[i]);
                    }
                });
            }
        });

        if (kimchi.hostarch === s390xArch) {
            $('#form-guest-edit-interface > div.header').hide();
            $('#form-guest-edit-interface > div.s390x').show();

            var typeOptionsdata = [{
                label: i18n['KCHVMED6013M'],
                value: 'macvtap'
            }, {
                label: i18n['KCHVMED6014M'],
                value: 'ovs'
            }, {
                label: i18n['KCHVMED6015M'],
                value: 'network'
            }];
            var typeOptions = '';

            for (var i = 0; i < typeOptionsdata.length; i++) {
                var isSlected = i === 0 ? ' selected="selected"' : "";
                typeOptions += '<option' + isSlected + ' value="' + typeOptionsdata[i].value + '">' + typeOptionsdata[i].label + '</option>';
            }

            var modeOptionsdata = [{
                label: i18n['KCHVMED6016M'],
                value: 'bridge'
            }, {
                label: i18n['KCHVMED6017M'],
                value: 'vepa'
            }];
            var modeOptions = '';

            for (var i = 0; i < modeOptionsdata.length; i++) {
                var isSlected = i === 0 ? " selected" : "";
                modeOptions += '<option' + isSlected + ' value="' + modeOptionsdata[i].value + '">' + modeOptionsdata[i].label + '</option>';
            }
        } else {
            $('#form-guest-edit-interface > div.header').show();
            $('#form-guest-edit-interface > div.s390x').hide();
        }
    };

    var setupPermission = function() {
        //set up for LDAP
        $(".add", "#form-guest-edit-permission").on('click', function(evt) {
            evt.preventDefault();
            addItem({
                user: "",
                freeze: false,
                viewMode: "hide",
                editMode: "",
                checked: true
            });
        });
        var addItem = function(data) {
            var itemNode = $.parseHTML(wok.substitute($('#ldap-user-tmpl').html(), data));
            $(".body", "#form-guest-edit-permission .ldap").append(itemNode);
            $(".delete", itemNode).on('click', function(evt) {
                evt.preventDefault();
                var item = $(this).parent().parent();
                item.remove();
            });
            $("input").focusout(function() {
                var item = $(this).parent().parent();
                var user = $(this).val();
                item.prop("id", user);
                $("label", item).text(user);
            });
            $("input").focusin(function() {
                $(this).removeClass("checked");
            });

            if (data.checked === true) {
                $(".checked", itemNode).addClass("hide");
            }
        };
        var toggleEdit = function(item, on) {
            $(".cell span", item).toggleClass("hide", on);
            $("input", item).toggleClass("hide", !on);
            $(".action-area", item).toggleClass("hide");
        };
        //set up for PAM
        var userNodes = {},
            groupNodes = {};
        authType = wok.config['auth'];
        if (authType === 'pam') {
            $("#form-guest-edit-permission .ldap").hide();
            kimchi.retrieveVM(kimchi.selectedGuest, function(vm) {
                kimchi.getUsers(function(users) {
                    kimchi.getGroups(function(groups) {
                        var subArray = function(a1, a2) { //a1-a2
                            for (var i = 0; i < a2.length; i++) {
                                for (var j = 0; j < a1.length; j++) {
                                    if (a2[i] === a1[j]) {
                                        a1.splice(j, 1);
                                        break;
                                    }
                                }
                            }
                        };
                        subArray(users, vm.users);
                        subArray(groups, vm.groups);
                        init(users, groups, vm.users, vm.groups);
                    });
                });
            });
        } else if (authType === 'ldap') {
            $("#form-guest-edit-permission .pam").hide();
            kimchi.retrieveVM(kimchi.selectedGuest, function(vm) {
                for (var i = 0; i < vm.users.length; i++) {
                    addItem({
                        user: vm.users[i],
                        viewMode: "",
                        freeze: true,
                        editMode: "hide",
                        checked: true
                    });
                }
            });
        }
        var sortNodes = function(container, isUser) {
            nodes = container.children();
            var keys = [];
            nodes.each(function() {
                keys.push($("label", this).text());
            });
            keys.sort();
            container.empty();
            for (var i = 0; i < keys.length; i++) {
                var itemNode = isUser ? userNodes[keys[i]] : groupNodes[keys[i]];
                $(itemNode).click(function() {
                    $(this).toggleClass("item-picked");
                });
                container.append(itemNode);
            }
        };
        var init = function(availUsers, availGroups, selUsers, selGroups) {
            var initNode = function(key, isUserNode) {
                var nodeGroups = isUserNode ? userNodes : groupNodes;
                nodeGroups[key] = $.parseHTML(wok.substitute($('#permission-item-pam').html(), {
                    val: key,
                    class: isUserNode ? "fa-user" : "fa-users"
                }));
            };
            for (var i = 0; i < availUsers.length; i++) {
                initNode(availUsers[i], true);
                $("#permission-avail-users").append(userNodes[availUsers[i]]);
            }
            sortNodes($("#permission-avail-users"), true);
            for (var i = 0; i < selUsers.length; i++) {
                initNode(selUsers[i], true);
                $("#permission-sel-users").append(userNodes[selUsers[i]]);
            }
            sortNodes($("#permission-sel-users"), true);
            for (var i = 0; i < availGroups.length; i++) {
                initNode(availGroups[i], false);
                $("#permission-avail-groups").append(groupNodes[availGroups[i]]);
            }
            sortNodes($("#permission-avail-groups"), false);
            for (var i = 0; i < selGroups.length; i++) {
                initNode(selGroups[i], false);
                $("#permission-sel-groups").append(groupNodes[selGroups[i]]);
            }
            sortNodes($("#permission-sel-groups"), false);
        };
        var filterNodes = function(key, container) {
            container.children().each(function() {
                $(this).css("display", $("label", this).text().indexOf(key) === -1 ? "none" : "");
            });
        };
        $("#permission-avail-searchBox").on("keyup", function() {
            var key = $(this).val();
            filterNodes(key, $("#permission-avail-users"));
            filterNodes(key, $("#permission-avail-groups"));
        });
        $("#permission-sel-searchBox").on("keyup", function() {
            var key = $(this).val();
            filterNodes(key, $("#permission-sel-users"));
            filterNodes(key, $("#permission-sel-groups"));
        });
        $('#permissionGo').on('click', function(evt) {
            evt.preventDefault();
            $("#permission-avail-users").children(".item-picked").appendTo("#permission-sel-users").removeClass("item-picked");
            sortNodes($("#permission-sel-users"), true);
            $("#permission-avail-groups").children(".item-picked").appendTo("#permission-sel-groups").removeClass("item-picked");
            sortNodes($("#permission-sel-groups"), false);
            $("#permission-sel-searchBox").val("");
            filterNodes("", $("#permission-sel-users"));
            filterNodes("", $("#permission-sel-groups"));
        });
        $('#permissionBack').on('click', function(evt) {
            evt.preventDefault();
            $("#permission-sel-users").children(".item-picked").appendTo("#permission-avail-users").removeClass("item-picked");
            sortNodes($("#permission-avail-users"), true);
            $("#permission-sel-groups").children(".item-picked").appendTo("#permission-avail-groups").removeClass("item-picked");
            sortNodes($("#permission-avail-groups"), false);
            $("#permission-avail-searchBox").val("");
            filterNodes("", $("#permission-avail-users"));
            filterNodes("", $("#permission-avail-groups"));
        });
    };

    var filterPCINodes = function(group, text) {
        text = text.trim().split(" ");
        var rows = $('.body', '#form-guest-edit-pci').find('div');
        if (text === "") {
            rows.show();
            return;
        }
        rows.hide();

        rows.filter(function(index, value) {
            var $span = $(this);
            var $itemGroup = $('button i', this);
            for (var i = 0; i < text.length; ++i) {
                if ($span.is(":containsNC('" + text[i] + "')")) {
                    if (group === 'all') {
                        return true;
                    } else if (group === 'toAdd' && $itemGroup.hasClass('fa-power-off')) {
                        return true;
                    } else if (group === 'added' && $itemGroup.hasClass('fa-ban')) {
                        return true;
                    }
                }
            }
            return false;
        }).show();
    };

    var _generatePciDeviceHtml = function(devices, pciType) {
        var pciEnabled = kimchi.capabilities.kernel_vfio;
        var deviceHTml = devices.map(function(device, index) {
            device.iconClass = (pciType === 'hostPCIs' ? 'fa-power-off' : (pciType === 'vmPCIs' ? 'fa-ban' : 'fa-power-off'));
            device.status = (pciType === 'vmPCIs' ? 'enabled' : 'disabled');
            device.product = (device.product !== null ? device.product.description : '');
            device.vendor = (device.vendor !== null ? device.vendor.description : '');
            deviceHtml = $.parseHTML(wok.substitute($('#pci-tmpl').html(), {
                status: device.status,
                name: device.name,
                product: device.product,
                vendor: device.vendor
            }));
            pciEnabled || $('button', deviceHtml).remove();
            $('button > i', deviceHtml).addClass(device.iconClass);
            if (kimchi.thisVMState === "running" && device.vga3d) {
                $('button', deviceHtml).prop("disabled", true);
            }
            device = deviceHtml[0].outerHTML;
            $('.body', '#form-guest-edit-pci').append(device);
        });
    };
    var getOngoingAttachingDevices = function(task) {
        kimchi.trackTask(task.id, function(result) {
            kimchi.getAvailableHostPCIDevices(function(arrPCIDevices) {
                kimchi.getVMPCIDevices(kimchi.selectedGuest, function(vmPCIs) {
                    for (var k = 0; k < vmPCIs.length; k++) {
                        $('#' + vmPCIs[k].name + '.item').removeClass('disabled').addClass('enabled');
                        $('#' + vmPCIs[k].name + ' .action-area button i').removeClass('fa-power-off').addClass('fa-ban');
                    }
                });
            });
            $('#form-guest-edit-pci > .wok-mask').fadeOut(300, function() {});
            wok.message.success(i18n['KCHVMED6010M'], '#alert-modal-container');
            filterPCINodes($('select', '#form-guest-edit-pci').val(), $('input#guest-edit-pci-filter', '#form-guest-edit-pci').val());
        }, function(result) {
            if (result['message']) {
                var errText = result['message'];
            } else {
                var errText = result['responseJSON']['reason'];
            }
            $('#form-guest-edit-pci > .wok-mask').fadeOut(300, function() {});
            filterPCINodes($('select', '#form-guest-edit-pci').val(), $('input#guest-edit-pci-filter', '#form-guest-edit-pci').val());
            result && wok.message.error(errText, '#alert-modal-container');
        }, function(result) {
            $('#form-guest-edit-pci > .wok-mask').show();
        });
    };
    var getOngoingDetachingDevices = function(task) {
        kimchi.trackTask(task.id, function(result) {
            kimchi.getAvailableHostPCIDevices(function(arrPCIDevices) {
                kimchi.getVMPCIDevices(kimchi.selectedGuest, function(vmPCIs) {
                    for (var k = 0; k < arrPCIDevices.length; k++) {
                        $('#' + arrPCIDevices[k].name + '.item').removeClass('enabled').addClass('disabled');
                        $('#' + arrPCIDevices[k].name + ' .action-area button i').removeClass('fa-ban').addClass('fa-power-off');
                    }
                    for (var k = 0; k < vmPCIs.length; k++) {
                        $('#' + arrPCIDevices[k].name + '.item').removeClass('disabled').addClass('enabled');
                        $('#' + arrPCIDevices[k].name + ' .action-area button i').removeClass('fa-power-off').addClass('fa-ban');
                    }
                });
            });
            $('#form-guest-edit-pci > .wok-mask').fadeOut(300, function() {});
            wok.message.success(i18n['KCHVMED6011M'], '#alert-modal-container');
            //id is for the object that is being added back to the available PCI devices
            filterPCINodes($('select', '#form-guest-edit-pci').val(), $('input#guest-edit-pci-filter', '#form-guest-edit-pci').val());
        }, function(result) {
            if (result['message']) {
                var errText = result['message'];
            } else {
                var errText = result['responseJSON']['reason'];
            }
            $('#form-guest-edit-pci > .wok-mask').fadeOut(300, function() {});
            filterPCINodes($('select', '#form-guest-edit-pci').val(), $('input#guest-edit-pci-filter', '#form-guest-edit-pci').val());
            result && wok.message.error(errText, '#alert-modal-container');
        }, function(result) {
            $('#form-guest-edit-pci > .wok-mask').show();
        });
    };
    var pciDeviceButtonHandler = function() {
        $('.btn.btn-link', '#form-guest-edit-pci').on('click', function(event) {
            event.preventDefault();
            if (event.originalEvent.detail > 1)
                return;
            var obj = $(this);
            var objIcon = obj.find('i');
            var id = obj.parent().parent().attr('id');
            if (objIcon.hasClass('fa-ban')) {
                kimchi.removeVMPCIDevice(kimchi.selectedGuest, id, function(task) {
                    getOngoingDetachingDevices(task);
                }, function(err) {
                    wok.message.error(err.responseJSON.reason, '#alert-modal-container');
                });
            } else {
                $('html').addClass('in-progress');
                $('#form-guest-edit-pci > .wok-mask').show();
                var haveCompanions = false;
                var pciTitle = i18n['KCHVMED6007M'] + '\n';
                kimchi.getPCIDeviceCompanions(id, function(infoData) {
                    for (var p = 0; p < infoData.length; p++) {
                        if (infoData[p].device_type === 'net') {
                            haveCompanions = true;
                            pciTitle += '   ' + infoData[p].name + '\n';
                            pciTitle += '      ' + i18n['KCHVMED6001M'] + ' ' + infoData[p].interface;
                            pciTitle += ', ' + i18n['KCHVMED6002M'] + ' ' + infoData[p].address;
                            pciTitle += ', ' + i18n['KCHVMED6003M'] + ' ' + infoData[p].link_type + '\n';
                        } else if (infoData[p].device_type === 'storage') {
                            haveCompanions = true;
                            pciTitle += '   ' + infoData[p].name + '\n';
                            pciTitle += '      ' + i18n['KCHVMED6004M'] + ' ' + infoData[p].block;
                            pciTitle += ', ' + i18n['KCHVMED6005M'] + ' ' + infoData[p].drive_type;
                            pciTitle += ', ' + i18n['KCHVMED6006M'] + ' ' + infoData[p].model + '\n';
                        }
                    }
                });
                $('#form-guest-edit-pci > .wok-mask').fadeOut(300, function() {});
                $('html').removeClass('in-progress');

                var settings = {
                    title: i18n['KCHVMED6012M'],
                    content: pciTitle,
                    confirm: i18n['KCHAPI6002M'],
                    cancel: i18n['KCHAPI6003M']
                };

                if (haveCompanions) {
                    wok.confirm(settings, function() {
                        kimchi.addVMPCIDevice(kimchi.selectedGuest, {
                            name: id
                        }, function(task) {
                            getOngoingAttachingDevices(task);
                        }, function(err) {
                            wok.message.error(err.responseJSON.reason, '#alert-modal-container');
                        });
                    });
                } else {
                    kimchi.addVMPCIDevice(kimchi.selectedGuest, {
                        name: id
                    }, function(task) {
                        getOngoingAttachingDevices(task);
                    }, function(err) {
                        wok.message.error(err.responseJSON.reason, '#alert-modal-container');
                    });
                }
            }
        });
    };

    var setupPCIDevice = function() {
        kimchi.getAvailableHostPCIDevices(function(hostPCIs) {
            kimchi.getVMPCIDevices(kimchi.selectedGuest, function(vmPCIs) {
                _generatePciDeviceHtml(hostPCIs, 'hostPCIs');
                _generatePciDeviceHtml(vmPCIs, 'vmPCIs');
                pciDeviceButtonHandler();
                $('#form-guest-edit-pci > .wok-mask').fadeOut(300, function() {});
            });
        });
        $('select', '#form-guest-edit-pci').change(function() {
            filterPCINodes($(this).val(), $('input#guest-edit-pci-filter', '#form-guest-edit-pci').val());
        });
        $('select', '#form-guest-edit-pci').selectpicker();
        $('input#guest-edit-pci-filter', '#form-guest-edit-pci').on('keyup', function() {
            filterPCINodes($('select', '#form-guest-edit-pci').val(), $(this).val());
        });
    };


    var setupSnapshot = function() {
        var currentSnapshot;
        var setCurrentSnapshot = function(aSnapshot) {
            if (!aSnapshot) {
                kimchi.getCurrentSnapshot(kimchi.selectedGuest, function(snapshot) {
                    if (snapshot && snapshot.name) {
                        aSnapshot = snapshot.name;
                    }
                }, null, true);
            }
            if (aSnapshot) {
                if (currentSnapshot) {
                    $(".fa.fa-check", "#" + currentSnapshot).addClass("hide");
                }
                $(".fa.fa-check", "#" + aSnapshot).removeClass("hide");
                currentSnapshot = aSnapshot;
            }
        };
        var addItem = function(data, container) {
            var itemNode = $.parseHTML(wok.substitute($('#snapshot-tmpl').html(), data));
            $("." + container, "#form-guest-edit-snapshot").append(itemNode);
            $(".delete", itemNode).on('click', function(evt) {
                evt.preventDefault();
                var item = $(this).parent().parent();
                $("button", "#form-guest-edit-snapshot").prop("disabled", true);
                kimchi.deleteSnapshot(kimchi.selectedGuest, item.prop("id"), function() {
                    item.remove();
                    setCurrentSnapshot();
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                }, function(data) {
                    wok.message.error(data.responseJSON.reason, '#alert-modal-container');
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                });
            });
            $(".revert", itemNode).on('click', function(evt) {
                evt.preventDefault();
                var item = $(this).parent().parent();
                $(".fa.fa-check", item).addClass("hide");
                $(".wok-loading", item).removeClass("hide");
                $("button", "#form-guest-edit-snapshot").prop("disabled", true);
                kimchi.revertSnapshot(kimchi.selectedGuest, item.prop("id"), function() {
                    $(".wok-loading", item).addClass("hide");
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                    setCurrentSnapshot(item.prop("id"));
                    kimchi.listVmsAuto();
                    wok.window.close();
                }, function(data) {
                    wok.message.error(data.responseJSON.reason, '#alert-modal-container');
                    $(".wok-loading-icon", item).addClass("hide");
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                });
            });
        };
        var addOngoingItem = function(task) {
            var uri = task.target_uri;
            addItem({
                name: uri.substring(uri.lastIndexOf('/') + 1, uri.length),
                created: "",
                listMode: "hide",
                createMode: ""
            }, 'task');
            if (kimchi.trackingTasks.indexOf(task.id) === -1) {
                kimchi.trackTask(task.id, function(task) {
                    listGeneratingSnapshots();
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                }, function(err) {
                    wok.message.error(err.message, '#alert-modal-container');
                    listGeneratingSnapshots();
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                });
            }
        };
        var listGeneratingSnapshots = function() {
            kimchi.getTasksByFilter('status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/snapshots/*'), function(tasks) {
                $(".task", "#form-guest-edit-snapshot").empty();
                for (var i = 0; i < tasks.length; i++) {
                    addOngoingItem(tasks[i]);
                }
                if (tasks.length === 0) {
                    listSnapshots();
                }
            });
        };
        var listSnapshots = function() {
            kimchi.listSnapshots(kimchi.selectedGuest, function(data) {
                $(".body", "#form-guest-edit-snapshot").empty();
                for (var i = 0; i < data.length; i++) {
                    data[i].created = new Date(data[i].created * 1000).toLocaleString();
                    data[i].createMode = "hide";
                    data[i].listMode = "";
                    addItem(data[i], 'body');
                }
                setCurrentSnapshot();
            });
        };
        listGeneratingSnapshots();
        $(".add", "#form-guest-edit-snapshot").on('click', function(evt) {
            evt.preventDefault();
            kimchi.createSnapshot(kimchi.selectedGuest, function(task) {
                $("button", "#form-guest-edit-snapshot").prop("disabled", true);
                addOngoingItem(task);
            });
        });
    };

    var setupBootOrder = function(guest) {
        var guestBootOrder = guest['bootorder'];
        var dev = ["cdrom", "hd", "network"];
        var excludedDev = dev.filter(function(e){return this.indexOf(e)<0;},guestBootOrder);

        $('#myList').empty();
        $.each(guestBootOrder, function(index, value) {
          item = $.parseHTML("<li class='list-group-item " + value + "' data-value=" + value + "><i class='fa fa-check'></i> " + value + "<span style='float: right; margin-top: -10px; padding: 0;'><button class='btn btn-link addBootOrderElem'><i class='fa fa-plus-circle'></i> Add</button><button class='btn btn-link deleteBootOrderElem'><i class='fa fa-minus-circle'></i> Remove</button></<span></li>");
          $('#myList').append(item);
          $('#myList .' + value + ' .addBootOrderElem').prop('disabled', true);
          $('#myList .' + value + ' .deleteBootOrderElem').prop('disabled', false);
        });
        if (excludedDev) {
          $.each(excludedDev, function(index, value) {
            item = $.parseHTML("<li class='list-group-item " + value + "' data-value=" + value + ">" + value + "<span style='float: right; margin-top: -10px; padding: 0;'><button class='btn btn-link addBootOrderElem'><i class='fa fa-plus-circle'></i> Add</button><button class='btn btn-link deleteBootOrderElem'><i class='fa fa-minus-circle'></i> Remove</button></<span></li>");
            $('#myList').append(item);
            $('#myList .' + value + ' .deleteBootOrderElem').prop('disabled', true);
          });
        }

        if (guestBootOrder.length == 1) {
          $('#myList .deleteBootOrderElem').prop('disabled', true);
        }

        $('.boot-order').sortable({
            items: 'li',
            cursor: 'move',
            opacity: 0.6,
            containment: "parent",
            start: function(event, ui) {
                $(this).addClass('focus');
            },
            stop: function(event, ui) {
                $(this).removeClass('focus');
            },
            change: function(event, ui) {
                // callback once started changing order
            },
            update: function(event, ui) {
                // callback once finished order
                $(saveButton).prop('disabled', false);
                bootOrderOptions = [];
                $("#myList li").each(function() {
                    bootOrderOptions.push($(this).attr("data-value").toLowerCase())
                });
                bootOrderOptions.forEach(function(entry) {
                    console.log(entry);
                });
                var data = {
                    bootorder: bootOrderOptions
                };
            }
        });

        $(".deleteBootOrderElem").on('click', function(evt) {
            evt.preventDefault();
            var item = $(this).parent().parent().attr("data-value").toLowerCase();
            var index = guestBootOrder.indexOf(item);

            $('.' + item + ' i.fa.fa-check').replaceWith('');
            $('#myList .' + item + ' .deleteBootOrderElem').prop('disabled', true);
            $('#myList .' + item + ' .addBootOrderElem').prop('disabled', false);

            if (index !== -1) {
              guestBootOrder.splice(index, 1);
            }
            if (guestBootOrder.length == 1) {
              $('#myList .deleteBootOrderElem').prop('disabled', true);
            }
            var data = {
                bootorder: guestBootOrder
            };
        });

        $(".addBootOrderElem").on('click', function(evt) {
            evt.preventDefault();
            var item = $(this).parent().parent().attr("data-value").toLowerCase();
            var index = guestBootOrder.indexOf(item);

            $('.' + item).prepend("<i class='fa fa-check'></i> ");
            $('#myList .' + item + ' .addBootOrderElem').prop('disabled', true);
            $('#myList .' + item + ' .deleteBootOrderElem').prop('disabled', false);

            guestBootOrder.push(item);

            if (guestBootOrder.length > 1) {
              $('#myList .deleteBootOrderElem').prop('disabled', false);
            }
            var data = {
                bootorder: guestBootOrder
            };
        });
    };

    var initContent = function(guest) {
        guest['icon'] = guest['icon'] || 'plugins/kimchi/images/icon-vm.png';
        $('#form-guest-edit-general').fillWithObject(guest);
        $('#guest-edit-memory-textbox').val(parseInt(guest.memory.current));
        $('#guest-edit-max-memory-textbox').val(parseInt(guest.memory.maxmemory));
        $("#enableGuestAutostart").prop('checked', parseInt(guest.autostart));
        kimchi.thisVMState = guest['state'];
        refreshCDROMs();
        $('#guest-edit-attach-cdrom-button').on('click', function(event) {
            event.preventDefault();
            wok.window.open('plugins/kimchi/guest-storage-add.html', 'extendCreateStorage');
        });
        if ((kimchi.thisVMState === "running") || (kimchi.thisVMState === "paused")) {
            if (kimchi.capabilities.mem_hotplug_support) {
                $("#form-guest-edit-general input").not("#guest-edit-memory-textbox").not("#enableGuestAutostart").prop("disabled", true);
            } else {
                $("#form-guest-edit-general input").not("#enableGuestAutostart").prop("disabled", true);
            }
        }
        if (! kimchi.capabilities.mem_hotplug_support) {
            $("#guest-edit-max-memory-textbox").prop("disabled", true);
            $("#guest-edit-memory-hotplug-unsupported").removeClass('hidden');
        }

        $('#guest-show-max-memory').on('click', function(e) {
            e.preventDefault;
            $('#guest-max-memory-panel').slideToggle();
            var text = $('#guest-show-max-memory span.text').text();
            $('#guest-show-max-memory span.text').text(text == i18n['KCHVMED6008M'] ? i18n['KCHVMED6009M'] : i18n['KCHVMED6008M']);
            $('#guest-show-max-memory i.fa').toggleClass('fa-plus-circle fa-minus-circle');
        });

        if ((kimchi.thisVMState !== "running") && (kimchi.thisVMState !== "paused")) {
            $("#guest-edit-memory-textbox").bind('keyup blur', function(e) {
                $('#guest-edit-max-memory-textbox').val($(this).val());
            });
        }

        if(kimchi.hostarch === s390xArch){
            var consoleData = guest.console ? guest.console : '';
            $('#guest-edit-console').val(consoleData);

            if (kimchi.thisVMState === "shutoff") {
                $('#guest-edit-console').prop('disabled', false);
            }else{
                $('#guest-edit-console').prop('disabled', true);
            }
            $('#guest-console-panel').show();
            $('#guest-edit-console').selectpicker();
        }

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
        setupPermission();
        setupPCIDevice();
        setupSnapshot();
        setupBootOrder(guest);

        kimchi.init_processor_tab(guest.cpu_info, $(saveButton));
        if ((kimchi.thisVMState === "running") || (kimchi.thisVMState === "paused")) {
            $('#guest-edit-max-processor-textbox').attr("disabled", true);
            $('#sockets').attr("disabled", true);
            $('#cores').attr("disabled", true);
            $('#threads').attr("disabled", true);

            $("#topology-checkbox").hide();
            $("#settings-readonly-help").removeClass('hidden');
        }

        wok.topic('kimchi/vmCDROMAttached').subscribe(onAttached);
        wok.topic('kimchi/vmCDROMReplaced').subscribe(onReplaced);
        wok.topic('kimchi/vmCDROMDetached').subscribe(onDetached);

        kimchi.clearGuestEdit = function() {
            wok.topic('kimchi/vmCDROMAttached').unsubscribe(onAttached);
            wok.topic('kimchi/vmCDROMReplaced').unsubscribe(onReplaced);
            wok.topic('kimchi/vmCDROMDetached').unsubscribe(onDetached);
        };
    };

    kimchi.retrieveVM(kimchi.selectedGuest, initContent);

    var generalSubmit = function(event) {
        kimchi.retrieveVM(kimchi.selectedGuest, function(org) {
            $(saveButton).prop('disabled', true);
            var data = $('#form-guest-edit-general').serializeObject();
            data['autostart'] = $("#enableGuestAutostart").prop('checked');
            data['memory'] = {current: Number(data['memory-ui']), maxmemory: Number(data['max-memory'])};

            var changedFields = {};
            for (var key in data) {
                valueFromUI = data[key];
                if (valueFromUI instanceof Object) {
                    // Compare if Objects of original and data are identical
                    // Handle special case when key is memory and guest is running as valueFromUI will return a null for max mem
                    // since it is disabled;
                    if (kimchi.thisVMState === 'running' || kimchi.thisVMState === 'paused') {
                        if (key === 'memory') {
                            // Replace valueFromUI of max mem with one from original as otherwise the value is undefined
                            data['memory']['maxmemory'] = org.memory.maxmemory;
                        }
                    }
                    // NOTE:  Be aware of using this comparison as the order of the properties matter
                    if (JSON.stringify(valueFromUI) !== JSON.stringify(org[key])) {
                        changedFields[key] = valueFromUI;
                    }
                } else {
                    if (org[key] !== undefined) {
                        if (data[key] != org[key]) {
                            changedFields[key] = valueFromUI;
                        }
                    }
                }
            }
            var origMem = Number(org.memory.current);
            var origMaxMem = Number(org.memory.maxmemory);
            var currentMem = data['memory-ui'];
            var currentMaxMem = data['max-memory'];

            if ('memory' in changedFields) {
                if (currentMaxMem !== undefined) {
                    currentMaxMem = Number(currentMaxMem);
                    if (currentMaxMem === origMaxMem) {
                        delete changedFields.memory.maxmemory;
                    }
                } else {
                    delete changedFields.memory.maxmemory;
                }
                if (currentMem !== undefined) {
                    currentMem = Number(currentMem);
                    if (kimchi.thisVMState === 'running' || kimchi.thisVMState === 'paused') {
                        // Compare to original max mem since current max mem is undefined in UI due to being disabled
                        if (currentMem > origMaxMem) {
                            wok.message.error(i18n['KCHVM0002E'], '#alert-modal-container');
                            $(saveButton).prop('disabled', false);
                            return;
                        }
                    }
                    if (currentMem === origMem) {
                        delete changedFields.memory.current;
                    }
                } else {
                    delete changedFields.memory.current;
                }
            }

            checkedValue = [];
            $("#myList i.fa.fa-check").each(function() {
              checkedValue.push($(this).parent().attr("data-value").toLowerCase());
            });
            changedFields.bootorder = checkedValue;

            kimchi.updateVM(kimchi.selectedGuest, changedFields, function() {
                kimchi.listVmsAuto();
                wok.window.close();
            }, function(err) {
                wok.message.error(err.responseJSON.reason, '#alert-modal-container');
                $(saveButton).prop('disabled', false);
            });

        });
    };

    var permissionSubmit = function(event) {
        var content = {
            users: [],
            groups: []
        };
        authType = wok.config['auth'];
        if (authType === 'pam') {
            $("#permission-sel-users").children().each(function() {
                content.users.push($("label", this).text());
            });
            $("#permission-sel-groups").children().each(function() {
                content.groups.push($("label", this).text());
            });
            kimchi.updateVM(kimchi.selectedGuest, content, function() {
                wok.window.close();
            });
        } else if (authType === 'ldap') {
            $(saveButton).prop('disabled', true);
            var errors = 0;

            $(".body", "#form-guest-edit-permission .ldap").children().each(function() {
                var elem = $(this);
                content.users.push(elem.attr("id"));

                if (!$('input', elem).hasClass('hide')) {
                    var user = {
                        'user_id': $(this).attr("id")
                    };
                    kimchi.getUserById(user, null, function(data) {
                        errors += 1;
                        $("input", elem).addClass("checked");
                    });
                }
            });
            if (errors === 0) {
                kimchi.updateVM(kimchi.selectedGuest, content, function() {
                    wok.window.close();
                });
            } else {
                $(saveButton).prop('disabled', false);
            }
        }
    };

    var processorSubmit = function(event) {
        kimchi.retrieveVM(kimchi.selectedGuest, function(org) {
            $(saveButton).prop('disabled', true);
            var data = {};

            var cpu = parseInt($('#vcpus').val());
            var maxCpu = parseInt($('#guest-edit-max-processor-textbox').val());
            var maxCpuFinal = cpu;
            if (maxCpu >= cpu) {
                maxCpuFinal = maxCpu;
            }
            if (kimchi.thisVMState === 'running' || kimchi.thisVMState === 'paused') {
                data['cpu_info'] = {vcpus: cpu};
            } else {
                if ($("input:checkbox", "#form-edit-processor").prop("checked")) {
                    data['cpu_info'] = {
                        vcpus: cpu,
                        maxvcpus: maxCpuFinal,
                        topology: {
                            sockets: parseInt($("#sockets").val()),
                            cores: parseInt($("#cores").val()),
                            threads: parseInt($("#threads").val())
                        }
                    };
                } else {
                    data['cpu_info'] = {
                        vcpus: cpu,
                        maxvcpus: maxCpuFinal,
                        topology: {}
                    };
                }
            }

            kimchi.updateVM(kimchi.selectedGuest, data, function() {
                kimchi.listVmsAuto();
                wok.window.close();
            }, function(err) {
                wok.message.error(err.responseJSON.reason, '#alert-modal-container');
                $(saveButton).prop('disabled', false);
            });
        });
    };

    if(kimchi.hostarch === s390xArch){
        $('#guest-edit-window ul li a[data-id="form-guest-edit-pci"],a[data-id="form-guest-edit-snapshot"]').parent().hide();
    }
};
