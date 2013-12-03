/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 * Yu Xin Huo <huoyuxin@linux.vnet.ibm.com>
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
}

kimchi.initNetworkListView = function() {
    kimchi.listNetworks(function(data) {
        for (var i = 0; i < data.length; i++) {
            var network = {
                name : data[i].name,
                state : data[i].state === "active" ? "up" : "down"
            };
            if (data[i].connection === "bridge") {
                network.type = kimchi.NETWORK_TYPE_BRIDGE;
            } else {
                network.type = data[i].connection;
            }
            network.interface = data[i].interface ? data[i].interface : null;
            network.addrSpace = data[i].subnet ? data[i].subnet : null;
            kimchi.addNetworkItem(network);
        }
    });
}

kimchi.addNetworkItem = function(network) {
    $("#networkBody").append(kimchi.getNetworkItemHtml(network));
    kimchi.addNetworkActions(network);
}

kimchi.getNetworkItemHtml = function(network) {
    if(!network.interface) {
        network.interface = i18n["value_unavailable"];
    }
    if(!network.addrSpace) {
        network.addrSpace = i18n["value_unavailable"];
    }
    if(i18n["network_type_" + network.type]) {
        network.type = i18n["network_type_" + network.type];
    }
    var networkItem = kimchi.template($('#networkItem').html(), {
        name : network.name,
        state : network.state,
        type : network.type,
        interface: network.interface,
        addrSpace : network.addrSpace,
        startClass : network.state === "up" ? "hide-action-item" : "",
        stopClass : network.state === "down" ? "hide-action-item" : "",
    });
    return networkItem;
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
                kimchi.toggleNetwork(network.name, true, function() {
                    $("[nwAct='start']", menu).addClass("hide-action-item");
                    $("[nwAct='stop']", menu).removeClass("hide-action-item");
                    $(".network-state", $("#" + network.name)).switchClass("down", "up");
                });
            } else if ($(evt.currentTarget).attr("nwAct") === "stop") {
                kimchi.toggleNetwork(network.name, false, function() {
                    $("[nwAct='start']", menu).removeClass("hide-action-item");
                    $("[nwAct='stop']", menu).addClass("hide-action-item");
                    $(".network-state", $("#" + network.name)).switchClass("up", "down");
                });
            }
        }
    });
    $(".column-action", "#" + network.name).children(":first").button({
        icons : {
            secondary : "arrow"
        }
    }).click(function() {
        $(".menu-container", "#" + network.name).toggle();
        window.scrollBy(0, 150);
    });
    $(".menu-container", "#" + network.name).mouseleave(function() {
        $(".menu-container", "#" + network.name).toggle(false);
    });
}
