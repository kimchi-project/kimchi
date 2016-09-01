/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2013-2016
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

// init Guest Filter List global variable
var guestFilterList;
var listFiltered;

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
        var content_msg_1 = i18n['KCHVM6003M'].replace('%1', '<strong>'+vm_id+'</strong>');
        var content_msg_2 = i18n['KCHVM6009M'].replace('%1', '<strong>'+vm_id+'</strong>');
        var content_msg = vm_persistent ? content_msg_1 : content_msg_2;
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
    var confirmMessage = i18n['KCHVM6007M'].replace('%1', '<strong>'+vm_id+'</strong>');
    var settings = {
        title: i18n['KCHVM6006M'],
        content: confirmMessage,
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
        var confirmMessage = i18n['KCHVM6005M'].replace('%1', '<strong>'+vm_id+'</strong>');
        var settings = {
            title: i18n['KCHVM6004M'],
            content: confirmMessage,
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
    var confirmMessage = i18n['KCHVM6001M'].replace('%1', '<strong>'+vm_id+'</strong>');
    var settings = {
        title: i18n['KCHVM6008M'],
        content: confirmMessage,
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

kimchi.vmmigrate = function(event) {
    var button = event.target;
    var vm = $(button).closest('li[name=guest]');
    var vm_id = $(vm).attr("id");
    kimchi.selectedGuest = vm_id;
    wok.window.open('plugins/kimchi/guest-migration.html');
};

kimchi.vmclone = function(event) {
    var button = event.target;
    var vm = $(button).closest('li[name=guest]');
    var vm_id = $(vm).attr("id");
    kimchi.selectedGuest = vm_id;
    wok.window.open('plugins/kimchi/guest-clone.html');
};

kimchi.openVmSerialConsole = function(event) {
    var button = event.target;
    var vm = $(button).closest('li[name=guest]');
    kimchi.serialToVM($(vm).attr('id'));
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

kimchi.initGuestFilter = function() {
    // Create the list with the css classes that could be filtered at
    // the first click at the Filter Input Field
    $('#search_input').one('keyup', function(event) {
        var options = {
            valueNames: ['title', 'distro-icon', 'processors-percentage', 'memory-percentage', 'storage-percentage', 'network-percentage']
        };
        guestFilterList = new List('guest-content-container', options);
    });
};

kimchi.resetGuestFilter = function() {
    if (guestFilterList) {
        $('#search_input').val();
        listFiltered = false;
    }
};


kimchi.initClone = function() {
    var numTimesToClone = $('#numberClone').val();
    for (var i = 0; i < numTimesToClone; i++) {
        kimchi.cloneGuest(kimchi.selectedGuest, function(data) {
            kimchi.listVmsAuto();
        });
    }
   wok.window.close();
};

kimchi.guestSetRequestHeader = function(xhr) {
    xhr.setRequestHeader('Accept', 'text/html');
};

kimchi.toggleGuestsGallery = function() {
    $(".wok-guest-list, .wok-guest-gallery").toggleClass("wok-guest-list wok-guest-gallery");
    $(".wok-list, .wok-gallery").toggleClass("wok-list wok-gallery");
    var text = $('#guest-gallery-table-button span.text').text();
    $('#guest-gallery-table-button span.text').text(text == i18n['KCHTMPL6005M'] ? i18n['KCHTMPL6004M'] : i18n['KCHTMPL6005M']);
    var buttonText = $('#guest-gallery-table-button span.text').text();
    if (buttonText.indexOf("Gallery") !== -1) {
        // Currently in list view
        kimchi.setGuestView("guestView", "list");
     } else {
        // Currently in gallery
        kimchi.setGuestView("guestView", "gallery");
     }
};

kimchi.setGuestView = function(name, value) {
    window.localStorage.setItem(name, value);
};

kimchi.readGuestView = function(name) {
    var viewName = window.localStorage.getItem(name);
    if (viewName !== "") {
        return viewName;
    } else {
        return null;
    }
};

kimchi.showGuestGallery = function() {
    $(".wok-guest-list").addClass("wok-guest-gallery");
    $(".wok-list").addClass("wok-gallery");
    $(".wok-guest-gallery").removeClass("wok-guest-list");
    $(".wok-gallery").removeClass("wok-list");
    $('#guest-gallery-table-button span.text').text(i18n['KCHTMPL6004M']);
};

kimchi.showGuestList = function() {
    $(".wok-guest-list").removeClass("wok-guest-gallery");
    $(".wok-list").removeClass("wok-gallery");
    $(".wok-guest-gallery").addClass("wok-guest-list");
    $(".wok-gallery").addClass("wok-list");
    $('#guest-gallery-table-button span.text').text(i18n['KCHTMPL6005M']);
};

kimchi.guest_main = function() {
    $('body').addClass('wok-list');
    var viewFound = kimchi.readGuestView("guestView");
    if (viewFound) {
        if(viewFound === "gallery") {
            // should be showing gallery
            kimchi.showGuestGallery();
        } else {
            // Should be showing list
            kimchi.showGuestList();
        }
    } else {
        // Default to showing list
        kimchi.showGuestList();
    }
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

    $('#guest-gallery-table-button').on('click', function(event) {
        kimchi.toggleGuestsGallery();
    });

    kimchi.resetGuestFilter();
    kimchi.initGuestFilter();
    kimchi.listVmsAuto();
};

kimchi.guest_clonevm_main = function() {
   kimchi.initCloneDialog();
};

kimchi.initCloneDialog = function(callback) {
    $("#numberClone").val("1");
    $("#cloneFormOk").on("click", function() {
        //Check if input is a number
        var numClone = parseInt($('#numberClone').val());
        var err = "";
        if (isNaN(numClone)) {
            err = i18n['KCHVM0001E'];
            wok.message.error(err,'#alert-modal-container');
        } else {
            $("#cloneFormOk").prop("disabled", true);
            kimchi.initClone();
        }
   });
};


kimchi.createGuestLi = function(vmObject, prevScreenImage, openMenu) {
    var result;
    if (typeof kimchi.guestElem !== 'undefined') {
        result = kimchi.guestElem.clone();
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
        var guestTitle = result.find('.title').attr({ 'val': vmObject.name, 'title': vmObject.name });
        guestTitle.html(vmObject.name);

        if (vmObject.screenshot !== null) {
            var scrensh = result.find('.screenshot').css('background-image', 'url(' + vmObject.screenshot + ')');
            scrensh.attr('title', vmObject.name);
        } else {
            var scrensh = result.find('.screenshot').css('background-image', 'none');
            scrensh.attr('title', vmObject.name);
        }

        //Add the OS Type and Icon
        var osType = result.find('.column-type.distro-icon');
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
        } else if (vmObject.icon !== null) {
            osType.css('background-image', vmObject.icon);
            osType.attr('val', 'Unknown');
            osType.html('Unknown');
        } else {
            //Unknown
            osType.addClass('icon-unknown');
            osType.attr('val', 'Unknown');
            osType.html('Unknown');
        }
        //Add the OS Icon to VM name in Gallery View
        var osName = result.find('.column-name.distro-icon');
        if (vmObject.icon == 'plugins/kimchi/images/icon-fedora.png') {
            osName.addClass('icon-fedora');
        } else if (vmObject.icon == 'plugins/kimchi/images/icon-ubuntu.png') {
            osName.addClass('icon-ubuntu');
        } else if (vmObject.icon == 'plugins/kimchi/images/icon-centos.png') {
            osName.addClass('icon-centos');
        } else if (vmObject.icon == 'plugins/kimchi/images/icon-opensuse.png') {
            osName.addClass('icon-opensuse');
        } else if (vmObject.icon == 'plugins/kimchi/images/icon-gentoo.png') {
            osName.addClass('icon-gentoo');
        } else if (vmObject.icon == 'plugins/kimchi/images/icon-debian.png') {
            osName.addClass('icon-debian');
        } else if (vmObject.icon !== null) {
            osName.css('background-image', vmObject.icon);
        } else {
            osName.addClass('icon-unknown');
        }

        //Setup the VM console thumbnail display
        var curImg = vmObject.icon;
        if (vmObject.screenshot) {
            curImg = vmObject.screenshot.replace(/^\//, '');
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
        if (!(vmObject.isCloning || vmObject.isCreating || vmObject.isMigrating)) {
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

        var serialConsoleLinkActions = guestActions.find("[name=vm-serial-console]");
        serialConsoleLinkActions.on("click", function(event) {
            event.preventDefault();
            kimchi.openVmSerialConsole(event);
        });

        var consoleActions = guestActions.find("[name=vm-console]");
        var consoleLinkActions = result.find(".vnc-link");

        if (((vmObject.graphics['type'] == 'vnc') || (vmObject.graphics['type'] == 'spice')) && (!vmPoweredOffBool)) {
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
            result.find('.vnc-link').css("display", "none");
            result.find('.column-vnc').html('--');
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
        if (!(vmObject.isCloning || vmObject.isCreating || vmObject.isMigrating)) {

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
                kimchi.vmclone(event);
            });
            guestActions.find("[name=vm-migrate]").on('click', function(event) {
                event.preventDefault();
                kimchi.vmmigrate(event);
            });
        } else {
            guestActions.find('.btn').attr('disabled', true);
            result.find('.guest-done').addClass('hidden');
            result.find('.guest-state').addClass('hidden');
            result.find('.guest-pending').removeClass('hidden');
            pendingText = result.find('.guest-pending .text')
            if (vmObject.isCloning)
                pendingText.text(i18n['KCHAPI6009M']);
            else if (vmObject.isMigrating)
                pendingText.text(i18n['KCHAPI6012M']);
            else
                pendingText.text(i18n['KCHAPI6008M']);
        }
    }
    return result;
};


kimchi.listVmsAuto = function() {
    $('#guests-root-container > .wok-mask').removeClass('hidden');
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
                    var guestName = guestUri.split('/')[4]
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
                    var guestName = guestUri.split('/')[4]
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

        var trackFailedCloningGuests = function() {
            kimchi.getTasksByFilter('status=failed&target_uri=' + encodeURIComponent('^/plugins/kimchi/vms/.+/clone'), function(tasks) {
                for (var i = 0; i < tasks.length; i++) {
                    if (kimchi.trackingTasks.indexOf(tasks[i].id) == -1)
                        kimchi.trackTask(tasks[i].id, null, function(err) {
                           wok.message.error(err.message);
                        }, null);
                }
            }, null, true);
        };

        var getMigratingGuests = function() {
            var guests = [];
            kimchi.getTasksByFilter('status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/vms/.+/migrate'), function(tasks) {
                for (var i = 0; i < tasks.length; i++) {
                    var guestUri = tasks[i].target_uri;
                    var guestName = guestUri.split('/')[4]
                    guests.push($.extend({}, kimchi.sampleGuestObject, {
                        name: guestName,
                        isMigrating: true
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
                    // Some clone tasks may fail before being tracked. Show
                    // error message for them.
                    trackFailedCloningGuests();
                    var migrated = getMigratingGuests();
                    for (i = migrated.length - 1; i >= 0; i--) {
                        for (j = result.length - 1; j >= 0; j--) {
                            if (result[j].name == migrated[i].name) result.splice(j, 1);
                        }
                    }
                    result = getMigratingGuests().concat(result);
                    result = getCloningGuests().concat(result);
                    result = getCreatingGuests().concat(result);
                    if (result.length) {
                        var listHtml = '';
                        var guestTemplate = kimchi.guestTemplate;
                        var currentConsoleImages = kimchi.getVmsCurrentConsoleImgs();
                        var openMenuGuest = kimchi.getOpenMenuVmId();
                        $('#guestList').empty();
                        $('.grid-control').removeClass('hidden');
                        $('#guestListField').show();
                        $('#noGuests').hide();
                        // Check if the list is being filtered, if true populate
                        // the #guestList only with the filtered elements
                        listFiltered = ((guestFilterList != undefined) && (guestFilterList.matchingItems.length != result.length) && $('#search_input').val() != "");
                        if (!listFiltered) {
                            $.each(result, function(index, vm) {
                                var guestLI = kimchi.createGuestLi(vm, currentConsoleImages[vm.name], vm.name == openMenuGuest);
                                $('#guestList').append(guestLI);
                            });
                        } else {
                            $.each(result, function(index, vm) {
                                $.each(guestFilterList.matchingItems, function(index, listFiltered) {
                                    if (listFiltered._values.title === vm.name) {
                                        var guestLI = kimchi.createGuestLi(vm, currentConsoleImages[vm.name], vm.name == openMenuGuest);
                                        $('#guestList').append(guestLI);
                                    }
                                });
                            });
                        }
                        $('#guests-root-container > .wok-mask').fadeOut(300, function() {
                        });
                    } else {
                        $('.grid-control').addClass('hidden');
                        $('#guestListField').hide();
                        $('#noGuests').show();
                        $('#guests-root-container > .wok-mask').fadeOut(300, function() {});
                    }
                }
                kimchi.setListVMAutoTimeout();
            },
            function(errorResponse, textStatus, errorThrown) {
                if (errorResponse.responseJSON && errorResponse.responseJSON.reason) {
                    wok.message.error(errorResponse.responseJSON.reason);
                    $('#guests-root-container > .wok-mask').fadeOut(300, function() {
                        $('#guests-root-container > .wok-mask').addClass('hidden');
                    });
                }
                kimchi.setListVMAutoTimeout();
            });
    } else {
        clearTimeout(kimchi.vmTimeout);
        kimchi.setListVMAutoTimeout();
    }
};

kimchi.editTemplate = function(guestTemplate, oldPopStat) {
    if (oldPopStat) {
        return guestTemplate.replace("vm-action", "vm-action open");
    }
    return guestTemplate;
};

kimchi.setListVMAutoTimeout = function() {
    kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
}
