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

kimchi.NETWORK_TYPE_BRIDGE = "bridged";

kimchi.initNetwork = function() {
    if(wok.tabMode['network'] === 'admin') {
        $('.tools').attr('style','display');
        $('#networkGrid .wok-nw-grid-header span:last-child').attr('style','display');
        kimchi.initNetworkCreation();
    }
    kimchi.initNetworkListView();
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
        $('#networkGrid').dataGrid({enableSorting: false});
        $('input', $('.grid-control', '#network-content-container')).on('keyup', function(){
            $('#networkGrid').dataGrid('filter', $(this).val());
        });
    });
};

kimchi.addNetworkItem = function(network) {
    var itemNode = $.parseHTML(kimchi.getNetworkItemHtml(network));
    $("#networkBody").append(itemNode);
    if(wok.tabMode["network"] === "admin") {
        $(".column-action").attr("style","display");
    }
    kimchi.addNetworkActions(network);
    return itemNode;
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

    var disable_in_use = network.in_use ? "disabled" : "";
    var networkItem = wok.substitute($('#networkItem').html(), {
        name : network.name,
        state : network.state,
        type : network.type,
        interface: network.interface,
        addrSpace : network.addrSpace,
        startClass : network.state === "up" ? "wok-hide-action-item" : "",
        stopClass : network.state === "down" ? "wok-hide-action-item" : disable_in_use,
        stopDisabled : network.in_use ? "disabled" : "",
        deleteClass : network.state === "up" || network.in_use ? "disabled" : "",
        deleteDisabled: network.state === "up" || network.in_use ? "disabled" : ""
    });
    return networkItem;
};

kimchi.stopNetwork = function(network,menu) {
    $(".network-state", $("#" + wok.escapeStr(network.name))).switchClass("up", "loading");
    $("[nwAct='stop']", menu).addClass("disabled");
    kimchi.toggleNetwork(network.name, false, function() {
        $("[nwAct='start']", menu).removeClass("wok-hide-action-item");
        $("[nwAct='stop']", menu).addClass("wok-hide-action-item");
        $("[nwAct='stop']", menu).removeClass("disabled");
        if (!network.in_use) {
            $("[nwAct='delete']", menu).removeClass("disabled");
            $(":first-child", $("[nwAct='delete']", menu)).removeAttr("disabled");
        }
        $(".network-state", $("#" + wok.escapeStr(network.name))).switchClass("loading", "down");
    }, function(err) {
        $(".network-state", $("#" + wok.escapeStr(network.name))).switchClass("loading", "up");
        if (!network.in_use) {
            $("[nwAct='stop']", menu).removeClass("disabled");
        }
        wok.message.error(err.responseJSON.reason);
    });
}

kimchi.addNetworkActions = function(network) {
    //$(".dropdown-menu", "#" + wok.escapeStr(network.name)).menu();

    $('#' + wok.escapeStr(network.name)).on('click', '.dropdown-menu li', function(evt) {
        var menu = $(evt.currentTarget).parent();
        if ($(evt.currentTarget).attr("nwAct") === "start") {
            $(".network-state", $("#" + wok.escapeStr(network.name))).switchClass("down", "nw-loading");
            $("[nwAct='start']", menu).addClass("disabled");
            $("[nwAct='delete']", menu).addClass("disabled");
            $(":first-child", $("[nwAct='delete']", menu)).attr("disabled", true);
            kimchi.toggleNetwork(network.name, true, function() {
                $("[nwAct='start']", menu).addClass("wok-hide-action-item");
                $("[nwAct='start']", menu).removeClass("disabled");
                $("[nwAct='stop']", menu).removeClass("wok-hide-action-item");
                network.state = "up";
                if (network.in_use) {
                    $("[nwAct='stop']", menu).addClass("disabled");
                }
                $(".network-state", $("#" + wok.escapeStr(network.name))).switchClass("nw-loading", "up");
            }, function(err) {
                $(".network-state", $("#" + wok.escapeStr(network.name))).switchClass("nw-loading","down");
                $("[nwAct='start']", menu).removeClass("disabled");
                if (!network.in_use) {
                    $("[nwAct='delete']", menu).removeClass("disabled");
                }
                $(":first-child", $("[nwAct='delete']", menu)).removeAttr("disabled");
                wok.message.error(err.responseJSON.reason);
            });
        } else if ($(evt.currentTarget).attr("nwAct") === "stop") {
            if (network.in_use) {
                return false;
            }
            if (!network.persistent) {
                var settings = {
                    title : i18n['KCHAPI6001M'],
                    content : i18n['KCHNET6004M'],
                    confirm : i18n['KCHAPI6002M'],
                    cancel : i18n['KCHAPI6003M']
                };
                wok.confirm(settings, function() {
                    kimchi.stopNetwork(network, menu);
                    $('#networkGrid').dataGrid('deleteRow', $(evt.currentTarget).parents(".row"));
                }, null);
            }
            else {
                kimchi.stopNetwork(network, menu);
                network.state = "down";
            }
        } else if ($(evt.currentTarget).attr("nwAct") === "delete") {
            if (network.state === "up" || network.in_use) {
                return false;
            }
            wok.confirm({
                title : i18n['KCHAPI6006M'],
                content : i18n['KCHNET6002M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            }, function() {
                kimchi.deleteNetwork(network.name, function() {
                    $('#networkGrid').dataGrid('deleteRow', $(evt.currentTarget).parents(".row"));
                });
            }, null);
        }
    });

    //$("#networkBody .column-action .dropdown.menu-flat").button();

};

kimchi.initNetworkCreation = function() {
    $("#networkAdd").on("click", function() {
        wok.window.open('plugins/kimchi/network-add.html');
    });
};
