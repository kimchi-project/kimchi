/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2016
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

kimchi.network_edit_main = function() {
    var initNetwork = function(network) {
        var networkType = network['connection'];
        $('#bridgedContent').hide();
        $('#networkType').val(networkType);
        $('#networkName').val(kimchi.selectedNetwork);

        var subnetValue = network['subnet'];
        if (subnetValue === "") {
            $('#networkSubnetRange').val("unavailable");
        } else {
            $('#networkSubnetRange').val(subnetValue);
        }

        // Default to hide Subnet
        $('#subnetRange').hide();

        if(networkType === "nat" || networkType === "isolated") {
            //Show subnet/dhcp range
            $('#subnetRange').show();
        }

        if (networkType === kimchi.NETWORK_TYPE_MACVTAP ||
            networkType === kimchi.NETWORK_TYPE_PASSTHROUGH ||
            networkType === kimchi.NETWORK_TYPE_VEPA ||
            networkType === kimchi.NETWORK_TYPE_BRIDGED) {
            $('#bridgedContent').show();
            $('#networkDestination').show();
            $('#vlan').hide();
            if (networkType === kimchi.NETWORK_TYPE_BRIDGED) {
                //Now check if there's a vlan id and only show if one exists
                var netInterface = network['interfaces'];
                var netInterfaceParts = netInterface[0].split('-', 2);
                var netvlanID = netInterfaceParts[1];
                if (netvlanID !== undefined) {
                    //Show vlan ID field; do not show the checkbox
                    $('#vlan').show();
                    $('#vlan_chkbox').hide();
                    $('#vlan-enabled').show();
                    $('#networkVlanID').val(netvlanID);
                }
            }
        }

        kimchi.setupNetworkFormEventForEdit(network);
    };

    kimchi.retrieveNetwork(kimchi.selectedNetwork, initNetwork);

    var generalSubmit = function(event) {
        $('#networkFormOk').text(i18n['KCHAPI6010M']);
        $('#networkFormOk').prop('disabled', true);

        var data = $('#networkConfig').serializeObject();
        kimchi.updateNetworkValues();
    };

    $('#networkConfig').on('submit', generalSubmit);
    $('#networkFormOk').on('click', generalSubmit);
};

kimchi.setupNetworkFormEventForEdit = function(network) {
    var selectedType = network['connection'];
    if (selectedType === kimchi.NETWORK_TYPE_BRIDGED) {
        if (kimchi.capabilities && kimchi.capabilities.nm_running) {
          wok.message.warn(i18n['KCHNET6001W'],'#alert-modal-container');
        }
    }

    // Network name validation
    $("#networkName").on("keyup", function(event) {
        $("#networkName").toggleClass("invalid-field", !$("#networkName").val().match(/^[^\"\/]+$/));
        kimchi.updateNetworkFormButtonForEdit();
    });

    var loadIfaces = function(interfaceFilterArray){
        var buildInterfaceOpts = function(result) {
            var currentIfaces = network['interfaces'];
            for (var i = 0; i < currentIfaces.length; i++) {
                kimchi.getInterface(currentIfaces[i], function(iface) {
                    result.push(iface);
                } , null, true);
            }
            kimchi.createInterfacesOpts(result, interfaceFilterArray);

            for (var i = 0; i < currentIfaces.length; i++) {
                $("#networkDestinationID option[value='" + currentIfaces[i] + "']").attr('selected','selected');
            }
            $('#networkDestinationID').selectpicker('refresh');
        };

        var networkType = $("#networkType").val();
        if (networkType === kimchi.NETWORK_TYPE_VEPA) {
            kimchi.getVEPAInterfaces(buildInterfaceOpts);
        } else {
            kimchi.getInterfaces(buildInterfaceOpts);
        }
    }

    var selectedType = network['connection'];
    if(selectedType === kimchi.NETWORK_TYPE_MACVTAP ||
       selectedType === kimchi.NETWORK_TYPE_PASSTHROUGH ||
       selectedType === kimchi.NETWORK_TYPE_VEPA) {
        if (selectedType === kimchi.NETWORK_TYPE_MACVTAP) {
            $('#networkDestinationID').attr('multiple', false).data('liveSearch',false);
        } else {
            $('#networkDestinationID').attr('multiple', true);
            if($('#networkDestinationID option').length > 10 ) {
                $('#networkDestinationID').data('liveSearch',true);
            }
        }
        $('#networkDestinationID').selectpicker('destroy');

        loadIfaces(new Array("nic", "bonding"));
    } else {
        loadIfaces(undefined);
    }
};

kimchi.updateNetworkFormButtonForEdit = function() {
    if ($("#networkName").hasClass("invalid-field")) {
        $('#networkFormOk').prop('disabled', true);
    } else{
        $('#networkFormOk').prop('disabled', false);
    }
};

kimchi.getNetworkDialogValuesForEdit = function() {
    var network = {
        name : $("#networkName").val(),
        type : $("#networkType").val(),
        subnetRange: $("#networkSubnetRange").val(),
        interface: $("#networkDestinationID").val(),
        vlan_id: $("#networkVlanID").val()
    };
    if (network.type === kimchi.NETWORK_TYPE_BRIDGED) {
        if (network.vlan_id !== "") {
            network.vlan_id = parseInt($("#networkVlanID").val());
        }
    }
    return network;
};

kimchi.updateNetworkValues = function() {
    kimchi.retrieveNetwork(kimchi.selectedNetwork, function(settings) {
        var network = kimchi.getNetworkDialogValuesForEdit();
        var data = {
            name : network.name,
            subnet: network.subnetRange,
            interfaces: [ network.interface ],
            vlan_id: network.vlan_id
        };
        var originalDest = settings.interfaces;
        var updatedDest = $('#networkDestinationID').val();
        if (originalDest === updatedDest || updatedDest === null) {
            delete data['interfaces'];
        }
        if (network.type !== "nat" && network.type !== "isolated") {
            delete data['subnet'];
        } else { // either nat or isolated
            delete data['interfaces'];
            delete data['vlan_id'];
        }
        if (network.type === kimchi.NETWORK_TYPE_BRIDGED) {
            if (data.vlan_id === "") {
                delete data['vlan_id'];
            } else {
                data.vlan_id = parseInt($("#networkVlanID").val());
            }
        } else {
            delete data['vlan_id'];
        }

        // Just like in Add Network, VEPA connection - network.interface - is already an array
        if (network.type === kimchi.NETWORK_TYPE_VEPA || network.type === kimchi.NETWORK_TYPE_PASSTHROUGH) {
            if (network.interface !== null) {
                data.interfaces = network.interface;
            }
        }

        kimchi.updateNetwork(kimchi.selectedNetwork, data, function(result) {
            $('#' + kimchi.selectedNetwork).remove();
            network = result;
            network.type = result.connection;
            network.state = result.state === "active" ? "up" : "down";
            network.interface = result.interfaces ? result.interfaces[0] : i18n["KCHNET6001M"];
            network.addrSpace = result.subnet ? result.subnet : i18n["KCHNET6001M"];
            network.persistent = result.persistent;
            $('#networkGrid').dataGrid('addRow', kimchi.addNetworkItem(network));
            wok.window.close();
        }, function(settings) {
            wok.message.error(settings.responseJSON.reason,'#alert-modal-container');
            $('#networkFormOk').text(i18n['KCHAPI6007M']);
            $('#networkFormOk').prop('disabled', false);
        });
    });
};
