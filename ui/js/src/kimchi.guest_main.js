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

kimchi.sampleGuestObject = {
    "name": "",
    "uuid": "",
    "state": "shutoff",
    "persistent": true,
    "icon": null,
    "cpus": 0,
    "memory": 0,
    "stats": {
        "net_throughput": 0,
        "io_throughput_peak": 100,
        "cpu_utilization": 0,
        "mem_utilization": 0,
        "io_throughput": 0,
        "net_throughput_peak": 100
    },
    "screenshot": null,
    "graphics": {
        "passwd": null,
        "passwdValidTo": null,
        "type": "vnc",
        "port": null,
        "listen": "127.0.0.1"
    },
    "users": [],
    "groups": [],
    "access": "full"
};

kimchi.vmstart = function(event) {
    var button = event.target;
    if (!$(button).hasClass('loading')) {
        $(button).addClass('loading');
        var vm = $(button).closest('li[name=guest]');
        var vm_id = $(vm).attr("id");
        // setting up css class when starting
        $(vm).find('.guest-state').removeClass('shutoff');
        $(vm).find('.guest-state').addClass('starting');
        $(vm).find('.progress').css("display", "none");
        $(vm).find('.percentage - label').html('--');
        $(vm).find('.measure-label').html('--');
        $(vm).find('.guest-actions').css("margin-top", "3px");
        $(vm).addClass('inactive');
        $(vm).find('.distro-icon').addClass('inactive');
        $(vm).find('.vnc-link').css("display", "none");
        $(vm).find('.column-vnc').html('--');
        kimchi.startVM(vm_id, function(result) {
            $(button).removeClass('loading');
            kimchi.listVmsAuto();
        }, function(err) {
            $(button).removeClass('loading');
            wok.message.error(err.responseJSON.reason);
        });
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmsuspend = function(event) {
    var button = event.target;
    if (!$(button).hasClass('pause-gray')) {
        $(button).addClass('pause-gray');
        var vm = $(button).closest('li[name=guest]');
        var vm_id = $(vm).attr("id");
        kimchi.suspendVM(vm_id, function(result) {
            $(button).removeClass('pause-gray');
            kimchi.listVmsAuto();
        }, function(err) {
            $(button).removeClass('pause-gray');
            wok.message.error(err.responseJSON.reason);
        });
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmresume = function(event) {
    var button = event.target;
    if (!$(button).hasClass('resume-gray')) {
        $(button).addClass('resume-gray');
        var vm = $(button).closest('li[name=guest]');
        var vm_id = vm.attr("id");
        kimchi.resumeVM(vm_id, function(result) {
            $(button).removeClass('resume-gray');
            kimchi.listVmsAuto();
        }, function(err) {
            $(button).removeClass('resume-gray');
            wok.message.error(err.responseJSON.reason);
        });
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmpoweroff = function(event) {
    var button = event.target;
    if (!$(button).hasClass('loading')) {
        $(button).addClass('loading');
        var vm = $(button).closest('li[name=guest]');
        var vm_id = vm.attr("id");
        var vmObject = vm.data();
        var vm_persistent = vmObject.persistent == true;
        var content_msg = vm_persistent ? i18n['KCHVM6003M'] :
            i18n['KCHVM6009M'];
        var settings = {
            title: i18n['KCHVM6002M'],
            content: content_msg,
            confirm: i18n['KCHAPI6002M'],
            cancel: i18n['KCHAPI6003M']
        };
        wok.confirm(settings, function() {
            kimchi.poweroffVM(vm_id, function(result) {
                $(button).removeClass('loading');
                kimchi.listVmsAuto();
            }, function(err) {
                wok.message.error(err.responseJSON.reason);
            });
        }, function() {});
    } else {
        event.preventDefault();
        event.stopPropagation();
    }
};

kimchi.vmshutdown = function(event) {
    var button = event.target;
    var vm = $(button).closest('li[name=guest]');
    var vm_id = vm.attr("id");
    var settings = {
        title: i18n['KCHVM6006M'],
        content: i18n['KCHVM6007M'],
        confirm: i18n['KCHAPI6002M'],
        cancel: i18n['KCHAPI6003M']
    };
    wok.confirm(settings, function() {
        kimchi.shutdownVM(vm_id, function(result) {
            kimchi.listVmsAuto();
        }, function(err) {
            wok.message.error(err.responseJSON.reason);
        });
    }, function() {});
};

kimchi.vmreset = function(event) {
    var button = event.target;
    if (!$(button).hasClass('loading')) {
        $(button).addClass('loading');
        var vm = $(button).closest('li[name=guest]');
        var vm_id = $(vm).attr("id");
        var settings = {
            title: i18n['KCHVM6004M'],
            content: i18n['KCHVM6005M'],
            confirm: i18n['KCHAPI6002M'],
            cancel: i18n['KCHAPI6003M']
        };
        wok.confirm(settings, function() {
            // setting up css class when resetting
            $(vm).find('.guest-state').removeClass('running');
            $(vm).find('.guest-state').addClass('resetting');
            $(vm).find('.fa-spin').addClass('active');
            kimchi.resetVM(vm_id, function(result) {
                $(button).removeClass('loading');
                kimchi.listVmsAuto();
            }, function(err) {
                $(button).removeClass('loading');
                wok.message.error(err.responseJSON.reason);
            });
        }, function() {});
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmdelete = function(event) {
    var button = event.target;
    var vm = $(button).closest('li[name=guest]');
    var vm_id = $(vm).attr("id");
    var settings = {
        title: i18n['KCHVM6008M'],
        content: i18n['KCHVM6001M'],
        confirm: i18n['KCHAPI6002M'],
        cancel: i18n['KCHAPI6003M']
    };
    wok.confirm(settings, function() {
        kimchi.deleteVM(vm_id, function(result) {
            kimchi.listVmsAuto();
        }, function(err) {
            wok.message.error(err.responseJSON.reason);
        });
    }, function() {});
};

kimchi.vmedit = function(event) {
    var button = event.target;
    var vm = $(button).closest('li[name=guest]');
    var vm_id = $(vm).attr("id");
    kimchi.selectedGuest = vm_id;
    wok.window.open({
        url: 'plugins/kimchi/guest-edit.html',
        close: function() {
            kimchi.clearGuestEdit();
        }
    });
};

kimchi.openVmConsole = function(event) {
    var button = event.target;
    var vm = $(button).closest('li[name=guest]');
    var vmObject = $(vm).data();
    if (vmObject.graphics['type'] == 'vnc') {
        kimchi.vncToVM($(vm).attr('id'));
    } else if (vmObject.graphics['type'] == 'spice') {
        kimchi.spiceToVM($(vm).attr('id'));
    }

};

kimchi.getVmsCurrentConsoleImgs = function() {
    var res = new Object();
    $('#guestList').children().each(function() {
        res[$(this).attr('id')] = $(this).find('img.imgactive').attr('src');
    })
    return res;
};

kimchi.getOpenMenuVmId = function() {
    var result;
    var openMenu = $('#guestList div[name="actionmenu"] .dropdown-menu:visible');
    if (openMenu) {
        var li_element = openMenu.closest('li');
        result = li_element.attr('id');
    }
    return result;
};

kimchi.listVmsAuto = function() {
    //Check if the actions button is opened or not,
    //if opended stop the reload of the itens until closed
    var $isDropdownOpened = $('[name="guest-actions"] ul.dropdown-menu').is(":visible");
    if (!$isDropdownOpened) {
        if (kimchi.vmTimeout) {
            clearTimeout(kimchi.vmTimeout);
        }
        var getCreatingGuests = function() {
            var guests = [];
            kimchi.getTasksByFilter('status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/vms/[^/]+$'), function(tasks) {
                for (var i = 0; i < tasks.length; i++) {
                    var guestUri = tasks[i].target_uri;
                    var guestName = guestUri.split('/')[2]
                    guests.push($.extend({}, kimchi.sampleGuestObject, {
                        name: guestName,
                        isCreating: true
                    }));
                    if (kimchi.trackingTasks.indexOf(tasks[i].id) == -1)
                        kimchi.trackTask(tasks[i].id, null, function(err) {
                            wok.message.error(err.message);
                        }, null);
                }
            }, null, true);
            return guests;
        };
        var getCloningGuests = function() {
            var guests = [];
            kimchi.getTasksByFilter('status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/vms/.+/clone'), function(tasks) {
                for (var i = 0; i < tasks.length; i++) {
                    var guestUri = tasks[i].target_uri;
                    var guestName = guestUri.split('/')[2]
                    guests.push($.extend({}, kimchi.sampleGuestObject, {
                        name: guestName,
                        isCloning: true
                    }));
                    if (kimchi.trackingTasks.indexOf(tasks[i].id) == -1)
                        kimchi.trackTask(tasks[i].id, null, function(err) {
                            wok.message.error(err.message);
                        }, null);
                }
            }, null, true);
            return guests;
        };
        kimchi.listVMs(function(result, textStatus, jqXHR) {
                if (result && textStatus == "success") {
                    result = getCloningGuests().concat(result);
                    result = getCreatingGuests().concat(result);
                    if (result.length) {
                        var listHtml = '';
                        var guestTemplate = kimchi.guestTemplate;
                        var currentConsoleImages = kimchi.getVmsCurrentConsoleImgs();
                        var openMenuGuest = kimchi.getOpenMenuVmId();
                        $('#guestList').empty();
                        $('#guestListField').show();
                        $('#noGuests').hide();

                        $.each(result, function(index, vm) {
                            var guestLI = kimchi.createGuestLi(vm, currentConsoleImages[vm.name], vm.name == openMenuGuest);
                            $('#guestList').append(guestLI);
                        });
                    } else {
                        $('#guestListField').hide();
                        $('#noGuests').show();
                    }
                }

                kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
            },
            function(errorResponse, textStatus, errorThrown) {
                if (errorResponse.responseJSON && errorResponse.responseJSON.reason) {
                    wok.message.error(errorResponse.responseJSON.reason);
                }
                kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
            });
    } else {
        clearTimeout(kimchi.vmTimeout);
        kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
    }
};


kimchi.createGuestLi = function(vmObject, prevScreenImage, openMenu) {
    var result = kimchi.guestElem.clone();

    //Setup the VM list entry
    var currentState = result.find('.guest-state');
    var vmRunningBool = (vmObject.state == "running");
    var vmSuspendedBool = (vmObject.state == "paused");
    var vmPoweredOffBool = (vmObject.state == "shutoff");
    var vmPersistent = (vmObject.persistent == true);

    if (vmObject.state !== 'undefined') {
        currentState.addClass(vmObject.state);
    };
    result.attr('id', vmObject.name);
    result.data(vmObject);

    //Add the Name
    var guestTitle = result.find('.title').attr('val', vmObject.name);
    guestTitle.html(vmObject.name);

    //Add the OS Type and Icon
    var osType = result.find('.distro-icon');
    console.log(vmObject);
    if (vmObject.icon == 'plugins/kimchi/images/icon-fedora.png') {
        osType.addClass('icon-fedora');
        osType.attr('val', 'Fedora');
        osType.html('Fedora');
    } else if (vmObject.icon == 'plugins/kimchi/images/icon-ubuntu.png') {
        osType.addClass('icon-ubuntu');
        osType.attr('val', 'Ubuntu');
        osType.html('Ubuntu');
    } else if (vmObject.icon == 'plugins/kimchi/images/icon-centos.png') {
        osType.addClass('icon-centos');
        osType.attr('val', 'Centos');
        osType.html('Centos');
    } else if (vmObject.icon == 'plugins/kimchi/images/icon-opensuse.png') {
        osType.addClass('icon-opensuse');
        osType.attr('val', 'openSUSE');
        osType.html('openSUSE');
    } else if (vmObject.icon == 'plugins/kimchi/images/icon-gentoo.png') {
        osType.addClass('icon-gentoo');
        osType.attr('val', 'Gentoo');
        osType.html('Gentoo');
    } else if (vmObject.icon == 'plugins/kimchi/images/icon-debian.png') {
        osType.addClass('icon-debian');
        osType.attr('val', 'Debian');
        osType.html('Debian');
    } else {
        //Unknown
        osType.addClass('icon-unknown');
        osType.attr('val', 'Unknown');
        osType.html('Unknown');
    }

    //Setup the VM console thumbnail display
    var curImg = vmObject.icon;
    if (vmObject.screenshot) {
        curImg = vmObject.screenshot.replace(/^\//,'');
    }
    var load_src = curImg || 'plugins/kimchi/images/icon-vm.png';
    var tile_src = prevScreenImage || vmObject['load-src'];
    var liveTile = result.find('div[name=guest-tile] > .tile');
    liveTile.addClass(vmObject.state);
    liveTile.find('.imgactive').attr('src', tile_src);
    var imgLoad = liveTile.find('.imgload');
    imgLoad.on('load', function() {
        var oldImg = $(this).parent().find('.imgactive');
        oldImg.removeClass("imgactive").addClass("imgload");
        oldImg.attr("src", "");
        $(this).addClass("imgactive").removeClass("imgload");
        $(this).off('load');
    });
    imgLoad.attr('src', load_src);

    //Link the stopped tile to the start action, the running tile to open the console, and the paused tile to resume
    if (!(vmObject.isCloning || vmObject.isCreating)) {
        if (vmPoweredOffBool) {
            liveTile.off("click", function(event) {
                event.preventDefault();
                kimchi.openVmConsole(event);
            });
            liveTile.off("click", function(event) {
                event.preventDefault();
                kimchi.vmresume(event);
            });
            liveTile.on("click", function(event) {
                event.preventDefault();
                kimchi.vmstart(event);
            });
            liveTile.hover("click", function(event) {
                event.preventDefault();
                $(this).find('.overlay').show()
            }, function(event) {
                $(this).find('.overlay').hide()
            });
        } else if (vmSuspendedBool) {
            liveTile.off("click", function(event) {
                event.preventDefault();
                kimchi.vmstart(event);
            });
            liveTile.off("click", function(event) {
                event.preventDefault();
                kimchi.openVmConsole(event);
            });
            liveTile.on("click", function(event) {
                event.preventDefault();
                kimchi.vmresume(event);
            });
            liveTile.hover("click", function(event) {
                event.preventDefault();
                $(this).find('.overlay').show()
            }, function(event) {
                $(this).find('.overlay').hide()
            });
            if (vmObject.state = "paused") {
                liveTile.find('.overlay').attr('src', "plugins/kimchi/images/theme-default/ac24_resume.png");
                liveTile.find('.overlay').attr('alt', "Resume");
            }
            liveTile.hover(function(event) {
                $(this).find('.overlay').show()
            }, function(event) {
                $(this).find('.overlay').hide()
            });
        } else {
            liveTile.off("click", function(event) {
                event.preventDefault();
                kimchi.vmstart(event);
            });
            liveTile.off("click", function(event) {
                event.preventDefault();
                kimchi.vmresume(event);
            });
            liveTile.on("click", function(event) {
                event.preventDefault();
                kimchi.openVmConsole(event);
            });
        }
    }

    //Setup progress bars
    if (!vmPoweredOffBool) {
        var cpuUtilization = 0;
        var cpuMaxThreshold = 80;
        var cpuMediumThreshold = 60;
        cpuUtilization = parseInt(vmObject.stats.cpu_utilization);
        result.find('.cpu-progress-bar').width(cpuUtilization + '%');
        result.find('.processors-percentage').html(cpuUtilization + '%');
        result.find('.medium-grey.cpu').width(cpuMaxThreshold + '%');
        result.find('.light-grey.cpu').width(cpuMediumThreshold + '%');

        var memoryUtilization = 0;
        var memoryMaxThreshold = 80;
        var memoryMediumThreshold = 60;
        memoryUtilization = parseInt(vmObject.stats.mem_utilization);
        result.find('.memory-progress-bar').width(memoryUtilization + '%');
        result.find('.memory-percentage').html(memoryUtilization + '%');
        result.find('.medium-grey.memory').width(memoryMaxThreshold + '%');
        result.find('.light-grey.memory').width(memoryMediumThreshold + '%');

        var ioThroughput = 0;
        var ioMaxThreshold = 80;
        var ioMediumThreshold = 60;
        ioValue = parseInt(vmObject.stats.io_throughput);
        ioThroughput = (ioValue * 100 / vmObject.stats.io_throughput_peak);
        result.find('.storage-progress-bar').width(ioThroughput + '%');
        result.find('.storage-percentage').html(Math.round(ioThroughput) + 'KB/s');
        result.find('.medium-grey.io').width(ioMaxThreshold + '%');
        result.find('.light-grey.io').width(ioMediumThreshold + '%');

        var netThroughput = 0;
        var netMaxThreshold = 80;
        var netMediumThreshold = 60;
        netValue = parseInt(vmObject.stats.net_throughput);
        netThroughput = (netValue * 100 / vmObject.stats.net_throughput_peak);
        result.find('.network-progress-bar').width(netThroughput + '%');
        result.find('.network-percentage').html(Math.round(netThroughput) + 'KB/s');
        result.find('.medium-grey.network').width(netMaxThreshold + '%');
        result.find('.light-grey.network').width(netMediumThreshold + '%');
    } else {
        result.find('.progress').css("display", "none");
        result.find('.percentage-label').html('--');
        result.find('.measure-label').html('--');
        result.find('.measure-label').html('--');
        result.find('.guest-actions').css("margin-top", "3px");
    }

    //Setup the VM Actions
    var guestActions = result.find("div[name=guest-actions]");
    guestActions.find(".shutoff-disabled").prop("disabled", !vmRunningBool);
    guestActions.find(".running-disabled").prop("disabled", vmRunningBool);
    guestActions.find(".non-persistent-disabled").prop("disabled", !vmPersistent);
    guestActions.find(".reset-disabled").prop("disabled", vmPoweredOffBool || !vmPersistent);
    guestActions.find(".pause-disabled").prop("disabled", vmPoweredOffBool || !vmPersistent);

    if (vmSuspendedBool) { //VM is paused
        //Hide Start
        guestActions.find(".running-hidden").hide();
        //Hide Pause button and menu
        guestActions.find(".pause-disabled").hide();
        guestActions.find(".pause-hidden").hide();
    }

    if (vmRunningBool) { //VM IS running
        //Hide Start
        guestActions.find(".running-hidden").hide();
        //Hide Resume
        guestActions.find(".resume-hidden").hide();
    }

    if (vmPoweredOffBool) { //VM is powered off
        result.addClass('inactive');
        result.find('.distro-icon').addClass('inactive');
        result.find('.vnc-link').css("display", "none");
        result.find('.column-vnc').html('--');        
        //Hide PowerOff
        guestActions.find(".shutoff-hidden").hide();
        //Hide Pause
        guestActions.find(".pause-hidden").hide();
        //Hide Resume
        guestActions.find(".resume-hidden").hide();
    }

    var consoleActions = guestActions.find("[name=vm-console]");
    var consoleLinkActions = result.find(".vnc-link");

    if ((vmObject.graphics['type'] == 'vnc') || (vmObject.graphics['type'] == 'spice')) {
        consoleActions.on("click", function(event) {
            event.preventDefault();
            kimchi.openVmConsole(event);
        });
        consoleLinkActions.on("click", function(event) {
            event.preventDefault();
            kimchi.openVmConsole(event);
        });
        consoleActions.show();
    } else { //we don't recognize the VMs supported graphics, so hide the menu choice
        consoleActions.hide();
        consoleActions.off("click", function(event) {
            event.preventDefault();
            kimchi.openVmConsole(event);
        });
        consoleLinkActions.off("click", function(event) {
            event.preventDefault();
            kimchi.openVmConsole(event);
        });
    }

    //Setup action event handlers
    if (!(vmObject.isCloning || vmObject.isCreating)) {

        guestActions.find("[name=vm-start]").on("click", function(event) {
            event.preventDefault();
            kimchi.vmstart(event);
        });
        guestActions.find("[name=vm-poweroff]").on("click", function(event) {
            event.preventDefault();
            kimchi.vmpoweroff(event);
        });
        if ((vmRunningBool) || (vmSuspendedBool)) {
            //If the guest is not running, do not enable reset; otherwise, reset is enabled (when running or paused)
            guestActions.find("[name=vm-reset]").on("click", function(event) {
                event.preventDefault();
                kimchi.vmreset(event);
            });
            //If the guest is not running, do not enable shutdown;otherwise, shutdown is enabled (when running or paused)
            guestActions.find("[name=vm-shutdown]").on("click", function(event) {
                event.preventDefault();
                kimchi.vmshutdown(event);
            });
        }

        if (vmSuspendedBool) {
            guestActions.find("[name=vm-resume]").on("click", function(event) {
                event.preventDefault();
                kimchi.vmresume(event);
            });
        }

        if (vmRunningBool) {
            guestActions.find("[name=vm-pause]").on("click", function(event) {
                event.preventDefault();
                kimchi.vmsuspend(event);
            });
        }

        guestActions.find("[name=vm-edit]").on("click", function(event) {
            event.preventDefault();
            kimchi.vmedit(event);
        });
        guestActions.find("[name=vm-delete]").on("click", function(event) {
            event.preventDefault();
            kimchi.vmdelete(event);
        });
        guestActions.find("[name=vm-clone]").on("click", function(event) {
            event.preventDefault();
            var guest = $(this).closest('li[name=guest]').attr("id");
            wok.confirm({
                title: i18n['KCHAPI6006M'],
                content: i18n['KCHVM6010M'],
                confirm: i18n['KCHAPI6002M'],
                cancel: i18n['KCHAPI6003M']
            }, function() {
                kimchi.cloneGuest(guest, function(data) {
                    kimchi.listVmsAuto();
                });
            }, null);
        });
    } else {
        guestActions.find('.btn').attr('disabled', true);
        result.find('.guest-pending').removeClass('hide-content');
        pendingText = result.find('.guest-pending .text')
        if (vmObject.isCloning)
            pendingText.text(i18n['KCHAPI6009M']);
        else
            pendingText.text(i18n['KCHAPI6008M']);
    }
    return result;
};

kimchi.guestSetRequestHeader = function(xhr) {
    xhr.setRequestHeader('Accept', 'text/html');
};

kimchi.guest_main = function() {
    if (wok.tabMode['guests'] === 'admin') {
        $('.tools').attr('style', 'display');
        $("#vm-add").on("click", function(event) {
            wok.window.open('plugins/kimchi/guest-add.html');
        });
    }
    kimchi.guestTemplate = $('#guest-tmpl').html();
    kimchi.guestElem = $('<div/>').html(kimchi.guestTemplate).find('li[name="guest"]');
    $('#guests-root-container').on('remove', function() {
        kimchi.vmTimeout && clearTimeout(kimchi.vmTimeout);
    });
    kimchi.listVmsAuto()
};

kimchi.editTemplate = function(guestTemplate, oldPopStat) {
    if (oldPopStat) {
        return guestTemplate.replace("vm-action", "vm-action open");
    }
    return guestTemplate;
};
