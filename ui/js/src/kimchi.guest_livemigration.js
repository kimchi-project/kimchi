/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2016-2017
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

kimchi.guest_livemigration_main = function() {
    kimchi.setupLiveMigrationFormEvent();
    kimchi.initLiveMigrationDialog();
};


kimchi.getOngoingMigration = function(guestName, toDelete) {
    var guests = [];
    kimchi.getTasksByFilter('status=running&target_uri='+ encodeURIComponent('^/plugins/kimchi/vms/' + guestName + '/migrate'), function(tasks) {
        for (var i = 0; i < tasks.length; i++) {
            var guestUri = tasks[i].target_uri;
            var guestName = guestUri.split('/')[4];
            guests[guestName] = tasks[i];

            if (kimchi.trackingTasks.indexOf(tasks[i].id) >= 0) {
                continue;
            }

            kimchi.trackTask(tasks[i].id, function(guests) {
                if (toDelete) {
                    kimchi.deleteVM(guestName, function(result) {
                        return;
                    });
                }
                kimchi.listVmsAuto();
            }, function(guests) {
                wok.message.error('<strong>'+guestName+'</strong>: '+guests.message,'#alert-container', true, 'failed-migration-'+guests.id);
                return;
            }, function(guests) {
                return;
            });
        }
    }, null, true);
    return guests;
};

kimchi.initLiveMigrationDialog = function(okCallback) {
    $("#migrateFormOk").on("click", function() {
        $("#migrateFormOk").prop("disabled", true);
        $("#remote_host").prop("readonly", "readonly");
        $("#user").prop("readonly", "readonly");
        $("#password").prop("readonly", "readonly");
        $("#deleteVM").prop("readonly", "readonly");
        wok.window.close();
        kimchi.initLiveMigrationProccess();
    });
};

kimchi.initLiveMigrationProccess = function() {
    var obj = kimchi.getLiveMigrationInputValues();
    var toDelete = obj[kimchi.selectedGuest].toDelete;
    kimchi.migrateGuest(kimchi.selectedGuest, obj[kimchi.selectedGuest].values, function() {
        kimchi.listVmsAuto();
        kimchi.getOngoingMigration(kimchi.selectedGuest, toDelete);
    }, function(err) {
        wok.message.error(err.responseJSON.reason);
    });
}

kimchi.getLiveMigrationInputValues = function() {
    var host = $("#remote_host").val();
    var username = $("#user").val();
    var password = $("#password").val();
    var toDelete = $("#deleteVM").prop('checked');
    var enable_rdma = $("#enableRDMA").prop('checked');
    var data = {};
    data[kimchi.selectedGuest] = {
        values: {
            remote_host: host,
            enable_rdma: enable_rdma
        },
        toDelete: toDelete
    };
    if (username && password) {
        data[kimchi.selectedGuest].values.user = username;
        data[kimchi.selectedGuest].values.password = password;
    }
    return data;
};

kimchi.setupLiveMigrationFormEvent = function() {
    $("#migrateFormOk").prop("disabled", true);
    $("#remote_host").on("keyup", function(event) {
        if (!this.value) {
            $(this).parent().addClass('has-error');
        } else {
            $(this).parent().removeClass('has-error');
        }
        kimchi.updateLiveMigrationButton();
    });
    $("#user").on("keyup", function(event) {
        if (this.value && !$("#password").val()) {
            $("#user").parent().removeClass('has-warning');
            $("#password").parent().addClass('has-warning');
        } else {
            $("#user").parent().removeClass('has-warning');
            $("#password").parent().removeClass('has-warning');
        }
        kimchi.updateLiveMigrationButton();
    });
    $("#password").on("keyup", function(event) {
        if (this.value && !$("#user").val()) {
            $("#user").parent().addClass('has-warning');
        } else {
            $("#user").parent().removeClass('has-warning');
            $("#password").parent().removeClass('has-warning');
            kimchi.updateLiveMigrationButton();
        }
    });
};

kimchi.updateLiveMigrationButton = function() {
    if ($("#remote_host").val()) {
        if ($("input[type='text']").parent().hasClass("has-error") || $("input[type='text']").parent().hasClass("has-warning")) {
            $("#migrateFormOk").prop("disabled", true);
        } else {
            $("#migrateFormOk").prop("disabled", false);
        }
    };
};
