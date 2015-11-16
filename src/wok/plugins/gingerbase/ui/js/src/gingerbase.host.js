/*
 * Project Ginger Base
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
gingerbase.host = {};

gingerbase.host_main = function() {
    "use strict";
    var repositoriesGrid = null;
    var initRepositoriesGrid = function(repo_type) {
        var gridFields = [];
        if (repo_type === "yum") {
            gridFields = [{
                name: 'repo_id',
                label: i18n['GGBREPO6004M'],
                'class': 'repository-id',
                type: 'name'
            }, {
                name: 'config[display_repo_name]',
                label: i18n['GGBREPO6005M'],
                'class': 'repository-name',
                type: 'description'
            }, {
                name: 'enabled',
                label: i18n['GGBREPO6009M'],
                'class': 'repository-enabled',
                type: 'status'
            }];
        } else if (repo_type === "deb") {
            gridFields = [{
                name: 'baseurl',
                label: i18n['GGBREPO6006M'],
                makeTitle: true,
                'class': 'repository-baseurl deb',
                type: 'description'
            }, {
                name: 'enabled',
                label: i18n['GGBREPO6009M'],
                'class': 'repository-enabled deb',
                type: 'status'
            }, {
                name: 'config[dist]',
                label: "dist",
                'class': 'repository-gpgcheck deb'
            }, {
                name: 'config[comps]',
                label: "comps",
                'class': 'repository-gpgcheck deb'
            }];
        } else {
            gridFields = [{
                name: 'repo_id',
                label: i18n['GGBREPO6004M'],
                'class': 'repository-id',
                type: 'name'
            }, {
                name: 'enabled',
                label: i18n['GGBREPO6009M'],
                'class': 'repository-enabled',
                type: 'status'
            }, {
                name: 'baseurl',
                label: i18n['GGBREPO6006M'],
                makeTitle: true,
                'class': 'repository-baseurl',
                type: 'description'
            }];
        }
        repositoriesGrid = new wok.widget.List({
            container: 'repositories-section',
            id: 'repositories-grid',
            title: i18n['GGBREPO6003M'],
            toolbarButtons: [{
                id: 'repositories-grid-add-button',
                label: i18n['GGBREPO6012M'],
                class: 'fa fa-plus-circle',
                onClick: function(event) {
                    wok.window.open({
                        url: 'plugins/gingerbase/repository-add.html',
                        class: repo_type
                    });
                }
            }, {
                id: 'repositories-grid-enable-button',
                label: i18n['GGBREPO6016M'],
                class: 'fa fa-play-circle-o',
                disabled: true,
                onClick: function(event) {
                    var repository = repositoriesGrid.getSelected();
                    if (!repository) {
                        return;
                    }
                    var name = repository['repo_id'];
                    var enable = !repository['enabled'];
                    $(this).prop('disabled', true);
                    gingerbase.enableRepository(name, enable, function() {
                        wok.topic('gingerbase/repositoryUpdated').publish();
                    });
                }
            }, {
                id: 'repositories-grid-edit-button',
                label: i18n['GGBREPO6013M'],
                class: 'fa fa-pencil',
                disabled: true,
                onClick: function(event) {
                    var repository = repositoriesGrid.getSelected();
                    if (!repository) {
                        return;
                    }
                    gingerbase.selectedRepository = repository['repo_id'];
                    wok.window.open({
                        url: 'plugins/gingerbase/repository-edit.html',
                        class: repo_type
                    });
                }
            }, {
                id: 'repositories-grid-remove-button',
                label: i18n['GGBREPO6014M'],
                class: 'fa fa-minus-circle',
                critical: true,
                disabled: true,
                onClick: function(event) {
                    var repository = repositoriesGrid.getSelected();
                    if (!repository) {
                        return;
                    }

                    var settings = {
                        title: i18n['GGBREPO6001M'],
                        content: i18n['GGBREPO6002M'],
                        confirm: i18n['GGBAPI6004M'],
                        cancel: i18n['GGBAPI6003M']
                    };

                    wok.confirm(settings, function() {
                        gingerbase.deleteRepository(
                            repository['repo_id'],
                            function(result) {
                                wok.topic('gingerbase/repositoryDeleted').publish(result);
                            },
                            function(error) {}
                        );
                    });
                }
            }],
            onRowSelected: function(row) {
                var repository = repositoriesGrid.getSelected();
                if (!repository) {
                    return;
                }
                var selectedRow = $('tr',repositoriesGrid.bodyContainer);
                $('#repositories-grid-remove-button',selectedRow).prop('disabled', false);
                $('#repositories-grid-edit-button',selectedRow).prop('disabled', false);
                var enabled = repository['enabled'];
                var actionHtml,actionText,actionIcon ='';
                if(enabled){
                    actionText= i18n['GGBREPO6017M'];
                    actionIcon = 'fa-pause';
                }else{
                    actionText= i18n['GGBREPO6016M'];
                    actionIcon = 'fa-play-circle-o';
                }
                actionHtml = ['<i class="fa',' ',actionIcon,'"></i>','',actionText].join('');
                $('#repositories-grid-enable-button',selectedRow)
                    .html(actionHtml)
                    .prop('disabled', false);
            },
            frozenFields: [],
            fields: gridFields,
            data: listRepositories
        });
    };

    var listRepositories = function(gridCallback) {
        gingerbase.listRepositories(function(repositories) {
                if ($.isFunction(gridCallback)) {
                    gridCallback(repositories);
                } else {
                    if (repositoriesGrid) {
                        repositoriesGrid.setData(repositories);
                    } else {
                        initRepositoriesGrid();
                        repositoriesGrid.setData(repositories);
                    }
                }
            },
            function(error) {
                var message = error && error['responseJSON'] && error['responseJSON']['reason'];

                if ($.isFunction(gridCallback)) {
                    gridCallback([]);
                }
                repositoriesGrid &&
                    repositoriesGrid.showMessage(message || i18n['GGBUPD6008M']);
            });

        $('#repositories-grid-remove-button').prop('disabled', true);
        $('#repositories-grid-edit-button').prop('disabled', true);
        $('#repositories-grid-enable-button').prop('disabled', true);
    };

    var softwareUpdatesGridID = 'software-updates-grid';
    var softwareUpdatesGrid = null;
    var progressAreaID = 'software-updates-progress-textarea';
    var reloadProgressArea = function(result) {
        var progressArea = $('#' + progressAreaID)[0];
        $(progressArea).text(result['message']);
        var scrollTop = $(progressArea).prop('scrollHeight');
        $(progressArea).prop('scrollTop', scrollTop);
    };

    var initSoftwareUpdatesGrid = function(softwareUpdates) {
        softwareUpdatesGrid = new wok.widget.Grid({
            container: 'software-updates-grid-container',
            id: softwareUpdatesGridID,
            title: i18n['GGBUPD6001M'],
            rowSelection: 'disabled',
            toolbarButtons: [{
                id: softwareUpdatesGridID + '-update-button',
                label: i18n['GGBUPD6006M'],
                disabled: true,
                onClick: function(event) {
                    var updateButton = $(this);
                    var progressArea = $('#' + progressAreaID)[0];
                    $('#software-updates-progress-container').removeClass('hidden');
                    $(progressArea).text('');
                    !wok.isElementInViewport(progressArea) &&
                        progressArea.scrollIntoView();
                    $(updateButton).text(i18n['GGBUPD6007M']).prop('disabled', true);

                    gingerbase.updateSoftware(function(result) {
                        reloadProgressArea(result);
                        $(updateButton).text(i18n['GGBUPD6006M']).prop('disabled', false);
                        wok.topic('gingerbase/softwareUpdated').publish({
                            result: result
                        });
                    }, function(error) {
                        var message = error && error['responseJSON'] && error['responseJSON']['reason'];
                        wok.message.error(message || i18n['GGBUPD6009M']);
                        $(updateButton).text(i18n['GGBUPD6006M']).prop('disabled', false);
                    }, reloadProgressArea);
                }
            }],
            frozenFields: [],
            fields: [{
                name: 'package_name',
                label: i18n['GGBUPD6002M'],
                'class': 'software-update-name'
            }, {
                name: 'version',
                label: i18n['GGBUPD6003M'],
                'class': 'software-update-version'
            }, {
                name: 'arch',
                label: i18n['GGBUPD6004M'],
                'class': 'software-update-arch'
            }, {
                name: 'repository',
                label: i18n['GGBUPD6005M'],
                'class': 'software-update-repos'
            }],
            data: listSoftwareUpdates
        });
    };

    var startSoftwareUpdateProgress = function() {
        var progressArea = $('#' + progressAreaID)[0];
        $('#software-updates-progress-container').removeClass('hidden');
        $(progressArea).text('');
        !wok.isElementInViewport(progressArea) &&
            progressArea.scrollIntoView();

        gingerbase.softwareUpdateProgress(function(result) {
            reloadProgressArea(result);
            wok.topic('gingerbase/softwareUpdated').publish({
                result: result
            });
            wok.message.warn(i18n['GGBUPD6010M']);
        }, function(error) {
            wok.message.error(i18n['GGBUPD6011M']);
        }, reloadProgressArea);
    };

    var listSoftwareUpdates = function(gridCallback) {
        gingerbase.listSoftwareUpdates(function(softwareUpdates) {
            if ($.isFunction(gridCallback)) {
                gridCallback(softwareUpdates);
            } else {
                if (softwareUpdatesGrid) {
                    softwareUpdatesGrid.setData(softwareUpdates);
                } else {
                    initSoftwareUpdatesGrid(softwareUpdates);
                }
            }

            var updateButton = $('#' + softwareUpdatesGridID + '-update-button');
            $(updateButton).prop('disabled', softwareUpdates.length === 0);
        }, function(error) {
            var message = error && error['responseJSON'] && error['responseJSON']['reason'];

            // cannot get the list of packages because there is another
            // package manager instance running, so follow that instance updates
            if (message.indexOf("GGBPKGUPD0005E") !== -1) {
                startSoftwareUpdateProgress();
                if ($.isFunction(gridCallback)) {
                    gridCallback([]);
                }
                return;
            }

            if ($.isFunction(gridCallback)) {
                gridCallback([]);
            }
            softwareUpdatesGrid &&
                softwareUpdatesGrid.showMessage(message || i18n['GGBUPD6008M']);
        });
    };

    var reportGridID = 'available-reports-grid';
    var reportGrid = null;
    var enableReportButtons = function(toEnable) {
        var buttonID = '#{grid}-{btn}-button';
        $.each(['rename', 'remove', 'download'], function(i, n) {
            $(wok.substitute(buttonID, {
                grid: reportGridID,
                btn: n
            })).prop('disabled', !toEnable);
        });
    };
    var initReportGrid = function(reports) {
        reportGrid = new wok.widget.List({
            container: 'debug-report-section',
            id: reportGridID,
            title: i18n['GGBDR6002M'],
            toolbarButtons: [{
                id: reportGridID + '-generate-button',
                class: 'fa fa-plus-circle',
                label: i18n['GGBDR6006M'],
                onClick: function(event) {
                    wok.window.open('plugins/gingerbase/report-add.html');
                }
            }, {
                id: reportGridID + '-rename-button',
                class: 'fa fa-pencil',
                label: i18n['GGBDR6008M'],
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if (!report) {
                        return;
                    }

                    gingerbase.selectedReport = report['name'];
                    wok.window.open('plugins/gingerbase/report-rename.html');
                }
            }, {
                id: reportGridID + '-download-button',
                label: i18n['GGBDR6010M'],
                class: 'fa fa-download',
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if (!report) {
                        return;
                    }

                    gingerbase.downloadReport({
                        file: report['uri']
                    });
                }
            }, {
                id: reportGridID + '-remove-button',
                class: 'fa fa-minus-circle',
                label: i18n['GGBDR6009M'],
                critical: true,
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if (!report) {
                        return;
                    }

                    var settings = {
                        title: i18n['GGBAPI6004M'],
                        content: i18n['GGBDR6001M'],
                        confirm: i18n['GGBAPI6002M'],
                        cancel: i18n['GGBAPI6003M']
                    };

                    wok.confirm(settings, function() {
                        gingerbase.deleteReport({
                            name: report['name']
                        }, function(result) {
                            listDebugReports();
                        }, function(error) {
                            wok.message.error(error.responseJSON.reason);
                        });
                    });
                }
            }],
            onRowSelected: function(row) {
                var report = reportGrid.getSelected();
                // Only enable report buttons if the selected line is not a
                // pending report
                if (report['time'] === i18n['GGBDR6007M']) {
                    var gridElement = $('#' + reportGridID);
                    var row = $('tr:contains(' + report['name'] + ')', gridElement);
                    enableReportButtons(false);
                    row.attr('class', '');
                } else {
                    enableReportButtons(true);
                }
            },
            frozenFields: [],
            fields: [{
                name: 'name',
                label: i18n['GGBDR6003M'],
                'class': 'debug-report-name',
                type: 'name'
            }, {
                name: 'time',
                label: i18n['GGBDR6005M'],
                'class': 'debug-report-time',
                type: 'description'
            }],
            data: reports
        });
    };

    var getPendingReports = function() {
        var reports = [];
        var filter = 'status=running&target_uri=' + encodeURIComponent('^/plugins/gingerbase/debugreports/*');

        gingerbase.getTasksByFilter(filter, function(tasks) {
            for (var i = 0; i < tasks.length; i++) {
                var reportName = tasks[i].target_uri.replace(/^\/plugins\/gingerbase\/debugreports\//, '') || i18n['GGBDR6012M'];
                reports.push({
                    'name': reportName,
                    'time': i18n['GGBDR6007M']
                });

                if (gingerbase.trackingTasks.indexOf(tasks[i].id) >= 0) {
                    continue;
                }

                gingerbase.trackTask(tasks[i].id, function(result) {
                    wok.topic('gingerbase/debugReportAdded').publish();
                }, function(result) {
                    // Error message from Async Task status
                    if (result['message']) {
                        var errText = result['message'];
                    }
                    // Error message from standard gingerbase exception
                    else {
                        var errText = result['responseJSON']['reason'];
                    }
                    result && wok.message.error(errText);
                    wok.topic('gingerbase/debugReportAdded').publish();
                }, null);
            }
        }, null, true);

        return reports;
    };

    var listDebugReports = function() {
        gingerbase.listReports(function(reports) {
            var pendingReports = getPendingReports();
            var allReports = pendingReports.concat(reports);
            $('#debug-report-section').removeClass('hidden');
            if ((gingerbase.capabilities['repo_mngt_tool']) && (gingerbase.capabilities['repo_mngt_tool'] !== "None")) {
                $('#debug-report-section, #repositories-section').removeClass('col-md-8');
                $('#debug-report-section, #repositories-section').addClass('col-md-4');
            } else {
                $('#content-sys-info').removeClass('col-md-12');
                $('#content-sys-info').addClass('col-md-4');
            }


            // Row selection will be cleared so disable buttons here
            enableReportButtons(false);

            if (reportGrid) {
                reportGrid.setData(allReports);
            } else {
                initReportGrid(allReports);
            }

            if (!allReports.length) {
                $('#available-reports-grid-btn-group').removeClass('hidden');
            } else {
                $('#available-reports-grid-btn-group').addClass('hidden');
            }

            // Set id-debug-img to pending reports
            // It will display a loading icon
            var gridElement = $('#' + reportGridID);
            //  "Generating..."
            $.each($('td:contains(' + i18n['GGBDR6007M'] + ')', gridElement), function(index, row) {
                console.log(row);
                $(row).parent().addClass('generating');
                $(row).parent().find('.dropdown-toggle').addClass('disabled');
                //$(row).attr('id', 'id-debug-img');
            });
        }, function(error) {
            if (error['status'] === 403) {
                $('#debug-report-section').addClass('hidden');
                // Check Repositories and resize column
                if ((gingerbase.capabilities['repo_mngt_tool']) && (gingerbase.capabilities['repo_mngt_tool'] !== "None")) {
                    $('#repositories-section').removeClass('col-md-4');
                    $('#repositories-section').addClass('col-md-8');
                } else {
                    $('#content-sys-info').removeClass('col-md-4');
                    $('#content-sys-info').addClass('col-md-12');
                }
                return;
            }
            $('#debug-report-section').removeClass('hidden');
            if ((gingerbase.capabilities['repo_mngt_tool']) && (gingerbase.capabilities['repo_mngt_tool'] !== "None")) {
                $('#debug-report-section, #repositories-section').removeClass('col-md-8');
                $('#debug-report-section, #repositories-section').addClass('col-md-4');
            } else {
                $('#content-sys-info').removeClass('col-md-12');
                $('#content-sys-info').addClass('col-md-4');
            }
        });
    };

    var shutdownButtonID = '#host-button-shutdown';
    var restartButtonID = '#host-button-restart';
    var shutdownHost = function(params) {
        var settings = {
            content: i18n['GGBHOST6008M'],
            confirm: i18n['GGBAPI6002M'],
            cancel: i18n['GGBAPI6003M']
        };

        wok.confirm(settings, function() {
            $(shutdownButtonID).prop('disabled', true);
            $(restartButtonID).prop('disabled', true);
            // Check if there is any VM is running.
            // Based on the success will shutdown/reboot
            gingerbase.shutdown(params, function(success) {
                wok.message.success(i18n['GGBHOST6009M'])
                $(shutdownButtonID).prop('disabled', false);
                $(restartButtonID).prop('disabled', false);
                return;
            }, function(error) {
            // Looks like VMs are running.
            wok.message.error.code('GGBHOST6001E');
            $(shutdownButtonID).prop('disabled', false);
            $(restartButtonID).prop('disabled', false);
        });
        }, function() {
        });
    };

    var initPage = function() {

        $('#host-button-shutdown').on('click', function(event) {
            event.preventDefault();
            shutdownHost(null);
        });

        $('#host-button-restart').on('click', function(event) {
            event.preventDefault();
            shutdownHost({
                reboot: true
            });
        });

        var setupUI = function() {
            if (gingerbase.capabilities === undefined) {
                setTimeout(setupUI, 2000);
                return;
            }

            if ((gingerbase.capabilities['repo_mngt_tool']) && (gingerbase.capabilities['repo_mngt_tool'] !== "None")) {
                initRepositoriesGrid(gingerbase.capabilities['repo_mngt_tool']);
                $('#repositories-section').switchClass('hidden', gingerbase.capabilities['repo_mngt_tool']);
                $('#content-sys-info').removeClass('col-md-12', gingerbase.capabilities['repo_mngt_tool']);
                $('#content-sys-info').addClass('col-md-4', gingerbase.capabilities['repo_mngt_tool']);
                wok.topic('gingerbase/repositoryAdded')
                    .subscribe(listRepositories);
                wok.topic('gingerbase/repositoryUpdated')
                    .subscribe(listRepositories);
                wok.topic('gingerbase/repositoryDeleted')
                    .subscribe(listRepositories);
            }

            if (gingerbase.capabilities['update_tool']) {
                $('#software-update-section').removeClass('hidden');
                initSoftwareUpdatesGrid();
                wok.topic('gingerbase/softwareUpdated')
                    .subscribe(listSoftwareUpdates);
            }

            if (gingerbase.capabilities['system_report_tool']) {
                listDebugReports();
                wok.topic('gingerbase/debugReportAdded')
                    .subscribe(listDebugReports);
                wok.topic('gingerbase/debugReportRenamed')
                    .subscribe(listDebugReports);
            }
        };
        setupUI();
    };

    gingerbase.getHost(function(data) {
        var htmlTmpl = $('#host-tmpl').html();
        data['logo'] = data['logo'] || '';
        data['memory'] = wok.formatMeasurement(data['memory'], {
            fixed: 2
        });
        var templated = wok.substitute(htmlTmpl, data);
        $('#host-content-container').html(templated);

        initPage();
        initTracker();
    });

    var StatsMgr = function() {
        var statsArray = {
            cpu: {
                u: {
                    type: 'percent',
                    legend: i18n['GGBHOST6002M'],
                    points: []
                }
            },
            memory: {
                u: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    legend: i18n['GGBHOST6003M'],
                    points: []
                }
            },
            diskIO: {
                w: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['GGBHOST6005M'],
                    'class': 'disk-write',
                    points: []
                },
                r: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['GGBHOST6004M'],
                    points: []
                }
            },
            networkIO: {
                s: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['GGBHOST6007M'],
                    'class': 'network-sent',
                    points: []
                },
                r: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['GGBHOST6006M'],
                    points: []
                }
            }
        };
        var SIZE = 20;
        var cursor = SIZE;

        var add = function(stats) {
            for (var key in stats) {
                var item = stats[key];
                for (var metrics in item) {
                    var value = item[metrics]['v'];
                    var max = item[metrics]['max'];
                    var unifiedMetrics = statsArray[key][metrics];
                    var ps = unifiedMetrics['points'];
                    if (!Array.isArray(value)) {
                        ps.push(value);
                        if (ps.length > SIZE + 1) {
                            ps.shift();
                        }
                    } else {
                        ps = ps.concat(value);
                        ps.splice(0, ps.length - SIZE - 1);
                        unifiedMetrics['points'] = ps;
                    }
                    if (max !== undefined) {
                        unifiedMetrics['max'] = max;
                    } else {
                        if (unifiedMetrics['type'] !== 'value') {
                            continue;
                        }
                        max = -Infinity;
                        $.each(ps, function(i, value) {
                            if (value > max) {
                                max = value;
                            }
                        });
                        if (max === 0) {
                            ++max;
                        }
                        max *= 1.1;
                        unifiedMetrics['max'] = max;
                    }
                }
            }
            cursor++;
        };

        var get = function(which) {
            var stats = statsArray[which];
            var lines = [];
            for (var k in stats) {
                var obj = stats[k];
                var line = {
                    type: obj['type'],
                    base: obj['base'],
                    unit: obj['unit'],
                    fixed: obj['fixed'],
                    legend: obj['legend']
                };
                if (obj['max']) {
                    line['max'] = obj['max'];
                }
                if (obj['class']) {
                    line['class'] = obj['class'];
                }
                var ps = obj['points'];
                var numStats = ps.length;
                var unifiedPoints = [];
                $.each(ps, function(i, value) {
                    unifiedPoints.push({
                        x: cursor - numStats + i,
                        y: value
                    });
                });
                line['points'] = unifiedPoints;
                lines.push(line);
            }
            return lines;
        };

        return {
            add: add,
            get: get
        };
    };

    var Tracker = function(charts) {
        var charts = charts;
        var timer = null;
        var statsPool = new StatsMgr();
        var setCharts = function(newCharts) {
            charts = newCharts;
            for (var key in charts) {
                var chart = charts[key];
                chart.updateUI(statsPool.get(key));
            }
        };

        var self = this;

        var UnifyStats = function(stats) {
            var result = {
                cpu: {
                    u: {
                        v: stats['cpu_utilization']
                    }
                },
                memory: {
                    u: {}
                },
                diskIO: {
                    w: {
                        v: stats['disk_write_rate']
                    },
                    r: {
                        v: stats['disk_read_rate']
                    }
                },
                networkIO: {
                    s: {
                        v: stats['net_sent_rate']
                    },
                    r: {
                        v: stats['net_recv_rate']
                    }
                }
            };
            if (Array.isArray(stats['memory'])) {
                result.memory.u['v'] = [];
                result.memory.u['max'] = -Infinity;
                for (var i = 0; i < stats['memory'].length; i++) {
                    result.memory.u['v'].push(stats['memory'][i]['avail']);
                    result.memory.u['max'] = Math.max(result.memory.u['max'], stats['memory'][i]['total']);
                }
            } else {
                result.memory.u['v'] = stats['memory']['avail'],
                    result.memory.u['max'] = stats['memory']['total']
            }
            return (result);
        };


        var statsCallback = function(stats) {
            var unifiedStats = UnifyStats(stats);
            statsPool.add(unifiedStats);
            for (var key in charts) {
                var chart = charts[key];
                chart.updateUI(statsPool.get(key));
            }
            timer = setTimeout(function() {
                continueTrack();
            }, 1000);
        };

        var track = function() {
            gingerbase.getHostStatsHistory(statsCallback,
                function() {
                    continueTrack();
                });
        };

        var continueTrack = function() {
            gingerbase.getHostStats(statsCallback,
                function() {
                    continueTrack();
                });
        };

        var destroy = function() {
            timer && clearTimeout(timer);
            timer = null;
        };

        return {
            setCharts: setCharts,
            start: track,
            stop: destroy
        };
    };

    var initTracker = function() {
        // TODO: Extend tabs with onUnload event to unregister timers.
        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.stop();
            delete gingerbase.hostTimer;
        }

        var trackedCharts = {
            cpu: new wok.widget.LineChart({
                id: 'chart-cpu',
                node: 'container-chart-cpu',
                type: 'percent'
            }),
            memory: new wok.widget.LineChart({
                id: 'chart-memory',
                node: 'container-chart-memory',
                type: 'value'
            }),
            diskIO: new wok.widget.LineChart({
                id: 'chart-disk-io',
                node: 'container-chart-disk-io',
                type: 'value'
            }),
            networkIO: new wok.widget.LineChart({
                id: 'chart-network-io',
                node: 'container-chart-network-io',
                type: 'value'
            })
        };

        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.setCharts(trackedCharts);
        } else {
            gingerbase.hostTimer = new Tracker(trackedCharts);
            gingerbase.hostTimer.start();
        }
    };

    $('#host-root-container').on('remove', function() {
        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.stop();
            delete gingerbase.hostTimer;
        }

        repositoriesGrid && repositoriesGrid.destroy();
        wok.topic('gingerbase/repositoryAdded')
            .unsubscribe(listRepositories);
        wok.topic('gingerbase/repositoryUpdated')
            .unsubscribe(listRepositories);
        wok.topic('gingerbase/repositoryDeleted')
            .unsubscribe(listRepositories);

        softwareUpdatesGrid && softwareUpdatesGrid.destroy();
        wok.topic('gingerbase/softwareUpdated').unsubscribe(listSoftwareUpdates);

        reportGrid && reportGrid.destroy();
        wok.topic('gingerbase/debugReportAdded').unsubscribe(listDebugReports);
        wok.topic('gingerbase/debugReportRenamed').unsubscribe(listDebugReports);
    });
};
