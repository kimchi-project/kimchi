/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2015
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

    $('#guest-edit-window a[data-toggle="tab"]').on('show.bs.tab', function(tab) {
        tab.target // newly activated tab
        tab.relatedTarget // previous active tab
        var display_list = null;
        if (kimchi.thisVMState === "running") {
            display_list = ['form-guest-edit-permission'];
        } else {
            display_list = ['form-guest-edit-general', 'form-guest-edit-permission'];
        }
        $(saveButton).prop('disabled', true);
        formTargetId = $(tab.target).data('id');
        var deactivated = $('form#' + formTargetId);
        if (display_list.indexOf($(deactivated).attr('id')) >= 0) {
            $(saveButton).prop('disabled', false);
        }
    });

    var submitForm = function(event) {

        // tap map, "general": 0, "storage": 1, "interface": 2, "permission": 3, "password": 4
        var submit_map = {
            0: generalSubmit,
            3: permissionSubmit
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
            if ($(this).data('type') == "disk")
                settings['content'] = i18n['KCHVMCD6009M'];

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
            $("#label-mac-" + itemId, item).toggleClass("hide", on);
            $("#edit-mac-" + itemId, item).toggleClass("hide", !on);
            $("#label-network-" + itemId, item).toggleClass("hide", false);
            $("select", item).toggleClass("hide", true);
            $(".bootstrap-select", item).toggleClass("hide", true);
            $(".action-area", item).toggleClass("hide");
        };
        var addItem = function(data) {
            if (data.id == -1) {
                data.id = $('#form-guest-edit-interface > .body').children().size()
            }
            if (data.ips == "" || data.ips == null) {
                data.ips = i18n["KCHNET6001M"];
            } else {
                data.ips = data.ips;
            }
            var itemNode = $.parseHTML(wok.substitute($('#interface-tmpl').html(), data));
            $(".body", "#form-guest-edit-interface").append(itemNode);
            $("select", itemNode).append(networkOptions);
            $("select", itemNode).selectpicker();
            if (data.network !== "") {
                $("select", itemNode).val(data.network);
            }
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
                var interface = {
                    network: $("select", item).val(),
                        type: "network",
                        mac: $(":text", item).val(),
                        ips: $(".ipText", item).val()
                };
                var postUpdate = function(mac) {
                    $("#label-network-" + data.id, item).text(interface.network);
                    $("#label-mac-" + data.id, item).text(mac);
                    $("#edit-mac-" + data.id, item).val(mac);
                    toggleEdit(item, false, data.id);
                };
                if (item.prop("id") == "") {
                    kimchi.createGuestInterface(kimchi.selectedGuest, interface, function(data) {
                        item.prop("id", data.mac);
                        postUpdate(data.mac);
                    });
                } else {
                    if (item.prop('id') == interface.mac) {
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
        };
        var networkOptions = "";
        kimchi.listNetworks(function(data) {
            for (var i = 0; i < data.length; i++) {
                var isSlected = i == 0 ? " selected" : "";
                networkOptions += "<option" + isSlected + ">" + data[i].name + "</option>";
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

            if (data.checked == true) {
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
        authType = kimchi.capabilities['auth']
        if (authType == 'pam') {
            $("#form-guest-edit-permission .ldap").hide();
            kimchi.retrieveVM(kimchi.selectedGuest, function(vm) {
                kimchi.getUsers(function(users) {
                    kimchi.getGroups(function(groups) {
                        var subArray = function(a1, a2) { //a1-a2
                            for (var i = 0; i < a2.length; i++) {
                                for (var j = 0; j < a1.length; j++) {
                                    if (a2[i] == a1[j]) {
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
        } else if (authType == 'ldap') {
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
                $(this).css("display", $("label", this).text().indexOf(key) == -1 ? "none" : "");
            });
        }
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
    }

    var filterPCINodes = function(group, text, targetName) {
        text = text.toLowerCase();
        targetName = targetName.toLowerCase();
        $('.body', '#form-guest-edit-pci').children().each(function() {
            var currentName = $('.name', this).text().toLowerCase();
            var textFilter = currentName.indexOf(text) !== -1;
            textFilter = textFilter || $('.product', this).text().toLowerCase().indexOf(text) !== -1;
            textFilter = textFilter || $('.vendor', this).text().toLowerCase().indexOf(text) !== -1;
            var display = 'none';
            var itemGroup = $('button i', this);
            if (textFilter) {
                if (group === 'all') {
                    display = '';
                } else if (group === 'toAdd' && itemGroup.hasClass('fa-power-off')) {
                    display = '';
                } else if (group === 'added' && itemGroup.hasClass('fa-ban')) {
                    display = '';
                }
            }
            $(this).css('display', display);
        });
    };
    var setupPCIDevice = function() {
        kimchi.getAvailableHostPCIDevices(function(hostPCIs) {
            kimchi.getVMPCIDevices(kimchi.selectedGuest, function(vmPCIs) {
                setupNode(hostPCIs, 'fa-power-off');
                setupNode(vmPCIs, 'fa-ban');
            });
        });
        $('select', '#form-guest-edit-pci').change(function() {
            filterPCINodes($(this).val(), $('input', '#form-guest-edit-pci').val(), '');
        });
        $('select', '#form-guest-edit-pci').selectpicker();
        $('input', '#form-guest-edit-pci').on('keyup', function() {
            filterPCINodes($('select', '#form-guest-edit-pci').val(), $(this).val(), '');
        });
    };
    var setupNode = function(arrPCIDevices, iconClass) {
        var pciEnabled = kimchi.capabilities.kernel_vfio;
        var pciDeviceName, pciDeviceProduct, pciDeviceProductDesc, pciDeviceVendor, pciDeviceVendorDesc, pciDeviceStatus;
        for (var i = 0; i < arrPCIDevices.length; i++) {
            pciDeviceName = arrPCIDevices[i].name;
            pciDeviceProduct = arrPCIDevices[i].product;
            pciDeviceVendor = arrPCIDevices[i].vendor;
            pciDeviceStatus = (iconClass === 'fa-ban') ? 'enabled' : 'disabled';
            if (pciDeviceProduct !== null) {
                pciDeviceProductDesc = pciDeviceProduct.description;
            }
            if (pciDeviceVendor !== null) {
                pciDeviceVendorDesc = pciDeviceVendor.description;
            }
            var itemNode = $.parseHTML(wok.substitute($('#pci-tmpl').html(), {
                status: pciDeviceStatus,
                name: pciDeviceName,
                product: pciDeviceProductDesc,
                vendor: pciDeviceVendorDesc
            }));
            $('.body', '#form-guest-edit-pci').append(itemNode);
            pciEnabled || $('button', itemNode).remove();
            $('button i', itemNode).addClass(iconClass);
            $('button', itemNode).on('click', function(event) {
                event.preventDefault();
                var obj = $(this);
                var objIcon = obj.find('i');
                var id = obj.parent().parent().attr('id');
                if (objIcon.hasClass('fa-ban')) {
                    kimchi.removeVMPCIDevice(kimchi.selectedGuest, id, function() {
                        kimchi.getAvailableHostPCIDevices(function(arrPCIDevices1) {
                            kimchi.getVMPCIDevices(kimchi.selectedGuest, function(vmPCIs1) {
                                for (var k = 0; k < arrPCIDevices1.length; k++) {
                                    $('button i', '#' + arrPCIDevices1[k].name).removeClass('fa-ban').addClass('fa-power-off');
                                }
                                for (var k = 0; k < vmPCIs1.length; k++) {
                                    $('button i', '#' + arrPCIDevices1[k].name).removeClass('fa-power-off').addClass('fa-ban');
                                }
                            });
                        });
                        //id is for the object that is being added back to the available PCI devices
                        filterPCINodes($('select', '#form-guest-edit-pci').val(), $('input', '#form-guest-edit-pci').val(), id);
                    });
                } else {
                    kimchi.addVMPCIDevice(kimchi.selectedGuest, {
                        name: id
                    }, function() {
                        kimchi.getVMPCIDevices(kimchi.selectedGuest, function(vmPCIs1) {
                            for (var k = 0; k < vmPCIs1.length; k++) {
                                $('button i', '#' + arrPCIDevices1[k].name).removeClass('fa-power-off').addClass('fa-ban');
                            }
                        });
                        //id is for the object that is being removed from the available PCI devices
                        filterPCINodes($('select', '#form-guest-edit-pci').val(), $('input', '#form-guest-edit-pci').val(), id);
                    });
                }
            });
            kimchi.getPCIDeviceCompanions(pciDeviceName, function(infoData) {
                var pciTitle = i18n['KCHVMED6007M'] + '\n';
                var haveCompanions = false;
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
                for (var q = 0; q < infoData.length; q++) {
                    haveCompanions && $('.name', '#' + infoData[q].parent).attr('title', pciTitle);
                    haveCompanions && $('.product', '#' + infoData[q].parent).attr('title', pciTitle);
                    haveCompanions && $('.vendor', '#' + infoData[q].parent).attr('title', pciTitle);
                }
            });
        }
    };

    var setupSnapshot = function() {
        var currentSnapshot;
        var setCurrentSnapshot = function(aSnapshot) {
            if (!aSnapshot)
                kimchi.getCurrentSnapshot(kimchi.selectedGuest, function(snapshot) {
                    if (snapshot && snapshot.name) aSnapshot = snapshot.name;
                }, null, true);
            if (aSnapshot) {
                if (currentSnapshot) $(".fa.fa-check", "#" + currentSnapshot).addClass("hide");
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
            if (kimchi.trackingTasks.indexOf(task.id) == -1)
                kimchi.trackTask(task.id, function(task) {
                    listGeneratingSnapshots();
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                }, function(err) {
                    wok.message.error(err.message, '#alert-modal-container');
                    listGeneratingSnapshots();
                    $("button", "#form-guest-edit-snapshot").prop("disabled", false);
                });
        };
        var listGeneratingSnapshots = function() {
            kimchi.getTasksByFilter('status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/snapshots/*'), function(tasks) {
                $(".task", "#form-guest-edit-snapshot").empty();
                for (var i = 0; i < tasks.length; i++) {
                    addOngoingItem(tasks[i]);
                }
                if (tasks.length == 0) listSnapshots();
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
        if (kimchi.thisVMState == "running") $("button", "#form-guest-edit-snapshot").remove();
    };

    var initContent = function(guest) {
        guest['icon'] = guest['icon'] || 'plugins/kimchi/images/icon-vm.png';
        $('#form-guest-edit-general').fillWithObject(guest);
        kimchi.thisVMState = guest['state'];
        refreshCDROMs();
        $('#guest-edit-attach-cdrom-button').on('click', function(event) {
            event.preventDefault();
            wok.window.open('plugins/kimchi/guest-storage-add.html', 'extendCreateStorage');
        });
        if ((kimchi.thisVMState === "running") || (kimchi.thisVMState === "paused")) {
            $("#form-guest-edit-general input").prop("disabled", true);
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
        $(saveButton).prop('disabled', true);
        var data = $('#form-guest-edit-general').serializeObject();
        if (data['memory'] != undefined) {
            data['memory'] = Number(data['memory']);
        }
        if (data['cpus'] != undefined) {
            data['cpus'] = Number(data['cpus']);
        }

        kimchi.updateVM(kimchi.selectedGuest, data, function() {
            kimchi.listVmsAuto();
            wok.window.close();
        }, function(err) {
            wok.message.error(err.responseJSON.reason, '#alert-modal-container');
            $(saveButton).prop('disabled', false);
        });
    }

    var permissionSubmit = function(event) {
        var content = {
            users: [],
            groups: []
        };
        authType = kimchi.capabilities['auth']
        if (authType == 'pam') {
            $("#permission-sel-users").children().each(function() {
                content.users.push($("label", this).text());
            });
            $("#permission-sel-groups").children().each(function() {
                content.groups.push($("label", this).text());
            });
            kimchi.updateVM(kimchi.selectedGuest, content, function() {
                wok.window.close();
            });
        } else if (authType == 'ldap') {
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
            if (errors == 0) {
                kimchi.updateVM(kimchi.selectedGuest, content, function() {
                    wok.window.close();
                });
            } else {
                $(saveButton).prop('disabled', false);
            }
        }
    }
};
