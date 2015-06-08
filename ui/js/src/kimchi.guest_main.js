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
    var button=$(this);
    if (!button.hasClass('loading')) {
        button.addClass('loading');
        var vm=$(this).closest('li[name=guest]');
        var vm_id=vm.attr("id");
        kimchi.startVM(vm_id, function(result) {
            button.removeClass('loading');
            kimchi.listVmsAuto();
            }, function(err) {
                button.removeClass('loading');
                kimchi.message.error(err.responseJSON.reason);
            }
        );
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmsuspend = function(event) {
    var button=$(this);
    if (!button.hasClass('pause-gray')) {
        button.addClass('pause-gray');
        var vm=$(this).closest('li[name=guest]');
        var vm_id=vm.attr("id");
        kimchi.suspendVM(vm_id, function(result) {
            button.removeClass('pause-gray');
            kimchi.listVmsAuto();
            }, function(err) {
                button.removeClass('pause-gray');
                kimchi.message.error(err.responseJSON.reason);
            }
        );
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmresume = function(event) {
    var button=$(this);
    if (!button.hasClass('resume-gray')) {
        button.addClass('resume-gray');
        var vm=$(this).closest('li[name=guest]');
        var vm_id=vm.attr("id");
        kimchi.resumeVM(vm_id, function(result) {
            button.removeClass('resume-gray');
            kimchi.listVmsAuto();
            }, function(err) {
                button.removeClass('resume-gray');
                kimchi.message.error(err.responseJSON.reason);
            }
        );
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmpoweroff = function(event) {
    var button=$(this);
    if (!button.hasClass('loading')) {
        button.addClass('loading');
        var vm=button.closest('li[name=guest]');
        var vm_id=vm.attr("id");
        var vmObject=vm.data();
        var vm_persistent=vmObject.persistent == true;
        var content_msg = vm_persistent ? i18n['KCHVM6003M'] :
            i18n['KCHVM6009M'];
        var settings = {
            title : i18n['KCHVM6002M'],
            content : content_msg,
            confirm : i18n['KCHAPI6002M'],
            cancel : i18n['KCHAPI6003M']
        };
        kimchi.confirm(settings, function() {
            kimchi.poweroffVM(vm_id, function(result) {
                button.removeClass('loading');
                kimchi.listVmsAuto();
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            });
        }, function() {
        });
    } else {
        event.preventDefault();
        event.stopPropagation();
    }
};

kimchi.vmshutdown = function(event){
    var vm=$(this).closest('li[name=guest]');
    var vm_id=vm.attr("id");
    var settings = {
        title : i18n['KCHVM6006M'],
        content : i18n['KCHVM6007M'],
        confirm : i18n['KCHAPI6002M'],
        cancel : i18n['KCHAPI6003M']
    };
    kimchi.confirm(settings, function() {
        kimchi.shutdownVM(vm_id, function(result) {
                kimchi.listVmsAuto();
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            }
        );
    }, function() {
    });
};

kimchi.vmreset = function(event){
    var vm=$(this).closest('li[name=guest]');
    var vm_id=vm.attr("id");
    var settings = {
        title : i18n['KCHVM6004M'],
        content : i18n['KCHVM6005M'],
        confirm : i18n['KCHAPI6002M'],
        cancel : i18n['KCHAPI6003M']
    };
    kimchi.confirm(settings, function() {
        kimchi.resetVM(vm_id, function(result) {
                kimchi.listVmsAuto();
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            }
        );
    }, function() {
    });
};

kimchi.vmdelete = function(event) {
    var vm = $(this).closest('li[name=guest]');
    var vm_id=vm.attr("id");
    var settings = {
        title : i18n['KCHVM6008M'],
        content : i18n['KCHVM6001M'],
        confirm : i18n['KCHAPI6002M'],
        cancel : i18n['KCHAPI6003M']
    };
    kimchi.confirm(settings, function() {
        kimchi.deleteVM(vm_id, function(result) {
            kimchi.listVmsAuto();
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    }, function() {
    });
};

kimchi.vmedit = function(event) {
    var vm = $(this).closest('li[name=guest]');
    var vm_id=vm.attr("id");
    kimchi.selectedGuest = vm_id;
    kimchi.window.open({
        url: 'guest-edit.html',
        close: function() {
            kimchi.clearGuestEdit();
        }
    });
};

kimchi.openVmConsole = function(event) {
    var vm=$(this).closest('li[name=guest]');
    var vmObject=vm.data();
    if (vmObject.graphics['type'] == 'vnc') {
        kimchi.vncToVM(vm.attr('id'));
    }
    else if (vmObject.graphics['type'] == 'spice') {
        kimchi.spiceToVM(vm.attr('id'));
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
    var openMenu = $('#guestList div[name="actionmenu"] .popover:visible');
    if(openMenu) {
        var li_element=openMenu.closest('li');
        result=li_element.attr('id');
    }
    return result;
};

kimchi.listVmsAuto = function() {
    if (kimchi.vmTimeout) {
        clearTimeout(kimchi.vmTimeout);
    }
    var getCreatingGuests = function(){
        var guests = [];
        kimchi.getTasksByFilter('status=running&target_uri='+encodeURIComponent('^/vms/[^/]+$'), function(tasks) {
            for(var i=0;i<tasks.length;i++){
                var guestUri = tasks[i].target_uri;
                var guestName = guestUri.split('/')[2]
                guests.push($.extend({}, kimchi.sampleGuestObject, {name: guestName, isCreating: true}));
                if(kimchi.trackingTasks.indexOf(tasks[i].id)==-1)
                    kimchi.trackTask(tasks[i].id, null, function(err){
                        kimchi.message.error(err.message);
                    }, null);
            }
        }, null, true);
        return guests;
    };
    var getCloningGuests = function(){
        var guests = [];
        kimchi.getTasksByFilter('status=running&target_uri='+encodeURIComponent('^/vms/.+/clone'), function(tasks) {
            for(var i=0;i<tasks.length;i++){
                var guestUri = tasks[i].target_uri;
                var guestName = guestUri.split('/')[2]
                guests.push($.extend({}, kimchi.sampleGuestObject, {name: guestName, isCloning: true}));
                if(kimchi.trackingTasks.indexOf(tasks[i].id)==-1)
                    kimchi.trackTask(tasks[i].id, null, function(err){
                        kimchi.message.error(err.message);
                    }, null);
            }
        }, null, true);
        return guests;
    };
    kimchi.listVMs(function(result, textStatus, jqXHR) {
        if (result && textStatus=="success") {
            result = getCloningGuests().concat(result);
            result = getCreatingGuests().concat(result);
            if(result.length) {
                var listHtml = '';
                var guestTemplate = kimchi.guestTemplate;
                var currentConsoleImages = kimchi.getVmsCurrentConsoleImgs();
                var openMenuGuest = kimchi.getOpenMenuVmId();
                $('#guestList').empty();
                $('#guestListField').show();
                $('#noGuests').hide();

                $.each(result, function(index, vm) {
                    var guestLI = kimchi.createGuestLi(vm, currentConsoleImages[vm.name], vm.name==openMenuGuest);
                    $('#guestList').append(guestLI);
                });
            } else {
                $('#guestListField').hide();
                $('#noGuests').show();
            }
        }

        kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
    }, function(errorResponse, textStatus, errorThrown) {
        if(errorResponse.responseJSON && errorResponse.responseJSON.reason) {
            kimchi.message.error(errorResponse.responseJSON.reason);
        }
        kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
    });
};

kimchi.createGuestLi = function(vmObject, prevScreenImage, openMenu) {
    var result=kimchi.guestElem.clone();
    
    //Setup the VM list entry
    var vmRunningBool=(vmObject.state=="running");
    var vmSuspendedBool = (vmObject.state=="paused");
    var vmPoweredOffBool = (vmObject.state=="shutoff");
    var vmPersistent = (vmObject.persistent == true);
    result.attr('id',vmObject.name);
    result.data(vmObject);

    //Add the Name
    var guestTitle=result.find('.title').attr('title',vmObject.name);
    guestTitle.html(vmObject.name);

    //Setup the VM console thumbnail display
    var curImg = vmObject.icon;
    if (vmObject.screenshot) {
        curImg = vmObject.screenshot.replace(/^\//,'');
    }
    var load_src = curImg || 'images/icon-vm.png';
    var tile_src = prevScreenImage || vmObject['load-src'];
    var liveTile=result.find('div[name=guest-tile] > .tile');
    liveTile.addClass(vmObject.state);
    liveTile.find('.imgactive').attr('src',tile_src);
    var imgLoad=liveTile.find('.imgload');
    imgLoad.on('load', function() {
                                     var oldImg=$(this).parent().find('.imgactive');
                                     oldImg.removeClass("imgactive").addClass("imgload");
                                     oldImg.attr("src","");
                                     $(this).addClass("imgactive").removeClass("imgload");
                                     $(this).off('load');
                                   });
    imgLoad.attr('src',load_src);

    //Link the stopped tile to the start action, the running tile to open the console, and the paused tile to resume
    if(!(vmObject.isCloning || vmObject.isCreating)){
        if (vmPoweredOffBool) {
            liveTile.off("click", kimchi.openVmConsole);
 	    liveTile.off("click", kimchi.vmresume);
            liveTile.on("click", kimchi.vmstart);
            liveTile.hover(function(event){$(this).find('.overlay').show()}, function(event){$(this).find('.overlay').hide()});
        } else if (vmSuspendedBool) {
	    liveTile.off("click", kimchi.vmstart);
	    liveTile.off("click", kimchi.openVmConsole);
            liveTile.on("click", kimchi.vmresume);
	    if(vmObject.state="paused") {
	        liveTile.find('.overlay').attr('src',"/images/theme-default/ac24_resume.png");
	        liveTile.find('.overlay').attr('alt',"Resume");
	    }
            liveTile.hover(function(event){$(this).find('.overlay').show()}, function(event){$(this).find('.overlay').hide()});
        } else {
            liveTile.off("click", kimchi.vmstart);
 	    liveTile.off("click", kimchi.vmresume);
            liveTile.on("click", kimchi.openVmConsole);
        }
    }

    //Setup the gauges
    var stats=vmObject.stats;
    var gaugeValue=0;
    gaugeValue=parseInt(stats.net_throughput);
    kimchi.circleGaugeInit(result, "net_throughput",gaugeValue,(gaugeValue*100/stats.net_throughput_peak));
    gaugeValue=parseInt(stats.io_throughput);
    kimchi.circleGaugeInit(result, "io_throughput",gaugeValue,(gaugeValue*100/stats.io_throughput_peak));
    gaugeValue=parseInt(stats.cpu_utilization);
    kimchi.circleGaugeInit(result, "cpu_utilization",gaugeValue+"%",gaugeValue);

    //Setup the VM Actions
    var guestActions=result.find("div[name=guest-actions]");
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
        //Hide PowerOff
        guestActions.find(".shutoff-hidden").hide();
        //Hide Pause
        guestActions.find(".pause-hidden").hide();
        //Hide Resume
        guestActions.find(".resume-hidden").hide();
    }

    var consoleActions=guestActions.find("[name=vm-console]");

    if ((vmObject.graphics['type'] == 'vnc') || (vmObject.graphics['type'] == 'spice')) {
        consoleActions.on("click", kimchi.openVmConsole);
        consoleActions.show();
    } else {         //we don't recognize the VMs supported graphics, so hide the menu choice
        consoleActions.hide();
        consoleActions.off("click",kimchi.openVmConsole);
    }

    //Setup action event handlers
    if(!(vmObject.isCloning || vmObject.isCreating)){
        guestActions.find("[name=vm-start]").on({click : kimchi.vmstart});
        guestActions.find("[name=vm-poweroff]").on({click : kimchi.vmpoweroff});
        if ((vmRunningBool) || (vmSuspendedBool)) {  
            //If the guest is not running, do not enable reset; otherwise, reset is enabled (when running or paused)
            guestActions.find("[name=vm-reset]").on({click : kimchi.vmreset});

	    //If the guest is not running, do not enable shutdown;otherwise, shutdown is enabled (when running or paused)
            guestActions.find("[name=vm-shutdown]").on({click : kimchi.vmshutdown});
        }

        if (vmSuspendedBool) {
            guestActions.find("[name=vm-resume]").on({click : kimchi.vmresume});
        }

        if (vmRunningBool) {
            guestActions.find("[name=vm-pause]").on({click : kimchi.vmsuspend});
        }

        guestActions.find("[name=vm-edit]").on({click : kimchi.vmedit});
        guestActions.find("[name=vm-delete]").on({click : kimchi.vmdelete});
        guestActions.find("[name=vm-clone]").click(function(){
            var guest = $(this).closest('li[name=guest]').attr("id");
            kimchi.confirm({
                title : i18n['KCHAPI6006M'],
                content : i18n['KCHVM6010M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            }, function() {
                kimchi.cloneGuest(guest, function(data){
                    kimchi.listVmsAuto();
                });
            }, null);
        });

        //Maintain menu open state
        var actionMenu=guestActions.find("div[name=actionmenu]");
        if (openMenu) {
            $('.popover', actionMenu).toggle();
        }

    }else{
        guestActions.find('.btn').attr('disabled', true);
        $('.popover', guestActions.find("div[name=actionmenu]")).remove();

        result.find('.guest-pending').removeClass('hide-content');
        pendingText = result.find('.guest-pending .text')
        if(vmObject.isCloning)
            pendingText.text(i18n['KCHAPI6009M']);
        else
            pendingText.text(i18n['KCHAPI6008M']);
    }

    return result;
};

kimchi.circleGaugeInit = function(topElement, divName, display, percentage){
    var gauge=topElement.find('div[name="' + divName + '"] .circleGauge');
    if(gauge) {
        var data=Object();
        data.percentage = percentage;
        data.display = display;
        gauge.data(data);
    }
    gauge.circleGauge();
    return(gauge);
};

kimchi.guestSetRequestHeader = function(xhr) {
    xhr.setRequestHeader('Accept', 'text/html');
};

kimchi.guest_main = function() {
    if(kimchi.tabMode['guests'] === 'admin') {
        $('.tools').attr('style','display');
        $("#vm-add").on("click", function(event) {
            kimchi.window.open('guest-add.html');
        });
    }
    kimchi.guestTemplate = $('#guest-tmpl').html();
    kimchi.guestElem=$('<div/>').html(kimchi.guestTemplate).find('li');
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
