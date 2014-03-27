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

kimchi.NETWORK_TYPE_BRIDGE = "bridged";

kimchi.initNetwork = function() {
    kimchi.initNetworkListView();
    kimchi.initNetworkDialog();
    kimchi.initNetworkCreation();
    kimchi.initNetworkCleanup();
};

kimchi.initNetworkListView = function() {
    kimchi.listNetworks(function(data) {
        for (var i = 0; i < data.length; i++) {
            var network = {
                name : data[i].name,
                in_use : data[i].in_use,
                state : data[i].state === "active" ? "up" : "down"
            };
            if (data[i].connection === "bridge") {
                network.type = kimchi.NETWORK_TYPE_BRIDGE;
            } else {
                network.type = data[i].connection;
            }
            network.interface = data[i].interface ? data[i].interface : null;
            network.addrSpace = data[i].subnet ? data[i].subnet : null;
            network.persistent = data[i].persistent;
            kimchi.addNetworkItem(network);
        }
    });
};

kimchi.addNetworkItem = function(network) {
    $("#networkBody").append(kimchi.getNetworkItemHtml(network));
    kimchi.addNetworkActions(network);
};

kimchi.getNetworkItemHtml = function(network) {
    if(!network.interface) {
        network.interface = i18n["KCHNET6001M"];
    }
    if(!network.addrSpace) {
        network.addrSpace = i18n["KCHNET6001M"];
    }
    if(i18n["network_type_" + network.type]) {
        network.type = i18n["network_type_" + network.type];
    }

    var disable_in_use = network.in_use ? "ui-state-disabled" : "";
    var networkItem = kimchi.template($('#networkItem').html(), {
        name : network.name,
        state : network.state,
        type : network.type,
        interface: network.interface,
        addrSpace : network.addrSpace,
        startClass : network.state === "up" ? "hide-action-item" : "",
        stopClass : network.state === "down" ? "hide-action-item" : disable_in_use,
        stopDisabled : network.in_use ? "disabled" : "",
        deleteClass : network.state === "up" || network.in_use ? "ui-state-disabled" : "",
        deleteDisabled: network.state === "up" || network.in_use ? "disabled" : ""
    });
    return networkItem;
};

kimchi.stopNetwork = function(network,menu) {
    $(".network-state", $("#" + network.name)).switchClass("up", "nw-loading");
    $("[nwAct='stop']", menu).addClass("ui-state-disabled");
    kimchi.toggleNetwork(network.name, false, function() {
        $("[nwAct='start']", menu).removeClass("hide-action-item");
        $("[nwAct='stop']", menu).addClass("hide-action-item");
        $("[nwAct='stop']", menu).removeClass("ui-state-disabled");
        if (!network.in_use) {
            $("[nwAct='delete']", menu).removeClass("ui-state-disabled");
            $(":first-child", $("[nwAct='delete']", menu)).removeAttr("disabled");
        }
        $(".network-state", $("#" + network.name)).switchClass("nw-loading", "down");
    }, function(err) {
        $(".network-state", $("#" + network.name)).switchClass("nw-loading", "up");
        if (!network.in_use) {
            $("[nwAct='stop']", menu).removeClass("ui-state-disabled");
        }
        kimchi.message.error(err.responseJSON.reason);
    });
}

kimchi.addNetworkActions = function(network) {
    $(".menu-container", "#" + network.name).menu({
        position : {
            my : "left top",
            at : "left bottom",
            of : "#" + network.name
        },
        select : function(evt, ui) {
            $(".menu-container", "#" + network.name).toggle(false);
            var menu = $(evt.currentTarget).parent();
            if ($(evt.currentTarget).attr("nwAct") === "start") {
                $(".network-state", $("#" + network.name)).switchClass("down", "nw-loading");
                $("[nwAct='start']", menu).addClass("ui-state-disabled");
                $("[nwAct='delete']", menu).addClass("ui-state-disabled");
                $(":first-child", $("[nwAct='delete']", menu)).attr("disabled", true);
                kimchi.toggleNetwork(network.name, true, function() {
                    $("[nwAct='start']", menu).addClass("hide-action-item");
                    $("[nwAct='start']", menu).removeClass("ui-state-disabled");
                    $("[nwAct='stop']", menu).removeClass("hide-action-item");
                    if (network.in_use) {
                        $("[nwAct='stop']", menu).addClass("ui-state-disabled");
                    }
                    $(".network-state", $("#" + network.name)).switchClass("nw-loading", "up");
                }, function(err) {
                    $(".network-state", $("#" + network.name)).switchClass("nw-loading","down");
                    $("[nwAct='start']", menu).removeClass("ui-state-disabled");
                    if (!network.in_use) {
                        $("[nwAct='delete']", menu).removeClass("ui-state-disabled");
                    }
                    $(":first-child", $("[nwAct='delete']", menu)).removeAttr("disabled");
                    kimchi.message.error(err.responseJSON.reason);
                });
            } else if ($(evt.currentTarget).attr("nwAct") === "stop") {
                if (!network.persistent) {
                    var settings = {
                        title : i18n['KCHAPI6001M'],
                        content : i18n['KCHNET6004M'],
                        confirm : i18n['KCHAPI6002M'],
                        cancel : i18n['KCHAPI6003M']
                    };
                    kimchi.confirm(settings, function() {
                        kimchi.stopNetwork(network, menu);
                        $(evt.currentTarget).parents(".item").remove();
                    }, null);
                }
                else {
                    kimchi.stopNetwork(network, menu);
                }
            } else if ($(evt.currentTarget).attr("nwAct") === "delete") {
                kimchi.confirm({
                    title : i18n['KCHAPI6006M'],
                    content : i18n['KCHNET6002M'],
                    confirm : i18n['KCHAPI6002M'],
                    cancel : i18n['KCHAPI6003M']
                }, function() {
                    kimchi.deleteNetwork(network.name, function() {
                        $(evt.currentTarget).parents(".item").remove();
                    });
                }, null);
            }
        }
    });
    $(".column-action", "#" + network.name).children(":first").button({
        icons : {
            secondary : "action-button-icon"
        }
    }).click(function() {
        $(".menu-container", "#" + network.name).toggle();
        window.scrollBy(0, 150);
    });
    $(".menu-container", "#" + network.name).mouseleave(function() {
        $(".menu-container", "#" + network.name).toggle(false);
    });
};

kimchi.initNetworkCreation = function() {
    $("#networkAdd").on("click", function() {
        kimchi.openNetworkDialog(function() {
            var network = kimchi.getNetworkDialogValues();
            var data = {
                name : network.name,
                connection: network.type
            };
            if (network.type === kimchi.NETWORK_TYPE_BRIDGE) {
                data.connection = "bridge";
                data.interface = network.interface;
                if ($("#enableVlan").prop("checked")) {
                    data.vlan_id = network.vlan_id;
                    if (!(data.vlan_id >=1 && data.vlan_id <= 4094)) {
                        kimchi.message.error.code('KCHNET6001E');
                        return;
                    }
                }
            }
            kimchi.createNetwork(data, function(result) {
                network.state = result.state === "active" ? "up" : "down";
                network.interface = result.interface ? result.interface : i18n["KCHNET6001M"];
                network.addrSpace = result.subnet ? result.subnet : i18n["KCHNET6001M"];
                kimchi.addNetworkItem(network);
                $("#networkConfig").dialog("close");
            });
        });
    });
};

kimchi.initNetworkDialog = function() {

    buttonsObj= {};
    buttonsObj['id'] = "networkFormOk";
    buttonsObj['text'] = i18n.KCHAPI6005M;
    buttonsObj['class'] = "ui-button-primary";
    buttonsObj['disabled'] = true;
    buttonsObj['click'] = function() { };
    $("#networkConfig").dialog({
        autoOpen : false,
        modal : true,
        width : 600,
        draggable : false,
        resizable : false,
        closeText: "X",
        dialogClass : "network-ui-dialog remove-when-logged-off",
        open : function(){
            $(".ui-dialog-titlebar-close", $("#networkConfig").parent()).removeAttr("title");
        },
        beforeClose : function() {
            kimchi.cleanNetworkDialog();
        },
        buttons : [buttonsObj]
    });
    kimchi.setupNetworkFormEvent();
};

kimchi.openNetworkDialog = function(okCallback) {
    kimchi.getInterfaces(function(result) {
        var options = "";
        var nics = {};
        for (var i = 0; i < result.length; i++) {
            options += "<option value=" + result[i].name + ">" + result[i].name + "</option>";
            nics[result[i].name] = result[i];
        }
        $("#networkInterface").append(options);
        onChange = function() {
            if (nics[$("#networkInterface").val()].type === "bridge") {
                $("#enableVlan").prop("checked", false);
                $("#enableVlan").prop("disabled", true);
                $("#networkVlanID").val("");
                $("#networkVlanID").prop("disabled", true);
            } else {
                $("#enableVlan").prop("disabled", false);
            }
        };
        $("#networkInterface").on("change", onChange);
        onChange();
        kimchi.setDefaultNetworkType(result.length!==0);
    });
    $("#networkConfig").dialog({
        title : i18n.KCHNET6003M
    });
    $("#networkFormOk").on("click", function() {
        okCallback();
    });
    $("#enableVlan").on("click", function() {
        $("#networkVlanID").prop("disabled", !this.checked);
        if (!this.checked) {
            $("#networkVlanID").val("");
        }
    });
    $("#networkConfig").dialog("open");
};

kimchi.enableBridgeOptions = function(enable) {
    if (!enable) {
        $("#enableVlan").prop("checked", false);
        $("#networkVlanID").prop("disabled", true);
        $("#networkVlanID").val("");
        $("#networkInterface").val("");
        $("#bridge-options").slideUp(100);
    } else if (!$("#networkInterface").val()){
        $("#networkInterface").prop("selectedIndex", 0);
        $("#bridge-options").slideDown(100);
    }
};

kimchi.setDefaultNetworkType = function(isInterfaceAvail) {
    $("#networkTypeBri").prop("checked", isInterfaceAvail);
    $("#networkTypeBri").prop("disabled", !isInterfaceAvail);
    $("#networkTypeNat").prop("checked", !isInterfaceAvail);
    if (!isInterfaceAvail) {
        kimchi.enableBridgeOptions(false);
    } else {
        $("#bridge-options").slideDown(100);
    }
};

kimchi.getNetworkDialogValues = function() {
    var network = {
        name : $("#networkName").val(),
        type : $("input:radio[name=networkType]:checked").val()
    };
    if (network.type === kimchi.NETWORK_TYPE_BRIDGE) {
        network.interface = $("#networkInterface").val();
        network.vlan_id = parseInt($("#networkVlanID").val());
    }
    return network;
};

kimchi.cleanNetworkDialog = function() {
    $("#networkInterface").empty();
    $("input:text", "#networkConfig").val(null).removeClass("invalid-field");
    $("#networkTypeIso").prop("checked", false);
    $("#networkTypeNat").prop("checked", false);
    $("#networkTypeBri").prop("checked", false);
    $("#networkInterface").prop("disabled", false);
    $("#networkInterface option").removeAttr("selected").find(":first").attr("selected", "selected");
    $("#networkFormOk").off("click");
    $("#networkFormOk").button("disable");
    $("#networkVlanID").prop("disabled", true);
    $("#enableVlan").prop("checked", false);
};

kimchi.setupNetworkFormEvent = function() {
    $("#networkName").on("keyup", function(event) {
        $("#networkName").toggleClass("invalid-field", !$("#networkName").val().match(/^[a-zA-Z0-9_]+$/));
        kimchi.updateNetworkFormButton();
    });
    $("#networkTypeIso").on("click", function(event) {
        $("#networkInterface").prop("disabled", true);
        kimchi.enableBridgeOptions(false);
    });
    $("#networkTypeNat").on("click", function(event) {
        $("#networkInterface").prop("disabled", true);
        kimchi.enableBridgeOptions(false);
    });
    $("#networkTypeBri").on("click", function(event) {
        $("#networkInterface").prop("disabled", false);
        kimchi.enableBridgeOptions(true);
    });
};

kimchi.updateNetworkFormButton = function() {
    if($("#networkName").hasClass("invalid-field")){
        $("#networkFormOk").button("disable");
    }else{
        $("#networkFormOk").button("enable");
    }
};

kimchi.initNetworkCleanup = function() {
    $("#network-content").on("remove", function() {
        $("#networkConfig").dialog("destroy");
    });
};
