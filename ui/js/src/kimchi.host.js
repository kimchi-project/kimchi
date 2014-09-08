/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2014
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
kimchi.host={};

kimchi.host_main = function() {
    var expand = function(header, toExpand) {
        var controlledNode = $(header).attr('aria-controls');
        $('#' + controlledNode)[toExpand ? 'removeClass' : 'addClass']('hidden');
        $(header).attr('aria-expanded', toExpand ? 'true' : 'false');
    };

    var repositoriesGrid = null;
    var initRepositoriesGrid = function(repo_type) {
        var gridFields=[];
        if (repo_type == "yum") {
                gridFields=[{
                    name: 'repo_id',
                    label: i18n['KCHREPO6004M'],
                    'class': 'repository-id'
                }, {
                    name: 'config[repo_name]',
                    label: i18n['KCHREPO6005M'],
                    'class': 'repository-name'
                }, {
                    name: 'enabled',
                    label: i18n['KCHREPO6009M'],
                    'class': 'repository-enabled'
                }];
        }
        else if (repo_type == "deb") {
                gridFields=[{
                    name: 'baseurl',
                    label: i18n['KCHREPO6006M'],
                    makeTitle: true,
                    'class': 'repository-baseurl deb'
                }, {
                    name: 'enabled',
                    label: i18n['KCHREPO6009M'],
                    'class': 'repository-enabled deb'
                }, {
                    name: 'config[dist]',
                    label: "dist",
                    'class': 'repository-gpgcheck deb'
                }, {
                    name: 'config[comps]',
                    label: "comps",
                    'class': 'repository-gpgcheck deb'
                }];
        }
        else {
            gridFields=[{
                name: 'repo_id',
                label: i18n['KCHREPO6004M'],
                'class': 'repository-id'
                }, {
                    name: 'enabled',
                    label: i18n['KCHREPO6009M'],
                    'class': 'repository-enabled'
                }, {
                    name: 'baseurl',
                    label: i18n['KCHREPO6006M'],
                    makeTitle: true,
                    'class': 'repository-baseurl'
                }];
        }
        repositoriesGrid = new kimchi.widget.Grid({
            container: 'repositories-grid-container',
            id: 'repositories-grid',
            title: i18n['KCHREPO6003M'],
            toolbarButtons: [{
                id: 'repositories-grid-add-button',
                label: i18n['KCHREPO6012M'],
                onClick: function(event) {
                    kimchi.window.open({url:'repository-add.html', class: repo_type});
                }
            }, {
                id: 'repositories-grid-enable-button',
                label: i18n['KCHREPO6016M'],
                disabled: true,
                onClick: function(event) {
                    var repository = repositoriesGrid.getSelected();
                    if(!repository) {
                        return;
                    }
                    var name = repository['repo_id'];
                    var enable = !repository['enabled'];
                    $(this).prop('disabled', true);
                    kimchi.enableRepository(name, enable, function() {
                        kimchi.topic('kimchi/repositoryUpdated').publish();
                    });
                }
            }, {
                id: 'repositories-grid-edit-button',
                label: i18n['KCHREPO6013M'],
                disabled: true,
                onClick: function(event) {
                    var repository = repositoriesGrid.getSelected();
                    if(!repository) {
                        return;
                    }
                    kimchi.selectedRepository = repository['repo_id'];
                    kimchi.window.open({url:'repository-edit.html', class: repo_type});
                }
            }, {
                id: 'repositories-grid-remove-button',
                label: i18n['KCHREPO6014M'],
                disabled: true,
                onClick: function(event) {
                    var repository = repositoriesGrid.getSelected();
                    if(!repository) {
                        return;
                    }

                    var settings = {
                        title : i18n['KCHREPO6001M'],
                        content : i18n['KCHREPO6002M'],
                        confirm : i18n['KCHAPI6004M'],
                        cancel : i18n['KCHAPI6003M']
                    };

                    kimchi.confirm(settings, function() {
                        kimchi.deleteRepository(
                            repository['repo_id'],
                            function(result) {
                                kimchi.topic('kimchi/repositoryDeleted').publish(result);
                            }, function(error) {
                            }
                        );
                    });
                }
            }],
            onRowSelected: function(row) {
                var repository = repositoriesGrid.getSelected();
                if(!repository) {
                    return;
                }
                $('#repositories-grid-remove-button').prop('disabled', false);
                $('#repositories-grid-edit-button').prop('disabled', false);
                var enabled = repository['enabled'];
                $('#repositories-grid-enable-button')
                    .text(i18n[enabled ? 'KCHREPO6017M' : 'KCHREPO6016M'])
                    .prop('disabled', false);
            },
            frozenFields: [],
            fields: gridFields,
            data: listRepositories
        });
    };

    var listRepositories = function(gridCallback) {
        kimchi.listRepositories(function(repositories) {
            if($.isFunction(gridCallback)) {
                gridCallback(repositories);
            }
            else {
                if(repositoriesGrid) {
                    repositoriesGrid.setData(repositories);
                }
                else {
                    initRepositoriesGrid();
                    repositoriesGrid.setData(repositories);
                }
            }
        },
        function(error) {
            var message = error && error['responseJSON'] && error['responseJSON']['reason'];

            if($.isFunction(gridCallback)) {
                gridCallback([]);
            }
            repositoriesGrid &&
                repositoriesGrid.showMessage(message || i18n['KCHUPD6008M']);
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
        softwareUpdatesGrid = new kimchi.widget.Grid({
            container: 'software-updates-grid-container',
            id: softwareUpdatesGridID,
            title: i18n['KCHUPD6001M'],
            rowSelection: 'disabled',
            toolbarButtons: [{
                id: softwareUpdatesGridID + '-update-button',
                label: i18n['KCHUPD6006M'],
                disabled: true,
                onClick: function(event) {
                    var updateButton = $(this);
                    var progressArea = $('#' + progressAreaID)[0];
                    $('#software-updates-progress-container').removeClass('hidden');
                    $(progressArea).text('');
                    !kimchi.isElementInViewport(progressArea) &&
                        progressArea.scrollIntoView();
                    $(updateButton).text(i18n['KCHUPD6007M']).prop('disabled', true);

                    kimchi.updateSoftware(function(result) {
                        reloadProgressArea(result);
                        $(updateButton).text(i18n['KCHUPD6006M']).prop('disabled', false);
                        kimchi.topic('kimchi/softwareUpdated').publish({
                            result: result
                        });
                    }, function(error) {
                        var message = error && error['responseJSON'] && error['responseJSON']['reason'];
                        kimchi.message.error(message || i18n['KCHUPD6009M']);
                        $(updateButton).text(i18n['KCHUPD6006M']).prop('disabled', false);
                    }, reloadProgressArea);
                }
            }],
            frozenFields: [],
            fields: [{
                name: 'package_name',
                label: i18n['KCHUPD6002M'],
                'class': 'software-update-name'
            }, {
                name: 'version',
                label: i18n['KCHUPD6003M'],
                'class': 'software-update-version'
            }, {
                name: 'arch',
                label: i18n['KCHUPD6004M'],
                'class': 'software-update-arch'
            }, {
                name: 'repository',
                label: i18n['KCHUPD6005M'],
                'class': 'software-update-repos'
            }],
            data: listSoftwareUpdates
        });
    };

    var listSoftwareUpdates = function(gridCallback) {
        kimchi.listSoftwareUpdates(function(softwareUpdates) {
            if($.isFunction(gridCallback)) {
                gridCallback(softwareUpdates);
            }
            else {
                if(softwareUpdatesGrid) {
                    softwareUpdatesGrid.setData(softwareUpdates);
                }
                else {
                    initSoftwareUpdatesGrid(softwareUpdates);
                }
            }

            var updateButton = $('#' + softwareUpdatesGridID + '-update-button');
            $(updateButton).prop('disabled', softwareUpdates.length === 0);
        }, function(error) {
            var message = error && error['responseJSON'] && error['responseJSON']['reason'];
            if($.isFunction(gridCallback)) {
                gridCallback([]);
            }
            softwareUpdatesGrid &&
                softwareUpdatesGrid.showMessage(message || i18n['KCHUPD6008M']);
        });
    };

    var reportGridID = 'available-reports-grid';
    var reportGrid = null;
    var enableReportButtons = function(toEnable) {
        var buttonID = '#{grid}-{btn}-button';
        $.each(['rename', 'remove', 'download'], function(i, n) {
            $(kimchi.substitute(buttonID, {
                grid: reportGridID,
                btn: n
            })).prop('disabled', !toEnable);
        });
    };
    var initReportGrid = function(reports) {
        reportGrid = new kimchi.widget.Grid({
            container: 'available-reports-grid-container',
            id: reportGridID,
            title: i18n['KCHDR6002M'],
            toolbarButtons: [{
                id: reportGridID + '-generate-button',
                label: i18n['KCHDR6006M'],
                onClick: function(event) {
                    kimchi.window.open('report-add.html');
                }
            }, {
                id: reportGridID + '-rename-button',
                label: i18n['KCHDR6008M'],
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if(!report) {
                        return;
                    }

                    kimchi.selectedReport = report['name'];
                    kimchi.window.open('report-rename.html');
                }
            }, {
                id: reportGridID + '-remove-button',
                label: i18n['KCHDR6009M'],
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if(!report) {
                        return;
                    }

                    var settings = {
                        title : i18n['KCHAPI6004M'],
                        content : i18n['KCHDR6001M'],
                        confirm : i18n['KCHAPI6002M'],
                        cancel : i18n['KCHAPI6003M']
                    };

                    kimchi.confirm(settings, function() {
                        kimchi.deleteReport({
                            name: report['name']
                        }, function(result) {
                            listDebugReports();
                        }, function(error) {
                           kimchi.message.error(error.responseJSON.reason);
                        });
                    });
                }
            }, {
                id: reportGridID + '-download-button',
                label: i18n['KCHDR6010M'],
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if(!report) {
                        return;
                    }

                    kimchi.downloadReport({
                        file: report['uri']
                    });
                }
            }],
            onRowSelected: function(row) {
                var report = reportGrid.getSelected();
                // Only enable report buttons if the selected line is not a
                // pending report
                if (report['time'] == i18n['KCHDR6007M']) {
                    var gridElement = $('#'+ reportGridID);
                    var row = $('tr:contains(' + report['name'] + ')', gridElement);
                    enableReportButtons(false);
                    row.attr('class', '');
                }
                else {
                    enableReportButtons(true);
                }
            },
            frozenFields: [],
            fields: [{
                name: 'name',
                label: i18n['KCHDR6003M'],
                'class': 'debug-report-name'
            }, {
                name: 'time',
                label: i18n['KCHDR6005M'],
                'class': 'debug-report-time'
            }],
            data: reports
        });
    };

    var getPendingReports = function() {
        var reports = []
        var filter = 'status=running&target_uri=' + encodeURIComponent('^/debugreports/*')

        kimchi.getTasksByFilter(filter, function(tasks) {
            for(var i = 0; i < tasks.length; i++) {
                reportName = tasks[i].target_uri.replace(/^\/debugreports\//, '') || i18n['KCHDR6012M'];
                reports.push({'name': reportName, 'time': i18n['KCHDR6007M']})

                if(kimchi.trackingTasks.indexOf(tasks[i].id) >= 0) {
                    continue;
                }

                kimchi.trackTask(tasks[i].id, function(result) {
                    kimchi.topic('kimchi/debugReportAdded').publish();
                }, function(result) {
                    // Error message from Async Task status
                    if (result['message']) {
                        var errText = result['message'];
                    }
                    // Error message from standard kimchi exception
                    else {
                        var errText = result['responseJSON']['reason'];
                    }
                    result && kimchi.message.error(errText);
                    kimchi.topic('kimchi/debugReportAdded').publish();
                }, null);
            }
        }, null, true);

        return reports;
    };

    var listDebugReports = function() {
        kimchi.listReports(function(reports) {
            pendingReports = getPendingReports();
            allReports = pendingReports.concat(reports);
            $('#debug-report-section').removeClass('hidden');

            // Row selection will be cleared so disable buttons here
            enableReportButtons(false);

            if(reportGrid) {
                reportGrid.setData(allReports);
            }
            else {
                initReportGrid(allReports);
            }

            // Set id-debug-img to pending reports
            // It will display a loading icon
            var gridElement = $('#' + reportGridID);
                $.each($('td:contains(' + i18n['KCHDR6007M']  + ')', gridElement), function(index, row) {
                $(row).parent().addClass('no-hover');
                $(row).attr('id', 'id-debug-img');
            });
        }, function(error) {
            if(error['status'] == 403) {
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
            title : i18n['KCHAPI6004M'],
            content : i18n['KCHHOST6008M'],
            confirm : i18n['KCHAPI6002M'],
            cancel : i18n['KCHAPI6003M']
        };

        kimchi.confirm(settings, function() {
            kimchi.shutdown(params);
            $(shutdownButtonID).prop('disabled', true);
            $(restartButtonID).prop('disabled', true);
            // Check if there is any VM is running.
            kimchi.listVMs(function(vms) {
                for(var i = 0; i < vms.length; i++) {
                    if(vms[i]['state'] === 'running') {
                        kimchi.message.error.code('KCHHOST6001E');
                        $(shutdownButtonID).prop('disabled', false);
                        $(restartButtonID).prop('disabled', false);
                        return;
                    }
                }

            });
        }, function() {
        });
    };

    var initPage = function() {
        $('#host-info-container .section-header').each(function(i, header) {
            $('<span class="arrow"></span>').prependTo(header);
            var toExpand = $(header).attr('aria-expanded') !== 'false';
            expand(header, toExpand);
        });

        $('#host-info-container').on('click', '.section-header', function(event) {
            var toExpand = $(this).attr('aria-expanded') === 'false';
            expand(this, toExpand);
        });

        $('#host-button-shutdown').on('click', function(event) {
            shutdownHost(null);
        });

        $('#host-button-restart').on('click', function(event) {
            shutdownHost({
                reboot: true
            });
        });

        var setupUI = function() {
            if (kimchi.capabilities == undefined) {
                setTimeout(setupUI, 2000);
                return;
            }

            if((kimchi.capabilities['repo_mngt_tool']) && (kimchi.capabilities['repo_mngt_tool']!="None")) {
                initRepositoriesGrid(kimchi.capabilities['repo_mngt_tool']);
                $('#repositories-section').switchClass('hidden', kimchi.capabilities['repo_mngt_tool']);
                kimchi.topic('kimchi/repositoryAdded')
                    .subscribe(listRepositories);
                kimchi.topic('kimchi/repositoryUpdated')
                    .subscribe(listRepositories);
                kimchi.topic('kimchi/repositoryDeleted')
                    .subscribe(listRepositories);
            }

            if(kimchi.capabilities['update_tool']) {
                $('#software-update-section').removeClass('hidden');
                initSoftwareUpdatesGrid();
                kimchi.topic('kimchi/softwareUpdated')
                    .subscribe(listSoftwareUpdates);
                $('#software-updates-progress-container').accordion({
                    collapsible: true
                });
            }

            if(kimchi.capabilities['system_report_tool']) {
                listDebugReports();
                kimchi.topic('kimchi/debugReportAdded')
                    .subscribe(listDebugReports);
                kimchi.topic('kimchi/debugReportRenamed')
                    .subscribe(listDebugReports);
            }
        };
        setupUI();
    };

    kimchi.getHost(function(data) {
        var htmlTmpl = $('#host-tmpl').html();
        data['logo'] = data['logo'] || '';
        data['memory'] = kimchi.formatMeasurement(data['memory'], {
            fixed: 2
        });
        var templated = kimchi.substitute(htmlTmpl, data);
        $('#host-content-container').html(templated);

        initPage();
        initTracker();
    });

    var StatsMgr = function() {
        var statsArray = {
            cpu: {
                u: {
                    type: 'percent',
                    legend: i18n['KCHHOST6002M'],
                    points: []
                }
            },
            memory: {
                u: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    legend: i18n['KCHHOST6003M'],
                    points: []
                }
            },
            diskIO: {
                r: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['KCHHOST6004M'],
                    points: []
                },
                w: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['KCHHOST6005M'],
                    'class': 'disk-write',
                    points: []
                }
            },
            networkIO: {
                r: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['KCHHOST6006M'],
                    points: []
                },
                s: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    unit: 'B/s',
                    legend: i18n['KCHHOST6007M'],
                    'class': 'network-sent',
                    points: []
                }
            }
        };
        var SIZE = 20;
        var cursor = SIZE;

        var add = function(stats) {
            for(var key in stats) {
                var item = stats[key];
                for(var metrics in item) {
                    var value = item[metrics]['v'];
                    var max = item[metrics]['max'];
                    var unifiedMetrics = statsArray[key][metrics];
                    var ps = unifiedMetrics['points'];
                    if(!Array.isArray(value)){
                        ps.push(value);
                        if(ps.length > SIZE + 1) {
                            ps.shift();
                        }
                    }
                    else{
                        ps=ps.concat(value);
                        ps.splice(0, ps.length-SIZE-1);
                        unifiedMetrics['points']=ps;
                    }
                    if(max !== undefined) {
                        unifiedMetrics['max'] = max;
                    }
                    else {
                        if(unifiedMetrics['type'] !== 'value') {
                            continue;
                        }
                        max = -Infinity;
                        $.each(ps, function(i, value) {
                            if(value > max) {
                                max = value;
                            }
                        });
                        if(max === 0) {
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
            for(var k in stats) {
                var obj = stats[k];
                var line = {
                    type: obj['type'],
                    base: obj['base'],
                    unit: obj['unit'],
                    fixed: obj['fixed'],
                    legend: obj['legend']
                };
                if(obj['max']) {
                    line['max'] = obj['max'];
                }
                if(obj['class']) {
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
          for(var key in charts) {
              var chart = charts[key];
              chart.updateUI(statsPool.get(key));
          }
      };

      var self = this;

      var UnifyStats = function(stats) {
          var result= {
              cpu: {
                  u: {
                      v: stats['cpu_utilization']
                  }
              },
              memory: {
                  u: {
                  }
              },
              diskIO: {
                  r: {
                      v: stats['disk_read_rate']
                  },
                  w: {
                      v: stats['disk_write_rate']
                  }
              },
              networkIO: {
                  r: {
                      v: stats['net_recv_rate']
                  },
                  s: {
                      v: stats['net_sent_rate']
                  }
              }
          };
          if(Array.isArray(stats['memory'])){
              result.memory.u['v']=[];
              result.memory.u['max']=-Infinity;
              for(var i=0;i<stats['memory'].length;i++){
                  result.memory.u['v'].push(stats['memory'][i]['avail']);
                  result.memory.u['max']=Math.max(result.memory.u['max'],stats['memory'][i]['total']);
              }
          }
          else {
              result.memory.u['v']=stats['memory']['avail'],
              result.memory.u['max']=stats['memory']['total']
          }
          return(result);
      };


      var statsCallback = function(stats) {
              var unifiedStats = UnifyStats(stats);
              statsPool.add(unifiedStats);
              for(var key in charts) {
                  var chart = charts[key];
                  chart.updateUI(statsPool.get(key));
              }
              timer = setTimeout(function() {
                  continueTrack();
              }, 1000);
          };

      var track = function() {
          kimchi.getHostStatsHistory(statsCallback,
            function() {
                continueTrack();
            });
      };

      var continueTrack = function() {
          kimchi.getHostStats(statsCallback,
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
        if(kimchi.hostTimer) {
            kimchi.hostTimer.stop();
            delete kimchi.hostTimer;
        }

        var trackedCharts = {
            cpu: new kimchi.widget.LineChart({
                id: 'chart-cpu',
                node: 'container-chart-cpu',
                type: 'percent'
            }),
            memory: new kimchi.widget.LineChart({
                id: 'chart-memory',
                node: 'container-chart-memory',
                type: 'value'
            }),
            diskIO: new kimchi.widget.LineChart({
                id: 'chart-disk-io',
                node: 'container-chart-disk-io',
                type: 'value'
            }),
            networkIO: new kimchi.widget.LineChart({
                id: 'chart-network-io',
                node: 'container-chart-network-io',
                type: 'value'
            })
        };

        if(kimchi.hostTimer) {
            kimchi.hostTimer.setCharts(trackedCharts);
        }
        else {
            kimchi.hostTimer = new Tracker(trackedCharts);
            kimchi.hostTimer.start();
        }
    };

    $('#host-root-container').on('remove', function() {
        if(kimchi.hostTimer) {
            kimchi.hostTimer.stop();
            delete kimchi.hostTimer;
            }

        repositoriesGrid && repositoriesGrid.destroy();
        kimchi.topic('kimchi/repositoryAdded')
            .unsubscribe(listRepositories);
        kimchi.topic('kimchi/repositoryUpdated')
            .unsubscribe(listRepositories);
        kimchi.topic('kimchi/repositoryDeleted')
            .unsubscribe(listRepositories);

        softwareUpdatesGrid && softwareUpdatesGrid.destroy();
        kimchi.topic('kimchi/softwareUpdated').unsubscribe(listSoftwareUpdates);

        reportGrid && reportGrid.destroy();
        kimchi.topic('kimchi/debugReportAdded').unsubscribe(listDebugReports);
        kimchi.topic('kimchi/debugReportRenamed').unsubscribe(listDebugReports);
    });
};
