/*
 * Project Ginger Base
 *
 * Copyright IBM, Corp. 2013-2015
 *
 * Code derived from Project Kimchi
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

    widget: {},

    trackingTasks: [],

    /**
     *
     * Get host capabilities
     * suc: callback if succeed err: callback if failed
     */
    getCapabilities : function(suc, err, done) {
        done = typeof done !== 'undefined' ? done: function(){};
        wok.requestJSON({
            url : "plugins/gingerbase/host/capabilities",
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
        wok.requestJSON({
            url : url ? url : 'plugins/gingerbase/i18n.json',
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
        wok.requestJSON({
            url : 'plugins/gingerbase/host',
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
        wok.requestJSON({
            url : 'plugins/gingerbase/host/stats',
            type : 'GET',
            contentType : 'application/json',
            headers: {'Wok-Robot': 'wok-robot'},
            dataType : 'json',
            success : suc,
            error: err
        });
    },

    /**
     * Get the historic host stats.
     */
    getHostStatsHistory : function(suc, err) {
        wok.requestJSON({
            url : 'plugins/gingerbase/host/stats/history',
            type : 'GET',
            resend: true,
            contentType : 'application/json',
            headers: {'Wok-Robot': 'wok-robot'},
            dataType : 'json',
            success : suc,
            error: err
        });
    },

    getTask : function(taskId, suc, err) {
        wok.requestJSON({
            url : 'plugins/gingerbase/tasks/' + encodeURIComponent(taskId),
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    getTasksByFilter : function(filter, suc, err, sync) {
        wok.requestJSON({
            url : 'plugins/gingerbase/tasks?' + filter,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            async : !sync,
            success : suc,
            error : err
        });
    },

    listReports : function(suc, err) {
        wok.requestJSON({
            url : 'plugins/gingerbase/debugreports',
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

        wok.requestJSON({
            url : 'plugins/gingerbase/debugreports',
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
            url : "plugins/gingerbase/debugreports/" + encodeURIComponent(name),
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
        wok.requestJSON({
            url : 'plugins/gingerbase/debugreports/' + reportName,
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
        var url = 'plugins/gingerbase/host/' + (reboot ? 'reboot' : 'shutdown');
        wok.requestJSON({
            url : url,
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listHostPartitions : function(suc, err) {
        wok.requestJSON({
            url : 'plugins/gingerbase/host/partitions',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listSoftwareUpdates : function(suc, err) {
        wok.requestJSON({
            url : 'plugins/gingerbase/host/packagesupdate',
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

        wok.requestJSON({
            url : 'plugins/gingerbase/host/swupdate',
            type : "POST",
            contentType : "application/json",
            dataType : "json",
            success : onResponse,
            error : err
        });
    },

    createRepository : function(settings, suc, err) {
        wok.requestJSON({
            url : "plugins/gingerbase/host/repositories",
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
        wok.requestJSON({
            url : "plugins/gingerbase/host/repositories/" + reposID,
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
            url : "plugins/gingerbase/host/repositories/" + reposID,
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
            url : "plugins/gingerbase/host/repositories/" + reposID +
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
        wok.requestJSON({
            url : 'plugins/gingerbase/host/repositories/' + reposID,
            type : 'DELETE',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    listRepositories : function(suc, err) {
        wok.requestJSON({
            url : 'plugins/gingerbase/host/repositories',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    getCPUInfo : function(suc, err) {
        wok.requestJSON({
            url : 'plugins/gingerbase/host/cpuinfo',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend : true,
            success : suc,
            error : err ? err : function(data) {
                wok.message.error(data.responseJSON.reason);
            }
        });
    }
};
