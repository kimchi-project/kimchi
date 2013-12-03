/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwanghl@cn.ibm.com>
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

    url : "../../../",

    /**
     * A wrapper of jQuery.ajax function to allow custom bindings.
     *
     * @param settings an extended object to jQuery Ajax settings object
     *   with some extra properties (see below)
     *
     *   resend: if the XHR has failed due to 401, the XHR can be resent
     *     after user being authenticated successfully by setting resend
     *     to true: settings = {resend: true}. It's useful for switching
     *     pages (Guests, Templates, etc.).
     *       e.g., the user wants to list guests by clicking Guests tab,
     *     but he is told not authorized and a login window will pop up.
     *     After login, the Ajax request for /vms will be resent without
     *     user clicking the tab again.
     *       Default to false.
     */
    requestJSON: function(settings) {
        settings['originalError'] = settings['error'];
        settings['error'] = null;
        settings['kimchi'] = true;
        return $.ajax(settings);
    },

    /**
     *
     * Get host capabilities
     * suc: callback if succeed err: callback if failed
     */
    getCapabilities : function(suc, err) {
        kimchi.requestJSON({
            url : "/config/capabilities",
            type : "GET",
            contentType : "application/json",
            dataType : "json",
            success: suc,
            error: err
        });
    },

    /**
     *
     * Create a new Virtual Machine. Usage: kimchi.createVM({ name: 'MyUbuntu',
     * template: '/templates/ubuntu_base' }, creationSuc, creationErr);
     *
     * settings: name *(optional)*: The name of the VM. Used to identify the VM
     * in this API. If omitted, a name will be chosen based on the template
     * used. template: The URI of a Template to use when building the VM
     * storagepool *(optional)*: Assign a specific Storage Pool to the new VM
     * suc: callback if succeed err: callback if failed
     */
    createVM : function(settings, suc, err) {
        kimchi.requestJSON({
            url : "/vms",
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json"
        }).done(suc).fail(err);
    },

    /**
     *
     * Create a new Template. settings name: The name of the Template. Used to
     * identify the Template in this API suc: callback if succeed err: callback
     * if failed
     */
    createTemplate : function(settings, suc, err) {
        kimchi.requestJSON({
            url : "/templates",
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json",
            success: suc,
            error: err
        });
    },

    deleteTemplate : function(tem, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'templates/' + encodeURIComponent(tem),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listTemplates : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'templates',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    /**
     * Retrieve the information of a template by the given name.
     */
    retrieveTemplate : function(templateName, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + "templates/" + encodeURIComponent(templateName),
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json'
        }).done(suc);
    },

    /**
     * Update a template with new information. TODO: Update me when the RESTful
     * API is available. Now work it around by remove the template and then
     * recreate it with new information.
     */
    updateTemplate : function(name, settings, suc, err) {
        $.ajax({
            url : kimchi.url + "templates/" + encodeURIComponent(name),
            type : 'PUT',
            contentType : 'application/json',
            data : JSON.stringify(settings),
            dataType : 'json'
        }).done(suc).fail(err);
    },

    /**
     * Create a new Storage Pool. settings name: The name of the Storage Pool
     * path: The path of the defined Storage Pool type: The type of the defined
     * Storage Pool capacity: The total space which can be used to store volumes
     * The unit is MBytes suc: callback if succeed err: callback if failed
     */
    createStoragePool : function(settings, suc, err) {
        kimchi.requestJSON({
            url : '/storagepools',
            type : 'POST',
            contentType : 'application/json',
            data : JSON.stringify(settings),
            dataType : 'json'
        }).done(suc).fail(err);
    },

    startVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'vms/' + encodeURIComponent(vm) + '/start',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    stopVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'vms/' + encodeURIComponent(vm) + '/stop',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    resetVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'vms/' + encodeURIComponent(vm) + '/stop',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : function() {
                kimchi.requestJSON({
                    url : kimchi.url + 'vms/' + encodeURIComponent(vm) + '/start',
                    type : 'POST',
                    contentType : 'application/json',
                    dataType : 'json',
                    success : suc,
                    error : err
                });
            },
            error : err
        });
    },

    /**
     * Retrieve the information of a given VM by its name.
     *
     * @param vm VM name
     * @param suc callback for success
     * @param err callback for error
     */
    retrieveVM : function(vm, suc, err) {
        $.ajax({
            url : kimchi.url + 'vms/' + encodeURIComponent(vm),
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success: suc,
            error: err
        });
    },

    /**
     * Update a VM with new information.
     */
    updateVM : function(name, settings, suc, err) {
        $.ajax({
            url : kimchi.url + "vms/" + encodeURIComponent(name),
            type : 'PUT',
            contentType : 'application/json',
            data : JSON.stringify(settings),
            dataType : 'json',
            success: suc,
            error: err
        });
    },

    deleteVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'vms/' + encodeURIComponent(vm),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    vncToVM : function(vm) {
        kimchi.requestJSON({
            url : '/config',
            type : 'GET',
            dataType : 'json'
        }).done(function(data, textStatus, xhr) {
            http_port = data['http_port'];
            kimchi.requestJSON({
                url : "/vms/" + encodeURIComponent(vm) + "/connect",
                type : "POST",
                dataType : "json"
            }).done(function(data, textStatus, xhr) {
                /**
                 * Due to problems with web sockets and self-signed
                 * certificates, for now we will always redirect to http
                 */
                url = 'http://' + location.hostname + ':' + http_port;
                url += "/vnc_auto.html?port=" + data.graphics.port;
                window.open(url);
            });
        }).error(function() {
            kimchi.message.error(i18n['msg.fail.get.config']);
        });
    },

    listVMs : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'vms',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    listTemplates : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'templates',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    listStoragePools : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'storagepools',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    listStorageVolumes : function(poolName, suc, err) {
        $.ajax({
            url : kimchi.url + 'storagepools/' + encodeURIComponent(poolName) + '/storagevolumes',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listIsos : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'storagepools/kimchi_isos/storagevolumes',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listDistros : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'config/distros',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    stepListDeepScanIsos : function(suc, err) {
        var deepScanHandler = {
            stop : false
        };
        var isoPool = 'iso' + new Date().getTime();
        kimchi.createStoragePool({
            name : isoPool,
            type : 'kimchi-iso',
            path : '/'
        }, function(result) {
            var taskId = result.task_id;
            function monitorTask() {
                if (deepScanHandler.stop) {
                    return;
                }
                kimchi.getTask(taskId, function(result) {
                    var status = result.status;
                    if (status === "finished") {
                        if (deepScanHandler.stop) {
                            return;
                        }
                        kimchi.listStorageVolumes(isoPool, function(isos) {
                            if (deepScanHandler.stop) {
                                return;
                            }
                            suc(isos, true);
                        }, err);
                    } else if (status === "running") {
                        if (deepScanHandler.stop) {
                            return;
                        }
                        kimchi.listStorageVolumes(isoPool, function(isos) {
                            if (deepScanHandler.stop) {
                                return;
                            }
                            suc(isos, false);
                            setTimeout(monitorTask, 2000);
                        }, err);
                    } else if (status === "failed") {
                        if (deepScanHandler.stop) {
                            return;
                        }
                        err(result.message);
                    }
                }, err);
            }
            setTimeout(monitorTask, 2000);
        }, err);
        return deepScanHandler;
    },

    listDeepScanIsos : function(suc, err) {
        var isoPool = 'iso' + new Date().getTime();
        kimchi.createStoragePool({
            name : isoPool,
            type : 'kimchi-iso',
            path : '/'
        }, function(result) {
            var taskId = result.task_id;
            function monitorTask() {
                kimchi.getTask(taskId, function(result) {
                    var status = result.status;
                    if (status === "finished") {
                        kimchi.listStorageVolumes(isoPool, suc, err);
                    } else if (status === "running") {
                        setTimeout(monitorTask, 50);
                    } else if (status === "failed") {
                        err(result.message);
                    }
                }, err);
            }
            monitorTask();
        }, err);
    },

    getTask : function(taskId, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'tasks/' + encodeURIComponent(taskId),
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    login : function(settings, suc, err) {
        $.ajax({
            url : "/login",
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json"
        }).done(suc).fail(err);
    },

    logout : function(suc, err) {
        kimchi.requestJSON({
            url : '/logout',
            type : 'POST',
            contentType : "application/json",
            dataType : "json"
        }).done(suc).fail(err);
    },

    deleteStoragePool : function(poolName, suc, err) {
        $.ajax({
            url : kimchi.url + 'storagepools/' + encodeURIComponent(poolName),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    changePoolState : function(poolName, state, suc, err) {
        if (state === 'activate' || state === 'deactivate')
            $.ajax({
                url : kimchi.url + 'storagepools/' + encodeURIComponent(poolName) + '/' + state,
                type : 'POST',
                contentType : 'application/json',
                dataType : 'json',
                success : suc,
                error : err
            });
    },

    listPlugins : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'plugins',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
     },

    listNetworks : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'networks',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend : true,
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    toggleNetwork : function(name, on, suc, err) {
        var action = on ? "activate" : "deactivate";
        kimchi.requestJSON({
            url : kimchi.url + 'networks/' + encodeURIComponent(name) + '/' + action,
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    createNetwork : function(network, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'networks',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            data : JSON.stringify(network),
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    getInterfaces : function(suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'interfaces',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend : true,
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    deleteNetwork : function(name, suc, err) {
        kimchi.requestJSON({
            url : kimchi.url + 'networks/' + encodeURIComponent(name),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    }

};
