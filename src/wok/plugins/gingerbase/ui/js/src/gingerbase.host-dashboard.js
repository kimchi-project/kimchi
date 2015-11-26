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

gingerbase.host_dashboard = function() {
    "use strict";
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
            });
        }, function(error) {
            if (error['status'] === 403) {
                $('#debug-report-section').addClass('hidden');
                return;
            }
            $('#debug-report-section').removeClass('hidden');
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
        var htmlTmpl = $('#host-dashboard-tmpl').html();
        var memory = null
        var cpus = null
        data['logo'] = data['logo'] || '';
        // Memory fetch online, offline details
        data['memory']['online'] = wok.formatMeasurement(data['memory']['online'], {
            fixed: 2
        });
        data['memory']['offline'] = wok.formatMeasurement(data['memory']['offline'], {
            fixed: 2
        });
        memory = "Online: " + data['memory']['online'] + ", Offline: " + data['memory']['offline'];
        // CPU fetch online, offline details
        cpus = 'Online: ' + data['cpus']['online'] + ', Offline: ' + data['cpus']['offline'];
        // This code is only for s390x architecture where hypervisor details required.
        if (data['architecture'] == 's390x'){
            cpus += ', Shared: ' + data['cpus']['shared'] + ', Dedicated: ' + data['cpus']['dedicated'];
            data['lpar_details'] = 'Name: ' + data['virtualization']['lpar_name'] + ', ID: ' + data['virtualization']['lpar_number'];
            data['hypervisor_details'] = 'Name: ' + data['virtualization']['hypervisor'] + ', Vendor :' + data['virtualization']['hypervisor_vendor'];
        }
        data['memory'] = memory
        data['cpus'] = cpus
        var templated = wok.substitute(htmlTmpl, data);
        $('#host-content-container').html(templated);

        initPage();
        initTracker();
        // Enable hypervisor, LPAR details on s390x architechture
        if (data['architecture'] == 's390x'){
            $('#s390x-info').removeClass();
        }
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

        reportGrid && reportGrid.destroy();
        wok.topic('gingerbase/debugReportAdded').unsubscribe(listDebugReports);
        wok.topic('gingerbase/debugReportRenamed').unsubscribe(listDebugReports);
    });
};
