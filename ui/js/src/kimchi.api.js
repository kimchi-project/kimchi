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
var kimchi = {

    url : "../../../",

    widget: {},

    trackingTasks: [],

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
    requestJSON : function(settings) {
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
    getCapabilities : function(suc, err, done) {
        done = typeof done !== 'undefined' ? done: function(){};
        kimchi.requestJSON({
            url : "config/capabilities",
            type : "GET",
            contentType : "application/json",
            dataType : "json",
            success: suc,
            error: err,
            complete: done
        });
    },

    /**
     * Get the i18 strings.
     */
    getI18n: function(suc, err, url, sync) {
        kimchi.requestJSON({
            url : url ? url : 'i18n.json',
            type : 'GET',
            resend: true,
            dataType : 'json',
            async : !sync,
            success : suc,
            error: err
        });
    },

    /**
     * Get the host static information.
     */
    getHost: function(suc, err) {
        kimchi.requestJSON({
            url : 'host',
            type : 'GET',
            resend: true,
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error: err
        });
    },

    /**
     * Get the dynamic host stats (usually used for monitoring).
     */
    getHostStats : function(suc, err) {
        kimchi.requestJSON({
            url : 'host/stats',
            type : 'GET',
            contentType : 'application/json',
            headers: {'Kimchi-Robot': 'kimchi-robot'},
            dataType : 'json',
            success : suc,
            error: err
        });
    },

    /**
     * Get the historic host stats.
     */
    getHostStatsHistory : function(suc, err) {
        kimchi.requestJSON({
            url : 'host/stats/history',
            type : 'GET',
            resend: true,
            contentType : 'application/json',
            headers: {'Kimchi-Robot': 'kimchi-robot'},
            dataType : 'json',
            success : suc,
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
            url : "vms",
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
            url : "templates",
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
            url : 'templates/' + encodeURIComponent(tem),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    cloneTemplate : function(tem, suc, err) {
        kimchi.requestJSON({
            url : 'templates/' + encodeURIComponent(tem) + "/clone",
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listTemplates : function(suc, err) {
        kimchi.requestJSON({
            url : 'templates',
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
            url : "templates/" + encodeURIComponent(templateName),
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
            url : "templates/" + encodeURIComponent(name),
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
            url : 'storagepools',
            type : 'POST',
            contentType : 'application/json',
            data : JSON.stringify(settings),
            dataType : 'json'
        }).done(suc).fail(err);
    },

    updateStoragePool : function(name, content, suc, err) {
        $.ajax({
            url : "storagepools/" + encodeURIComponent(name),
            type : 'PUT',
            contentType : 'application/json',
            dataType : 'json',
            data : JSON.stringify(content)
        }).done(suc).fail(err ? err : function(data) {
            kimchi.message.error(data.responseJSON.reason);
        });
    },

    startVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/' + encodeURIComponent(vm) + '/start',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    poweroffVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/' + encodeURIComponent(vm) + '/poweroff',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    shutdownVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/' + encodeURIComponent(vm) + '/shutdown',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    resetVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/' + encodeURIComponent(vm) + '/reset',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    suspendVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/' + encodeURIComponent(vm) + '/suspend',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    resumeVM : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/' + encodeURIComponent(vm) + '/resume',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
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
            url : 'vms/' + encodeURIComponent(vm),
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
            url : "vms/" + encodeURIComponent(name),
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
            url : 'vms/' + encodeURIComponent(vm),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    vncToVM : function(vm) {
        kimchi.requestJSON({
            url : 'config',
            type : 'GET',
            dataType : 'json'
        }).done(function(data, textStatus, xhr) {
            proxy_port = data['display_proxy_port'];
            kimchi.requestJSON({
                url : "vms/" + encodeURIComponent(vm) + "/connect",
                type : "POST",
                dataType : "json"
            }).done(function() {
                url = 'https://' + location.hostname + ':' + proxy_port;
                url += "/console.html?url=" + encodeURIComponent("novnc/vnc_auto.html");
                url += "&port=" + proxy_port;
                /*
                 * From python documentation base64.urlsafe_b64encode(s)
                 * substitutes - instead of + and _ instead of / in the
                 * standard Base64 alphabet, BUT the result can still
                 * contain = which is not safe in a URL query component.
                 * So remove it when needed as base64 can work well without it.
                 * */
                url += "&path=?token=" + kimchi.urlSafeB64Encode(vm).replace(/=*$/g, "");
                url += "&kimchi=" + location.port;
                url += '&encrypt=1';
                window.open(url);
            });
        }).error(function() {
            kimchi.message.error.code('KCHAPI6002E');
        });
    },

    spiceToVM : function(vm) {
        kimchi.requestJSON({
            url : 'config',
            type : 'GET',
            dataType : 'json'
        }).done(function(data, textStatus, xhr) {
            proxy_port = data['display_proxy_port'];
            kimchi.requestJSON({
                url : "vms/" + encodeURIComponent(vm) + "/connect",
                type : "POST",
                dataType : "json"
            }).done(function(data, textStatus, xhr) {
                url = 'https://' + location.hostname + ':' + proxy_port;
                url += "/console.html?url=spice_auto.html&port=" + proxy_port;
                url += "&listen=" + location.hostname;
                /*
                 * From python documentation base64.urlsafe_b64encode(s)
                 * substitutes - instead of + and _ instead of / in the
                 * standard Base64 alphabet, BUT the result can still
                 * contain = which is not safe in a URL query component.
                 * So remove it when needed as base64 can work well without it.
                 * */
                url += "&token=" + kimchi.urlSafeB64Encode(vm).replace(/=*$/g, "");
                url += "&kimchi=" + location.port;
                url += '&encrypt=1';
                window.open(url);
            });
        }).error(function() {
            kimchi.message.error.code('KCHAPI6002E');
        });
    },

    listVMs : function(suc, err) {
        kimchi.requestJSON({
            url : 'vms',
            type : 'GET',
            contentType : 'application/json',
            headers: {'Kimchi-Robot': 'kimchi-robot'},
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    listTemplates : function(suc, err) {
        kimchi.requestJSON({
            url : 'templates',
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
            url : 'storagepools',
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
            url : 'storagepools/' + encodeURIComponent(poolName) + '/storagevolumes',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listIsos : function(suc, err) {
        kimchi.requestJSON({
            url : 'storagepools/kimchi_isos/storagevolumes',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listDistros : function(suc, err) {
        kimchi.requestJSON({
            url : 'config/distros',
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

    getTask : function(taskId, suc, err) {
        kimchi.requestJSON({
            url : 'tasks/' + encodeURIComponent(taskId),
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    getTasksByFilter : function(filter, suc, err, sync) {
        kimchi.requestJSON({
            url : 'tasks?' + filter,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            async : !sync,
            success : suc,
            error : err
        });
    },

    login : function(settings, suc, err) {
        $.ajax({
            url : "login",
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json"
        }).done(suc).fail(err);
    },

    logout : function(suc, err) {
        kimchi.requestJSON({
            url : 'logout',
            type : 'POST',
            contentType : "application/json",
            dataType : "json"
        }).done(suc).fail(err);
    },

    deleteStoragePool : function(poolName, suc, err) {
        $.ajax({
            url : 'storagepools/' + encodeURIComponent(poolName),
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
                url : 'storagepools/' + encodeURIComponent(poolName) + '/' + state,
                type : 'POST',
                contentType : 'application/json',
                dataType : 'json',
                success : suc,
                error : err
            });
    },

    listPlugins : function(suc, err, sync) {
        kimchi.requestJSON({
            url : 'plugins',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            async : !sync,
            success : suc,
            error : err
        });
     },

    listNetworks : function(suc, err) {
        kimchi.requestJSON({
            url : 'networks',
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
            url : 'networks/' + encodeURIComponent(name) + '/' + action,
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
            url : 'networks',
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
            url : 'interfaces',
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
            url : 'networks/' + encodeURIComponent(name),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    listReports : function(suc, err) {
        kimchi.requestJSON({
            url : 'debugreports',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    trackTask : function(taskID, suc, err, progress) {
        var onTaskResponse = function(result) {
            var taskStatus = result['status'];
            switch(taskStatus) {
            case 'running':
                progress && progress(result);
                setTimeout(function() {
                    kimchi.trackTask(taskID, suc, err, progress);
                }, 2000);
                break;
            case 'finished':
                suc && suc(result);
                break;
            case 'failed':
                err && err(result);
                break;
            default:
                break;
            }
        };

        kimchi.getTask(taskID, onTaskResponse, err);
        if(kimchi.trackingTasks.indexOf(taskID) < 0)
            kimchi.trackingTasks.push(taskID);
    },

    createReport: function(settings, suc, err, progress) {
        var onResponse = function(data) {
            taskID = data['id'];
            kimchi.trackTask(taskID, suc, err, progress);
        };

        kimchi.requestJSON({
            url : 'debugreports',
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json",
            success : onResponse,
            error : err
        });
    },

    renameReport : function(name, settings, suc, err) {
        $.ajax({
            url : "debugreports/" + encodeURIComponent(name),
            type : 'PUT',
            contentType : 'application/json',
            data : JSON.stringify(settings),
            dataType : 'json',
            success: suc,
            error: err
        });
    },

    deleteReport: function(settings, suc, err) {
        var reportName = encodeURIComponent(settings['name']);
        kimchi.requestJSON({
            url : 'debugreports/' + reportName,
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    downloadReport: function(settings, suc, err) {
        window.open(settings['file']);
    },

    shutdown: function(settings, suc, err) {
        var reboot = settings && settings['reboot'] === true;
        var url = 'host/' + (reboot ? 'reboot' : 'shutdown');
        kimchi.requestJSON({
            url : url,
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listHostPartitions : function(suc, err) {
        kimchi.requestJSON({
            url : 'host/partitions',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    getStorageServers: function(type, suc, err) {
        var url = 'storageservers?_target_type=' + type;
        kimchi.requestJSON({
            url : url,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    getStorageTargets: function(server,type, suc, err) {
        var url = 'storageservers/' + server + '/storagetargets?_target_type=' + type;
        kimchi.requestJSON({
            url : url,
            type : 'GET',
            contentType : 'application/json',
            timeout: 2000,
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    getStoragePool: function(poolName, suc, err) {
        var url = kimchi.url + 'storagepools/' + encodeURIComponent(poolName);
        kimchi.requestJSON({
            url : url,
            type : 'GET',
            contentType : 'application/json',
            timeout: 2000,
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    getStoragePoolVolume: function(poolName, volumeName, suc, err) {
        var url = 'storagepools/' + encodeURIComponent(poolName) + '/storagevolumes/' + encodeURIComponent(volumeName);
        kimchi.requestJSON({
            url : url,
            type : 'GET',
            contentType : 'application/json',
            timeout: 2000,
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    addVMStorage : function(settings, suc, err) {
        var vm = encodeURIComponent(settings['vm']);
        delete settings['vm'];
        kimchi.requestJSON({
            url : 'vms/' + vm + '/storages',
            type : 'POST',
            contentType : 'application/json',
            data : JSON.stringify(settings),
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    retrieveVMStorage : function(settings, suc, err) {
        var vm = encodeURIComponent(settings['vm']);
        var dev = encodeURIComponent(settings['dev']);
        kimchi.requestJSON({
            url : "vms/" + vm + '/storages/' + dev,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success: suc,
            error: err
        });
    },

    replaceVMStorage : function(settings, suc, err) {
        var vm = encodeURIComponent(settings['vm']);
        var dev = encodeURIComponent(settings['dev']);
        kimchi.requestJSON({
            url : 'vms/' + vm + '/storages/' + dev,
            type : 'PUT',
            contentType : 'application/json',
            data : JSON.stringify({
                path: settings['path']
            }),
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    deleteVMStorage : function(settings, suc, err) {
        var vm = settings['vm'];
        var dev = settings['dev'];
        kimchi.requestJSON({
            url : 'vms/' + encodeURIComponent(vm) +
                      '/storages/' + encodeURIComponent(dev),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listVMStorages : function(params, suc, err) {
        var vm = encodeURIComponent(params['vm']);
        var type = params['storageType'];
        var url = 'vms/' + vm + '/storages';
        if(type) {
            url += '?type=' + type;
        }
        kimchi.requestJSON({
            url : url,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listSoftwareUpdates : function(suc, err) {
        kimchi.requestJSON({
            url : 'host/packagesupdate',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    updateSoftware : function(suc, err, progress) {
        var taskID = -1;
        var onResponse = function(data) {
            taskID = data['id'];
            trackTask();
        };

        var trackTask = function() {
            kimchi.getTask(taskID, onTaskResponse, err);
        };

        var onTaskResponse = function(result) {
            var taskStatus = result['status'];
            switch(taskStatus) {
            case 'running':
                progress && progress(result);
                setTimeout(function() {
                    trackTask();
                }, 200);
                break;
            case 'finished':
            case 'failed':
                suc(result);
                break;
            default:
                break;
            }
        };

        kimchi.requestJSON({
            url : 'host/swupdate',
            type : "POST",
            contentType : "application/json",
            dataType : "json",
            success : onResponse,
            error : err
        });
    },

    createRepository : function(settings, suc, err) {
        kimchi.requestJSON({
            url : "host/repositories",
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json",
            success: suc,
            error: err
        });
    },

    retrieveRepository : function(repository, suc, err) {
        var reposID = encodeURIComponent(repository);
        kimchi.requestJSON({
            url : "host/repositories/" + reposID,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    updateRepository : function(name, settings, suc, err) {
        var reposID = encodeURIComponent(name);
        $.ajax({
            url : "host/repositories/" + reposID,
            type : 'PUT',
            contentType : 'application/json',
            data : JSON.stringify(settings),
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    enableRepository : function(name, enable, suc, err) {
        var reposID = encodeURIComponent(name);
        $.ajax({
            url : "host/repositories/" + reposID +
                '/' + (enable === true ? 'enable' : 'disable'),
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    deleteRepository : function(repository, suc, err) {
        var reposID = encodeURIComponent(repository);
        kimchi.requestJSON({
            url : 'host/repositories/' + reposID,
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listRepositories : function(suc, err) {
        kimchi.requestJSON({
            url : 'host/repositories',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    getHostFCDevices: function(suc, err) {
        var url = 'host/devices?_cap=fc_host';
        kimchi.requestJSON({
            url : url,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    getGuestInterfaces: function(name, suc, err) {
        var url = 'vms/'+encodeURIComponent(name)+'/ifaces';
        kimchi.requestJSON({
            url : url,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err || function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    createGuestInterface : function(name, interface, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(name)+'/ifaces',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            data : JSON.stringify(interface),
            success : suc,
            error : err || function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    deleteGuestInterface : function(vm, mac, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(vm)+'/ifaces/'+encodeURIComponent(mac),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    updateGuestInterface : function(vm, mac, interface, suc, err) {
        $.ajax({
            url : 'vms/'+encodeURIComponent(vm)+'/ifaces/'+encodeURIComponent(mac),
            type : 'PUT',
            contentType : 'application/json',
            data : JSON.stringify(interface),
            dataType : 'json',
            success: suc,
            error: err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    getUserById : function(data, suc, err) {
        kimchi.requestJSON({
            url : 'users?_user_id=' + data.user_id,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend : true,
            async : false,
            success : suc && suc(data),
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    getUsers : function(suc, err) {
        kimchi.requestJSON({
            url : 'users',
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

    getGroups : function(suc, err) {
        kimchi.requestJSON({
            url : 'groups',
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

    getHostPCIDevices : function(suc, err) {
        kimchi.requestJSON({
            url : 'host/devices?_passthrough=true&_cap=pci',
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

    getPCIDeviceCompanions : function(pcidev, suc, err) {
        kimchi.requestJSON({
            url : 'host/devices?_passthrough_affected_by=' + pcidev,
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

    getISCSITargets : function(server, port, suc, err) {
        server = encodeURIComponent(server);
        port = port ? '&_server_port='+encodeURIComponent(port) : '';
        kimchi.requestJSON({
            url : 'storageservers/'+server+'/storagetargets?_target_type=iscsi'+port,
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

    getPeers : function(suc, err) {
        kimchi.requestJSON({
            url : 'peers',
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

    getVMPCIDevices : function(id, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(id)+'/hostdevs',
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

    addVMPCIDevice : function(vm, device, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+ encodeURIComponent(vm) +'/hostdevs',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            data : JSON.stringify(device),
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    removeVMPCIDevice : function(vm, device, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+ encodeURIComponent(vm) +'/hostdevs/' + encodeURIComponent(device),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    /**
     * Create a new volume with capacity
     */
    createVolumeWithCapacity: function(poolName, settings, suc, err) {
        kimchi.requestJSON({
            url : 'storagepools/' + encodeURIComponent(poolName) + '/storagevolumes',
            type : 'POST',
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json",
            success : suc,
            error : err
        });
    },

    /**
     * Upload volume content
     */
    uploadVolumeToSP: function(poolName, volumeName, settings, suc, err) {
        var url = 'storagepools/' + encodeURIComponent(poolName) + '/storagevolumes/' + encodeURIComponent(volumeName);
        var fd = settings['formData'];
        kimchi.requestJSON({
            url : url,
            type : 'PUT',
            data : fd,
            processData : false,
            contentType : false,
            dataType: 'json',
            success : suc,
            error : err
        });
    },

    /**
     * Add a volume to a given storage pool by URL.
     */
    downloadVolumeToSP: function(settings, suc, err) {
        var sp = encodeURIComponent(settings['sp']);
        delete settings['sp'];
        kimchi.requestJSON({
            url : 'storagepools/' + sp + '/storagevolumes',
            type : 'POST',
            data : JSON.stringify(settings),
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    cloneGuest: function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(vm)+"/clone",
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    listSnapshots : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(vm)+'/snapshots',
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

    getCurrentSnapshot : function(vm, suc, err, sync) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(vm)+'/snapshots/current',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            async : !sync,
            resend : true,
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    revertSnapshot : function(vm, snapshot, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(vm)+'/snapshots/'+encodeURIComponent(snapshot)+'/revert',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    createSnapshot : function(vm, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(vm)+'/snapshots',
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    deleteSnapshot : function(vm, snapshot, suc, err) {
        kimchi.requestJSON({
            url : 'vms/'+encodeURIComponent(vm)+'/snapshots/'+encodeURIComponent(snapshot),
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    },

    getCPUInfo : function(suc, err) {
        kimchi.requestJSON({
            url : 'host/cpuinfo',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend : true,
            success : suc,
            error : err ? err : function(data) {
                kimchi.message.error(data.responseJSON.reason);
            }
        });
    }
};
