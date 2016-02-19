/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2015-2016
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

 kimchi.network_add_main = function() {
    kimchi.setupNetworkFormEvent();
    kimchi.openNetworkDialog();
};

kimchi.startNetworkCreation = function() {
    var errorCallback = function(){
        $("#networkFormOk").button("enable");
        $("#networkName").removeAttr("readonly");
        $("#networkVlanID").removeAttr("readonly");
        $("#networkFormOk").text(i18n.KCHAPI6005M);
    };
    var network = kimchi.getNetworkDialogValues();
    var data = {
        name : network.name,
        connection: network.type,
        interfaces: [ network.interface ],
        vlan_id: network.vlan_id
    };

    kimchi.createNetwork(data, function(result) {
        network.state = result.state === "active" ? "up" : "down";
        network.interface = result.interfaces ? result.interfaces[0] : i18n["KCHNET6001M"];
        network.addrSpace = result.subnet ? result.subnet : i18n["KCHNET6001M"];
        network.persistent = result.persistent;
        $('#networkGrid').dataGrid('addRow', kimchi.addNetworkItem(network));
        wok.window.close();
    }, function(data) {
        wok.message.error(data.responseJSON.reason,'#alert-modal-container');
        errorCallback();
    });
};

kimchi.openNetworkDialog = function(okCallback) {
    kimchi.loadInterfaces();

    $("#networkFormOk").on("click", function() {
        $("#networkFormOk").button("disable");
        $("#networkName").prop("readonly", "readonly");
        $("#networkVlanID").prop("readonly", "readonly");
        $("#networkFormOk").text(i18n.KCHAPI6008M);
        kimchi.startNetworkCreation();
    });
    $("#enableVlan").on("click", function() {
        $("#networkVlanID").prop("disabled", !this.checked);
        if (!this.checked) {
            $("#networkVlanID").val("");
        }
    });
};

kimchi.setDefaultNetworkType = function(isInterfaceAvail) {
    $("#networkType").selectpicker();
    if (!isInterfaceAvail) {
        kimchi.enableBridgeOptions(false);
        $("#networkBriDisabledLabel").removeClass('hidden');
    } else {
        $("#networkBriDisabledLabel").remove();
    }
};

kimchi.getNetworkDialogValues = function() {
    var network = {
        name : $("#networkName").val(),
        type : $("#networkType").val()
    };
    if (network.type === kimchi.NETWORK_TYPE_MACVTAP ||  network.type === kimchi.NETWORK_TYPE_VEPA) {
        network.interface = $("#networkDestinationID").val();
    }
    if (network.type === kimchi.NETWORK_TYPE_BRIDGED) {
        network.interface = $("#networkDestinationID").val();
        if ($("#enableVlan").prop("checked") && ($("#networkDestinationID").find(':selected').data('type') === 'nic' || $("#networkDestinationID").find(':selected').data('type') === 'bonding')) {
            network.vlan_id = parseInt($("#networkVlanID").val());
        }
    }
    return network;
};

kimchi.setupNetworkFormEvent = function() {
    if (kimchi.capabilities && kimchi.capabilities.nm_running) {
            wok.message.warn(i18n['KCHNET6001W'],'#alert-modal-container');
    }
    $('#bridgedContent').hide();
    $("#networkName").on("keyup", function(event) {
        $("#networkName").toggleClass("invalid-field", !$("#networkName").val().match(/^[^\"\/]+$/));
        kimchi.updateNetworkFormButton();
    });

    $('#networkType').on('change', function() {
        var selectedType = $("#networkType").val();
        if(selectedType === kimchi.NETWORK_TYPE_MACVTAP || selectedType === kimchi.NETWORK_TYPE_VEPA) {
            kimchi.loadInterfaces(new Array("nic", "bonding"));
        } else {
            kimchi.loadInterfaces();
        }
    });

    $('#networkDestinationID').on('change', function() {
        kimchi.changeNetworkDestination();
    });
};

kimchi.changeNetworkDestination = function() {
    var selectedType = $("#networkType").val();
    var selectedDestinationType = $("#networkDestinationID").find(':selected').data('type');
    if(selectedType ==  'isolated' ||  selectedType ==  'nat') {
        kimchi.enableBridgeOptions(false);
    } else {
        kimchi.enableBridgeOptions(true, selectedType, selectedDestinationType);
    }
}

kimchi.updateNetworkFormButton = function() {
    if($("#networkName").hasClass("invalid-field")){
        $("#networkFormOk").button("disable");
    }else{
        $("#networkFormOk").button("enable");
    }
};

kimchi.enableBridgeOptions = function(enable, networkType, networkDestinationType) {
    $("#enableVlan").prop("checked", false);
    $("#networkVlanID").val("");
    $('#vlan').hide();
    if (enable) {
        $('#bridgedContent').slideDown(300);
        $('#enableVlan').prop("disabled", false);
        $('#networkVlanID').prop("disabled", true);
        if (networkType === kimchi.NETWORK_TYPE_BRIDGED && (networkDestinationType === 'nic' || networkDestinationType === 'bonding')) {
            $('#vlan').show();
        }
    } else {
        $('#bridgedContent').slideUp(300);
        $('#enableVlan').prop("disabled", true);
        $('#networkVlanID').prop("disabled", true);
    };
};

kimchi.loadInterfaces = function(interfaceFilterArray) {
   kimchi.getInterfaces(function(result) {
        var options = [];
        $selectDestination = $('#networkDestinationID');
        var nics = {};
        $('#networkDestinationID').find('option').remove();
        var selectDestinationOptionHTML = '';
        for (var i = 0; i < result.length; i++) {
            if (typeof interfaceFilterArray === 'undefined') {
                options.push({label:result[i].name,value:result[i].name});
                nics[result[i].name] = result[i];
                selectDestinationOptionHTML += '<option data-type="'+ result[i].type +'" value="'+ result[i].name + '">' + result[i].name + '</option>';
            } else {
                for (var k = 0; k < interfaceFilterArray.length; k++) {
                    if (result[i].type == interfaceFilterArray[k]) {
                        options.push({label:result[i].name,value:result[i].name});
                        nics[result[i].name] = result[i];
                        selectDestinationOptionHTML += '<option data-type="'+ result[i].type +'" value="'+ result[i].name + '">' + result[i].name + '</option>';
                    }
                }
            }
        }
        $selectDestination.append(selectDestinationOptionHTML);
        $('#networkDestinationID').selectpicker('refresh');
        kimchi.setDefaultNetworkType(result.length!==0);
        kimchi.changeNetworkDestination();
    });
};
