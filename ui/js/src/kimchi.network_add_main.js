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
        connection: network.type
    };
    if (network.type === kimchi.NETWORK_TYPE_BRIDGE) {
        data.connection = "bridge";
        data.interface = network.interface;
        if ($("#enableVlan").prop("checked")) {
            data.vlan_id = network.vlan_id;
            if (!(data.vlan_id >=1 && data.vlan_id <= 4094)) {
                wok.message.error.code('KCHNET6001E');
                errorCallback();
                return;
            }
        }
    }
    kimchi.createNetwork(data, function(result) {
        network.state = result.state === "active" ? "up" : "down";
        network.interface = result.interface ? result.interface : i18n["KCHNET6001M"];
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
        kimchi.getInterfaces(function(result) {
        var options = [];
        $selectDestination = $('#networkDestinationID');
        var nics = {};
        var selectDestinationOptionHTML = '';
        for (var i = 0; i < result.length; i++) {
            options.push({label:result[i].name,value:result[i].name});
            nics[result[i].name] = result[i];
            selectDestinationOptionHTML += '<option value="'+ result[i].name + '">' + result[i].name + '</option>';
        }
        $selectDestination.append(selectDestinationOptionHTML);
        $selectDestination.selectpicker();
        onChange = function() {
            if (result.length>0 && $selectDestination.val() !== "") {
                $("#enableVlan").prop("disabled",false);
                $("#networkVlanID").val("");
            } else {
                $("#enableVlan").prop("disabled",true);
            }
        };
        $("#networkDestinationID").on("change", onChange);
        kimchi.setDefaultNetworkType(result.length!==0);
        onChange();
    });
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

kimchi.enableBridgeOptions = function(enable) {
    $("#enableVlan").prop("checked", false);
    $("#networkVlanID").val("");
    if (enable) {
        $('#bridgedContent').slideDown(300);
        $('#enableVlan').prop("disabled", false);
        $('#networkVlanID').prop("disabled", true);
    } else {
        $('#bridgedContent').slideUp(300);
        $('#enableVlan').prop("disabled", true);
        $('#networkVlanID').prop("disabled", true);
    }
};


kimchi.setDefaultNetworkType = function(isInterfaceAvail) {
    $("#networkType").val('bridged', isInterfaceAvail);
    $("#networkType option:contains('bridged')").prop("disabled", !isInterfaceAvail);
    $("#networkType").val('nat', !isInterfaceAvail);
    $("#networkType").selectpicker();
    if (!isInterfaceAvail) {
        kimchi.enableBridgeOptions(false);
        $("#networkBriDisabledLabel").removeClass('hidden');
    } else {
        if (kimchi.capabilities && kimchi.capabilities.nm_running) {
            wok.message.warn(i18n['KCHNET6001W'],'#alert-modal-container');
        }
        $("#networkBriDisabledLabel").remove();
    }
};

kimchi.getNetworkDialogValues = function() {
    var network = {
        name : $("#networkName").val(),
        type : $("#networkType").val()
    };
    if (network.type === kimchi.NETWORK_TYPE_BRIDGE) {
        network.interface = $("#networkDestinationLabel").text();
        network.vlan_id = parseInt($("#networkVlanID").val());
    }
    return network;
};

kimchi.setupNetworkFormEvent = function() {
    $('#bridgedContent').hide();
    $("#networkName").on("keyup", function(event) {
        $("#networkName").toggleClass("invalid-field", !$("#networkName").val().match(/^[^\"\/]+$/));
        kimchi.updateNetworkFormButton();
    });
    $('#networkType').on('change', function() {
        var selectedType = $(this).val();
        if(selectedType ==  'isolated' ||  selectedType ==  'nat') {
            kimchi.enableBridgeOptions(false);
        } else if (selectedType ==  'bridged') {
            kimchi.enableBridgeOptions(true);
        }
    }); 
};

kimchi.updateNetworkFormButton = function() {
    if($("#networkName").hasClass("invalid-field")){
        $("#networkFormOk").button("disable");
    }else{
        $("#networkFormOk").button("enable");
    }
};