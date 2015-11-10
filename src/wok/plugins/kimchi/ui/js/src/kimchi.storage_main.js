/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2015
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
kimchi.doListStoragePools = function() {
    kimchi.listStoragePools(function(result) {
        var storageHtml = $('#storageTmpl').html();
        if (result && result.length) {
            var listHtml = '';
            $.each(result, function(index, value) {
                value.usage = Math.round(value.allocated / value.capacity * 100) || 0;
                if (value.usage <= 100 && value.usage >= 85) {
                    value.icon = 'icon-high';
                }else if (value.usage <= 85 && value.usage >= 75 ) {
                    value.icon = 'icon-med';
                } else {
                    value.icon = 'icon-low';
                }                
                value.capacity = wok.changetoProperUnit(value.capacity,1);
                value.allocated = wok.changetoProperUnit(value.allocated,1);
                value.enableExt = value.type==="logical" ? "" : "hide-content";
                if ('kimchi-iso' !== value.type) {
                    listHtml += wok.substitute(storageHtml, value);
                }
            });
            if($('#storageGrid').hasClass('wok-datagrid'))
                $('#storageGrid').dataGrid('destroy');
            $('#storagepoolsList').html(listHtml);
            if(wok.tabMode['storage'] === 'admin') {
                $('.storage-button').attr('style','display');
            } else {
                $('.storage-allocate').addClass('storage-allocate-padding-user');
            }
            $('#storageGrid').dataGrid({enableSorting: false});
            $('input', $('.grid-control', '.storage')).on('keyup', function(){
                $('#storageGrid').dataGrid('filter', $(this).val());
            });
            kimchi.storageBindClick();
        } else {
            $('#storagepoolsList').html('');
        }
    }, function(err) {
        wok.message.error(err.responseJSON.reason);
    });
}

kimchi.storageBindClick = function() {

    $('.inactive').each(function(index) {
        if ('active' === $(this).data('state')) {
            $(this).hide();
        } else {
            $(this).show();
        }
    });

    $('.list-storage .storage-state .active').each(function(index) {
        if ('active' === $(this).data('state')) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });

    $('.pool-activate').each(function(index) {
        if ('active' === $(this).data('stat')) {
            $(this).hide();
        } else {
            $(this).show();
        }
    });

    $('.pool-deactivate').each(function(index) {
        if ('active' === $(this).data('stat')) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });

    $('.pool-add-volume').each(function(index) {
        var canAddVolume =
            $(this).data('stat') === 'active' &&
            $(this).data('type') !== 'iscsi' &&
            $(this).data('type') !== 'scsi';
        if(canAddVolume) {
            $(this).show();
        }
        else {
            $(this).hide();
        }
    });

    if(wok.tabMode['storage'] === 'admin') {
        $('.pool-delete').on('click', function(event) {
            event.preventDefault();
            var $pool = $(this);
            var settings = {
                title : i18n['KCHAPI6001M'],
                content : i18n['KCHPOOL6001M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            };
            wok.confirm(settings, function() {
                var poolName = $pool.data('name');
                kimchi.deleteStoragePool(poolName, function() {
                    kimchi.doListStoragePools();
                }, function(err) {
                    wok.message.error(err.responseJSON.reason);
                });
            });
        });

        $('.pool-activate').on('click', function(event) {
            event.preventDefault();
            var poolName = $(this).data('name');
            kimchi.changePoolState(poolName, 'activate', function() {
                kimchi.doListStoragePools();
            }, function(err) {
                wok.message.error(err.responseJSON.reason);
            });
        });

        $('.pool-deactivate').on('click', function(event) {
            event.preventDefault();
            var poolName = $(this).data('name');
            var settings = {
                title : i18n['KCHAPI6001M'],
                content : i18n['KCHPOOL6012M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            };
            if (!$(this).data('persistent')) {
                wok.confirm(settings, function() {
                    kimchi.changePoolState(poolName, 'deactivate', function() {
                        kimchi.doListStoragePools();
                    }, function(err) {
                        wok.message.error(err.responseJSON.reason);
                    });
                }, function() {
                    return false;
                });
            }
            else {
                kimchi.changePoolState(poolName, 'deactivate', function() {
                    kimchi.doListStoragePools();
                }, function(err) {
                    wok.message.error(err.responseJSON.reason);
                });
            }
        });

        $('.pool-add-volume').on('click', function(event) {
            event.preventDefault();
            var poolName = $(this).data('name');
            kimchi.selectedSP = poolName;
            wok.window.open('plugins/kimchi/storagepool-add-volume.html');
        });

        $('.storage-action').on('click', function(event) {
            event.preventDefault();
            var storage_action = $(this);
            var deleteButton = storage_action.find('.pool-delete');
            if ('active' === deleteButton.data('stat')) {
                deleteButton.attr('disabled', 'disabled');
            } else {
                deleteButton.removeAttr('disabled');
            }
        });

        $('.pool-extend').on('click', function(event) {
            event.preventDefault();
            //$("#logicalPoolExtend").dialog("option", "poolName", $(this).data('name'));
            //$("#logicalPoolExtend").dialog("open");
            partitions = $(this).data('name');
            //$("#logicalPoolExtend").dialog("option", "poolName", $(this).data('name'));
        });



    }

    $('.wok-datagrid-row .handle ').on('click', function(event) {
        if (!$(event.target).parents().hasClass('bottom')) {
            if ($(this).parent().parent().data('stat') === 'active') {
                var that = $(this).parent().parent();
                var volumeDiv = $('#volume' + that.data('name'));
                var slide = $('.volumes', $(this).parent().parent());
                if (that.hasClass('in')) {
                    that.css('height','auto');
                    kimchi.doListVolumes(that);
                } else {
                    slide.slideUp('slow', function(){
                        that.css('height','');
                    });
                    that.addClass('in');
                    kimchi.changeArrow($('.arrow-up', $(this).parent().parent()));
                }
            }
        }
    });
}

kimchi._generateVolumeHTML = function(volume) {
    if(volume['type'] === 'kimchi-iso') {
        return '';
    }
    var volumeHtml = $('#volumeTmpl').html();
    volume.capacityLevel = Math.round(volume.allocation / volume.capacity * 100) || 0;
    if (volume.capacityLevel > 100) {
        volume.capacityIcon = 'icon-high';
        volume.capacityLevel = 100;
    } else if (volume.capacityLevel <= 100 && volume.capacityLevel >= 85) {
        volume.capacityIcon = 'icon-high';
    }else if (volume.capacityLevel <= 85 && volume.capacityLevel >= 75 ) {
        volume.capacityIcon = 'icon-med';
    } else {
        volume.capacityIcon = 'icon-low';
    }
    volume.capacity = wok.changetoProperUnit(volume.capacity,1);
    volume.allocation = wok.changetoProperUnit(volume.allocation,1);
    return wok.substitute(volumeHtml, volume);
};

kimchi.doListVolumes = function(poolObj) {
    var poolName = poolObj.data('name')

    var getOngoingVolumes = function() {
        var result = {}
        var filter = 'status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/storagepools/' + poolName + '/*')
        kimchi.getTasksByFilter(filter, function(tasks) {
            for(var i = 0; i < tasks.length; i++) {
                var volumeName = tasks[i].target_uri.split('/').pop();
                result[volumeName] = tasks[i];

                if(kimchi.trackingTasks.indexOf(tasks[i].id) >= 0) {
                    continue;
                }

                kimchi.trackTask(tasks[i].id, function(result) {
                    wok.topic('kimchi/volumeTransferFinished').publish(result);
                }, function(result) {
                    wok.topic('kimchi/volumeTransferError').publish(result);
                }, function(result) {
                    wok.topic('kimchi/volumeTransferProgress').publish(result);
                });
            }
        }, null, true);
        return result;
    };

    var volumeDiv = $('#volume' + poolName);
    $(volumeDiv).empty();
    var slide = $('.volumes', poolObj);
    var handleArrow = $('.arrow-down', poolObj);

    kimchi.listStorageVolumes(poolName, function(result) {
        var listHtml = '';
        var ongoingVolumes = [];
        var ongoingVolumesMap = getOngoingVolumes();
        $.each(ongoingVolumesMap, function(volumeName, task) {
            ongoingVolumes.push(volumeName)
            var volume = {
                poolName: poolName,
                used_by: [],
                capacity: 0,
                name: volumeName,
                format: '',
                bootable: null,
                os_distro: '',
                allocation: 0,
                os_version: '',
                path: '',
                type: 'file',
                capacityLevel: 0,
                capacityIcon: ''
            };
            listHtml += kimchi._generateVolumeHTML(volume);
        });

        $.each(result, function(index, value) {
            if (ongoingVolumes.indexOf(value.name) == -1) {
                value.poolname = poolName;
                listHtml += kimchi._generateVolumeHTML(value);
            }
        });

        if (listHtml.length > 0) {
            volumeDiv.html(listHtml);
        } else {
            volumeDiv.html("<div class='pool-empty'>" + i18n['KCHPOOL6002M'] + "</div>");
        }

        $.each(ongoingVolumesMap, function(volumeName, task) {
            wok.topic('kimchi/volumeTransferProgress').publish(task);
        });

        poolObj.removeClass('in');
        kimchi.changeArrow(handleArrow);
        slide.slideDown('slow');
    }, function(err) {
        wok.message.error(err.responseJSON.reason);
    });
}

    kimchi.initLogicalPoolExtend = function() {

    // $("#logicalPoolExtend").dialog({
    //     autoOpen : false,
    //     modal : true,
    //     width : 600,
    //     resizable : false,
    //     closeText: "X",
    //     open : function(){
    //         $('#loading-info', '#logicalPoolExtend').removeClass('hidden');
    //         $(".ui-dialog-titlebar-close", $("#logicalPoolExtend").parent()).removeAttr("title");
    //         kimchi.listHostPartitions(function(data) {
    //             $('#loading-info', '#logicalPoolExtend').addClass('hidden');
    //             if (data.length > 0) {
    //                 for(var i=0;i<data.length;i++){
    //                     if (data[i].type === 'part' || data[i].type === 'disk') {
    //                         $('.host-partition', '#logicalPoolExtend').append(wok.substitute($('#logicalPoolExtendTmpl').html(), data[i]));
    //                     }
    //                 }
    //             } else {
    //                 $('.host-partition').html(i18n['KCHPOOL6011M']);
    //                 $('.host-partition').addClass('text-help');
    //             }
    //         }, function(err) {
    //             $('#loading-info', '#logicalPoolExtend').addClass('hidden');
    //             $('.host-partition').html(i18n['KCHPOOL6013M'] + '<br/>(' + err.responseJSON.reason + ')');
    //             $('.host-partition').addClass('text-help');
    //         });
    //     },
    //     beforeClose : function() { $('.host-partition', '#logicalPoolExtend').empty(); },
    //     buttons : [{
    //         class: "ui-button-primary",
    //         text: i18n.KCHAPI6007M,
    //         click: function(){
    //             var devicePaths = [];
    //             $("input[type='checkbox']:checked", "#logicalPoolExtend").each(function(){
    //                 devicePaths.push($(this).prop('value'));
    //             })
    //             kimchi.updateStoragePool($("#logicalPoolExtend").dialog("option", "poolName"),{disks: devicePaths},function(data){
    //                 var item = $("#"+$("#logicalPoolExtend").dialog("option", "poolName"));
    //                 $(".usage", $(".storage-name", item)).text((Math.round(data.allocated/data.capacity*100)||0)+"%");
    //                 $(".storage-text", $(".storage-capacity", item)).text(wok.changetoProperUnit(data.capacity,1));
    //                 $(".storage-text", $(".storage-allocate", item)).text(wok.changetoProperUnit(data.allocated,1));
    //             });
    //             $(this).dialog("close");
    //         }
    //     }]
    // });

    $('#logicalPoolExtend').on('hidden.bs.modal', function () {
        $('.host-partition', '#logicalPoolExtend').empty();
    })

    $('#logicalPoolExtend').on('show.bs.modal', function() {
        //$('#logicalPoolExtend2').find('.modal-content').html();
        kimchi.listHostPartitions(function(partitions) {
            $('#loading-info', '#logicalPoolExtend').removeClass('hidden');
            if (partitions.length > 0) {
                for (var i = 0; i < partitions.length; i++) {
                    if (partitions[i].type === 'part' || partitions[i].type === 'disk') {
                        $('.host-partition', '#logicalPoolExtend').append(wok.substitute($('#logicalPoolExtendTmpl').html(), partitions[i]));
                        $('#savePartitions', '#logicalPoolExtend').prop('disabled', false);
                    }
                }
            } else {
                $('#loading-info', '#logicalPoolExtend').addClass('hidden');
                $('.host-partition').html(i18n['KCHPOOL6011M']);
            }
        }, function(err) {
            $('#loading-info', '#logicalPoolExtend').addClass('hidden');
            $('.host-partition').html(i18n['KCHPOOL6013M'] + '<br/>(' + err.responseJSON.reason + ')');
        });

        $('#savePartitions', '#logicalPoolExtend').on('click', function(event) {
            event.preventDefault();
            var devicePaths = [];
            $("input[type='checkbox']:checked", "#logicalPoolExtend").each(function() {
                devicePaths.push($(this).prop('value'));
            })
            kimchi.updateStoragePool($("#logicalPoolExtend"), {
                disks: devicePaths
            }, function(partitions) {
                var item = $("#" + $("#logicalPoolExtend").dialog("option", "poolName"));
                $('#logicalPoolExtend').modal('hide');
                $(".usage", $(".storage-name", item)).text((Math.round(partitions.allocated / partitions.capacity * 100) || 0) + "%");
                $(".storage-text", $(".storage-capacity", item)).text(wok.changetoProperUnit(partitions.capacity, 1));
                $(".storage-text", $(".storage-allocate", item)).text(wok.changetoProperUnit(partitions.allocated, 1));
            }, function(err) {
                $('#savePartitions', '#logicalPoolExtend').prop('disabled', true);
                $('#logicalPoolExtend').modal('hide');
            });
        });

    });

}

kimchi.storage_main = function() {
    if(wok.tabMode['storage'] === 'admin') {
        $('.tools').attr('style','display');
        $('#storage-pool-add').on('click', function() {
            wok.window.open('plugins/kimchi/storagepool-add.html');
        });
        $('.list-title .title-actions').attr('style','display');
    }
    kimchi.doListStoragePools();
    kimchi.initLogicalPoolExtend();

    wok.topic('kimchi/storageVolumeAdded').subscribe(function() {
        pool = kimchi.selectedSP;
        var poolNode = $('.storage-li[data-name="' + pool + '"]');
        kimchi.doListVolumes(poolNode);
    });

    wok.topic('kimchi/volumeTransferProgress').subscribe(function(result) {
        var extractProgressData = function(data) {
            var sizeArray = /(\d+)\/(\d+)/g.exec(data) || [0, 0, 0];
            var downloaded = sizeArray[1];
            var percent = 0;
            if(downloaded) {
                var total = sizeArray[2];
                if(!isNaN(total)) {
                    percent = downloaded / total * 100;
                }
            }
            var formatted = wok.formatMeasurement(downloaded);
            var size = (1.0 * formatted['v']).toFixed(1) + formatted['s'];
            return {
                size: size,
                percent: percent
            };
        };

        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[2];
        var volumeName = uriElements.pop();
        var progress = extractProgressData(result['message']);
        var size = progress['size'];
        var percent = progress['percent'];

        volumeBox = $('#volume' + poolName + ' [data-volume-name="' + volumeName + '"]');
        $('.progress-bar-inner', volumeBox).css({
            width: percent + '%'
        });
        $('.progress-transferred', volumeBox).text(size);
        $('.volume-progress', volumeBox).removeClass('hidden');
        $('.progress-status', volumeBox).text(i18n['KCHPOOL6014M']);
    });

    wok.topic('kimchi/volumeTransferFinished').subscribe(function(result) {
        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[2];
        var volumeName = uriElements.pop();
        var volumeBox = $('#volume' + poolName + ' [data-volume-name="' + volumeName + '"]');
        $('.volume-progress', volumeBox).addClass('hidden');
        kimchi.getStoragePoolVolume(poolName, volumeName, function(volume) {
            var html = kimchi._generateVolumeHTML(volume);
            $(volumeBox).replaceWith(html);
        }, function(err) {
            wok.message.error(err.responseJSON.reason);
        });
    });

    wok.topic('kimchi/volumeTransferError').subscribe(function(result) {
        // Error message from Async Task status
        if (result['message']) {
            var errText = result['message'];
        }
        // Error message from standard kimchi exception
        else {
            var errText = result['responseJSON']['reason'];
        }
        result && wok.message.error(errText);

        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[2];
        var volumeName = uriElements.pop();
        volumeBox = $('#volume' + poolName + ' [data-volume-name="' + volumeName + '"]');
        $('.progress-status', volumeBox).text(i18n['KCHPOOL6015M']);
    });
};

kimchi.changeArrow = function(obj) {
    if ($(obj).hasClass('arrow-down')) {
        $(obj).removeClass('arrow-down').addClass('arrow-up');
    } else {
        $(obj).removeClass('arrow-up').addClass('arrow-down');
    }
}