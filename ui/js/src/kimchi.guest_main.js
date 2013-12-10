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
kimchi.initVmButtonsAction = function() {

    var vmstart = function(event) {
        if (!$(this).hasClass('loading')) {
            $(this).addClass('loading');
            kimchi.startVM($(this).data('vm'), function(result) {
                kimchi.listVmsAuto();
            }, function() {
                kimchi.message.error(i18n['msg.fail.start']);
            });
        } else {
            event.preventDefault();
            event.stopPropagation();
            return;
        }
    };

    var vmstop = function(event) {
        if (!$(this).hasClass('loading')) {
            $(this).addClass('loading');
            kimchi.stopVM($(this).data('vm'), function(result) {
                kimchi.listVmsAuto();
            }, function() {
                kimchi.message.error(i18n['msg.fail.stop']);
            });
        } else {
            event.preventDefault();
            event.stopPropagation();
        }
    };

    $('.circle').circle();

    $(".vm-start").each(function(index) {
        if ('running' === $(this).data('vmstate')) {
            $(this).hide();
        } else {
            $(this).show();
        }
    });

    $(".vm-stop").each(function(index) {
        if ('running' === $(this).data('vmstate')) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });

    $(".vm-start").on({
        click : vmstart,
    });

    $(".vm-stop").on({
        click : vmstop,
    });

    $(".vm-reset").on("click", function(event) {
        if ('running' === $(this).data('vmstate')) {
            kimchi.resetVM($(this).data('vm'), function(result) {
                kimchi.listVmsAuto();
            }, function() {
                kimchi.message.error(i18n['msg.fail.reset']);
            });
        } else {
            kimchi.startVM($(this).data('vm'), function(result) {
                kimchi.listVmsAuto();
            }, function() {
                kimchi.message.error(i18n['msg.fail.start']);
            });
        }
    });

    $(".vm-delete").on("click", function(event) {
        var vm = $(this);
        var settings = {
            title : i18n['msg.confirm.delete.title'],
            content : i18n['msg.vm.confirm.delete'],
            confirm : i18n['msg.confirm.delete.confirm'],
            cancel : i18n['msg.confirm.delete.cancel']
        };
        kimchi.confirm(settings, function() {
            kimchi.deleteVM(vm.data('vm'), function(result) {
                kimchi.listVmsAuto();
            }, function() {
                kimchi.message.error(i18n['msg.fail.delete']);
            });
        }, function() {
        });
    });

    $(".vm-edit").on("click", function(event) {
        var vmName = $(this).data('vm');
        kimchi.selectedGuest = vmName;
        kimchi.window.open("guest-edit.html");
    });

    $(".vm-vnc").on("click", function(event) {
        kimchi.vncToVM($(this).data('vm'));
    });

    kimchi.init_button_stat();

};

kimchi.init_button_stat = function() {
    $('.vm-action').each(function() {
        var vm_action = $(this);
        var vm_vnc = vm_action.find('.vm-vnc');
        if ((vm_action.data('graphics') === 'vnc')
                && (vm_action.data('vmstate') === 'running')) {
            vm_vnc.removeAttr('disabled');
        } else {
            vm_vnc.attr('disabled', 'disabled');
        }

        var editButton = vm_action.find('.vm-edit');
        editButton.prop('disabled', vm_action.data('vmstate') !== 'shutoff');
    })
};

kimchi.getVmsOldImg = function() {
    var res = new Object();
    $('#guestList').children().each(function() {
        res[$(this).attr('id')] = $(this).find('img').attr('src');
    })
    return res;
};

kimchi.getVmsOldPopStats = function() {
    var oldSettings = new Object();
    $('#guestList').children().each(function() {
        if ($(this).find('.popable').hasClass('open')) {
            oldSettings[$(this).attr('id')] = true;
        } else {
            oldSettings[$(this).attr('id')] = false;
        }
    })
    return oldSettings;
};

kimchi.listVmsAuto = function() {
    if (kimchi.vmTimeout) {
        clearTimeout(kimchi.vmTimeout);
    }
    kimchi.listVMs(function(result, textStatus, jqXHR) {
        if (result && textStatus=="success") {
            var listHtml = '';
            var guestTemplate = kimchi.guestTemplate;
            var oldImages = kimchi.getVmsOldImg();
            var oldSettings = kimchi.getVmsOldPopStats();
            $.each(result, function(index, value) {
                var oldImg = oldImages[value.name];
                curImg = value.state == 'running' ? value.screenshot : value.icon;
                value['load-src'] = curImg || 'images/icon-vm.png';
                value['tile-src'] = oldImg || value['load-src'];
                var statusTemplate = kimchi.editTemplate(guestTemplate, oldSettings[value.name]);
                listHtml += kimchi.template(statusTemplate, value);
            });
            $('#guestList').html(listHtml);
            $('#guestList').find('.imgload').each(function() {
                this.onload = function() {
                    $(this).prev('.imgactive').remove();
                    $(this).show();
                }
            })
            kimchi.initVmButtonsAction();
        }

        kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
    }, function() {
        kimchi.message.error(i18n['msg.fail.list.guests']);
        kimchi.vmTimeout = window.setTimeout("kimchi.listVmsAuto();", 5000);
    });
};

kimchi.guestSetRequestHeader = function(xhr) {
    xhr.setRequestHeader('Accept', 'text/html');
};

kimchi.guest_main = function() {
    $("#vm-add").on("click", function(event) {
        kimchi.window.open('guest-add.html');
    });

    $.ajax({
        headers : {
            Accept : "text/html"
        },
        url : 'guest.html',
        type : 'GET',
        dataType : 'html',
        accepts : 'text/html',
        success : function(response) {
            kimchi.guestTemplate = response;
            kimchi.listVmsAuto()
        },
        error : function() {
            console.error('Could not get guest.html');
        },
    });

    $('#guests-root-container').on('remove', function() {
        kimchi.vmTimeout && clearTimeout(kimchi.vmTimeout);
    });
};

kimchi.editTemplate = function(guestTemplate, oldPopStat) {
    if (oldPopStat != null && oldPopStat) {
        return guestTemplate.replace("vm-action", "vm-action open");
    }
    return guestTemplate;
};
