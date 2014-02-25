/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
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

kimchi.vmstart = function(event) {
    var button=$(this);
    if (!button.hasClass('loading')) {
        button.addClass('loading');
        var vm=$(this).closest('li[name=guest]');
        var vm_id=vm.attr("id");
        kimchi.startVM(vm_id, function(result) {
            button.removeClass('loading');
            kimchi.listVmsAuto();
            }, function() {
                startButton.removeClass('loading');
                kimchi.message.error(i18n['msg.fail.start']);
            }
        );
    } else {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
};

kimchi.vmstop = function(event) {
    var button=$(this);
    if (!button.hasClass('loading')) {
        button.addClass('loading');
        var vm=button.closest('li[name=guest]');
        var vm_id=vm.attr("id");
        kimchi.stopVM(vm_id, function(result) {
            button.removeClass('loading');
            kimchi.listVmsAuto();
        }, function() {
            kimchi.message.error(i18n['msg.fail.stop']);
        });
    } else {
        event.preventDefault();
        event.stopPropagation();
    }
};

kimchi.vmreset = function(event){
    var vm=$(this).closest('li[name=guest]');
    var vm_id=vm.attr("id");
    kimchi.resetVM(vm_id, function(result) {
            kimchi.listVmsAuto();
        }, function() {
            kimchi.message.error(i18n['msg.fail.reset']);
        }
    );
};

kimchi.vmdelete = function(event) {
    var vm = $(this).closest('li[name=guest]');
    var vm_id=vm.attr("id");
    var settings = {
        title : i18n['msg.confirm.delete.title'],
        content : i18n['msg.vm.confirm.delete'],
        confirm : i18n['msg.confirm.delete.confirm'],
        cancel : i18n['msg.confirm.delete.cancel']
    };
    kimchi.confirm(settings, function() {
        kimchi.deleteVM(vm_id, function(result) {
            kimchi.listVmsAuto();
        }, function() {
            kimchi.message.error(i18n['msg.fail.delete']);
        });
    }, function() {
    });
};

kimchi.vmedit = function(event) {
    var vm = $(this).closest('li[name=guest]');
    var vm_id=vm.attr("id");
    kimchi.selectedGuest = vm_id;
    kimchi.window.open("guest-edit.html");
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
    var openMenu = $('#guestList .open:first')
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
    kimchi.listVMs(function(result, textStatus, jqXHR) {
        if (result && textStatus=="success") {
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
    }, function(err) {
        kimchi.message.error(err.responseJSON.reason);
        kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
    });
};

kimchi.createGuestLi = function(vmObject, prevScreenImage, openMenu) {
    var result=kimchi.guestElem.clone();

    //Setup the VM list entry
    var vmRunningBool=(vmObject.state=="running");
    result.attr('id',vmObject.name);
    result.data(vmObject);

    //Add the Name
    var guestTitle=result.find('.title').attr('title',vmObject.name);
    guestTitle.html(vmObject.name);

    //Setup the VM console thumbnail display
    var curImg = vmObject.state == 'running' ? vmObject.screenshot : vmObject.icon;
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

    //Link the stopped tile to the start action, the running tile to open the console
    if (vmRunningBool) {
        liveTile.off("click", kimchi.vmstart);
        liveTile.on("click", kimchi.openVmConsole);
    }
    else {
        liveTile.off("click", kimchi.openVmConsole);
        liveTile.on("click", kimchi.vmstart);
        liveTile.hover(function(event){$(this).find('.overlay').show()}, function(event){$(this).find('.overlay').hide()});
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
    guestActions.find(".shutoff-disabled").prop('disabled', !vmRunningBool );
    guestActions.find(".running-disabled").prop('disabled', vmRunningBool );

    if (vmRunningBool) {
        guestActions.find(".running-hidden").hide();
    }
    else {
        guestActions.find(".shutoff-hidden").hide();
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
    guestActions.find("[name=vm-start]").on({click : kimchi.vmstart});
    guestActions.find("[name=vm-stop]").on({click : kimchi.vmstop});
    if (vmRunningBool) {  //If the guest is not running, do not enable reset
        guestActions.find("[name=vm-reset]").on({click : kimchi.vmreset});
    }
    guestActions.find("[name=vm-edit]").on({click : kimchi.vmedit});
    guestActions.find("[name=vm-delete]").on({click : kimchi.vmdelete});

    //Maintain menu open state
    var actionMenu=guestActions.find("div[name=actionmenu]");
    if (openMenu) {
      actionMenu.addClass("open");
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
    $("#vm-add").on("click", function(event) {
        kimchi.window.open('guest-add.html');
    });
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
