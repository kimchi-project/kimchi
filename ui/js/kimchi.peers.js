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

var kimchi = {

    getPeers: function(suc, err) {
        wok.requestJSON({
            url: 'plugins/kimchi/peers',
            type: 'GET',
            contentType: 'application/json',
            dataType: 'json',
            resend: true,
            success: suc,
            error: err ? err : function(data) {
                wok.message.error(data.responseJSON.reason);
            }
        });
    },

    initPeers: function() {

        var peersAccordion = "<div class='panel-group federation-enabled accordion' id='peers-content-area-accordion' role='tablist' aria-multiselectable='true'>" +
            "<h3>" +
            "<a role='button' aria-expanded='true' data-toggle='collapse' data-parent='#peers-content-area-accordion' href='#peers-content-area' aria-expanded='false' aria-controls='peers-content-area' class=''>" +
            "<span class='accordion-icon'></span>" +
            "<span class='accordion-text' id='#peers-title'>"+i18n['KCHPEERS0001M']+"</span>" +
            "</a>" +
            "</h3>" +
            "<div id='peers-content-area' class='panel-collapse collapse in' role='tabpanel' aria-labelledby='peers-title'>" +
            "<div id='peers-alert-container'></div>" +
            "<div class='row'>" +
            "<div class='col-sm-12'>" +
            "<table id='peers-list' class='table table-striped' cellspacing='0' width='100%''>" +
            "<thead>" +
            "<tr>" +
            "<th><span class='sr-only'>" + i18n['KCHPEERS0001M'] + "</span></th>" +
            "</tr>" +
            "</thead>" +
            "</table>" +
            "</div>" +
            "</div>" +
            "<div class='wok-mask' role='presentation'>" +
            "<div class='wok-mask-loader-container'>" +
            "<div class='wok-mask-loading'>" +
            "<div class='wok-mask-loading-icon'></div>" +
            "<div class='wok-mask-loading-text'>" + i18n['WOKGRD6001M'] + "</div>" +
            "</div>" +
            "</div>" +
            "</div>" +
            "</div>" +
            "</div>";

        var peersDatatableTable;
        var peers = new Array();

        $('#peers-container > .container').append(peersAccordion);

        var peersDatatable = function(nwConfigDataSet) {
            peersDatatableTable = $('#peers-list').DataTable({
                "processing": true,
                "data": peers,
                "language": {
                    "emptyTable": i18n['WOKSETT0010M']
                },
                "order": [],
                "paging": false,
                "dom": '<"row"<"col-sm-12"t>>',
                "scrollY": "269px",
                "scrollCollapse": true,
                "columnDefs": [{
                    "targets": 0,
                    "searchable": false,
                    "orderable": false,
                    "width": "100%",
                    "className": "tabular-data",
                    "render": function(data, type, full, meta) {
                        return '<a href="' + data + '" target="_blank">' + data + '</a>';
                    }
                }],
                "initComplete": function(settings, json) {
                    $('#peers-content-area > .wok-mask').addClass('hidden');
                }
            });
        };

        var getPeers = function() {
            kimchi.getPeers(function(result) {
                peers.length = 0;
                for (var i = 0; i < result.length; i++) {
                    var tempArr = [];
                    tempArr.push(result[i]);
                    peers.push(tempArr);
                }
                peersDatatable(peers);
            }, function(err) {
                wok.message.error(err.responseJSON.reason, '#peers-alert-container', true);
            });
        };
        getPeers();

    },

    getConfig: function(suc, err, done) {
        done = typeof done !== 'undefined' ? done : function() {};
        wok.requestJSON({
            url: "plugins/kimchi/config",
            type: "GET",
            contentType: "application/json",
            dataType: "json",
            success: suc,
            error: err,
            complete: done
        });
    }
}

$(document).ready(function() {
    // Peers check
    kimchi.getConfig(function(config) {
        if (config.federation) {
            $("#host-content-container").after('<div id="peers-container"><div class="container"></div></div>');
            kimchi.initPeers();
        }
    });
});
