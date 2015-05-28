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
                value.capacity = kimchi.changetoProperUnit(value.capacity,1);
                value.allocated = kimchi.changetoProperUnit(value.allocated,1);
                value.enableExt = value.type==="logical" ? "" : "hide-content";
                if ('kimchi-iso' !== value.type) {
                    listHtml += kimchi.substitute(storageHtml, value);
                }
            });
            $('#storagepoolsList').html(listHtml);
            if(kimchi.tabMode['storage'] === 'admin') {
                $('.storage-button').attr('style','display');
            } else {
                $('.storage-allocate').addClass('storage-allocate-padding-user');
            }
            kimchi.storageBindClick();
        } else {
            $('#storagepoolsList').html('');
        }
    }, function(err) {
        kimchi.message.error(err.responseJSON.reason);
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

    if(kimchi.tabMode['storage'] === 'admin') {
        $('.pool-delete').on('click', function(event) {
            var $pool = $(this);
            var settings = {
                title : i18n['KCHAPI6001M'],
                content : i18n['KCHPOOL6001M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            };
            kimchi.confirm(settings, function() {
                var poolName = $pool.data('name');
                kimchi.deleteStoragePool(poolName, function() {
                    kimchi.doListStoragePools();
                }, function(err) {
                    kimchi.message.error(err.responseJSON.reason);
                });
            });
        });

        $('.pool-activate').on('click', function(event) {
            var poolName = $(this).data('name');
            kimchi.changePoolState(poolName, 'activate', function() {
                kimchi.doListStoragePools();
            }, function(err) {
                kimchi.message.error(err.responseJSON.reason);
            });
        });

        $('.pool-deactivate').on('click', function(event) {
            var poolName = $(this).data('name');
            var settings = {
                title : i18n['KCHAPI6001M'],
                content : i18n['KCHPOOL6012M'],
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            };
            if (!$(this).data('persistent')) {
                kimchi.confirm(settings, function() {
                    kimchi.changePoolState(poolName, 'deactivate', function() {
                        kimchi.doListStoragePools();
                    }, function(err) {
                        kimchi.message.error(err.responseJSON.reason);
                    });
                }, function() {
                    return false;
                });
            }
            else {
                kimchi.changePoolState(poolName, 'deactivate', function() {
                    kimchi.doListStoragePools();
                }, function(err) {
                    kimchi.message.error(err.responseJSON.reason);
                });
            }
        });

        $('.pool-add-volume').on('click', function(event) {
            var poolName = $(this).data('name');
            kimchi.selectedSP = poolName;
            kimchi.window.open('storagepool-add-volume.html');
        });

        $('.storage-action').on('click', function() {
            var storage_action = $(this);
            var deleteButton = storage_action.find('.pool-delete');
            if ('active' === deleteButton.data('stat')) {
                deleteButton.attr('disabled', 'disabled');
            } else {
                deleteButton.removeAttr('disabled');
            }
        });

        $('.pool-extend').on('click', function() {
            $("#logicalPoolExtend").dialog("option", "poolName", $(this).data('name'));
            $("#logicalPoolExtend").dialog("open");
        });
    }

    $('.storage-li').on('click', function(event) {
        if (!$(event.target).parents().hasClass('bottom')) {
            if ($(this).data('stat') === 'active') {
                var that = $(this);
                var volumeDiv = $('#volume' + that.data('name'));
                var slide = $(this).next('.volumes');
                if (that.hasClass('in')) {
                    kimchi.doListVolumes(that);
                } else {
                    slide.slideUp('slow');
                    that.addClass('in');
                    kimchi.changeArrow(that.children().last().children());
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
    volume.capacity = kimchi.changetoProperUnit(volume.capacity,1);
    volume.allocation = kimchi.changetoProperUnit(volume.allocation,1);
    return kimchi.substitute(volumeHtml, volume);
};

kimchi.doListVolumes = function(poolObj) {
    var poolName = poolObj.data('name')

    var getOngoingVolumes = function() {
        var result = {}
        var filter = 'status=running&target_uri=' + encodeURIComponent('^/storagepools/' + poolName + '/*')
        kimchi.getTasksByFilter(filter, function(tasks) {
            for(var i = 0; i < tasks.length; i++) {
                var volumeName = tasks[i].target_uri.split('/').pop();
                result[volumeName] = tasks[i];

                if(kimchi.trackingTasks.indexOf(tasks[i].id) >= 0) {
                    continue;
                }

                kimchi.trackTask(tasks[i].id, function(result) {
                    kimchi.topic('kimchi/volumeTransferFinished').publish(result);
                }, function(result) {
                    kimchi.topic('kimchi/volumeTransferError').publish(result);
                }, function(result) {
                    kimchi.topic('kimchi/volumeTransferProgress').publish(result);
                });
            }
        }, null, true);
        return result;
    };

    var volumeDiv = $('#volume' + poolName);
    $(volumeDiv).empty();
    var slide = poolObj.next('.volumes');
    var handleArrow = poolObj.children().last().children();

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
                type: 'file'
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
            kimchi.topic('kimchi/volumeTransferProgress').publish(task);
        });

        poolObj.removeClass('in');
        kimchi.changeArrow(handleArrow);
        slide.slideDown('slow');
    }, function(err) {
        kimchi.message.error(err.responseJSON.reason);
    });
}

kimchi.initLogicalPoolExtend = function() {
    $("#logicalPoolExtend").dialog({
        autoOpen : false,
        modal : true,
        width : 600,
        resizable : false,
        closeText: "X",
        open : function(){
            $('#loading-info', '#logicalPoolExtend').removeClass('hidden');
            $(".ui-dialog-titlebar-close", $("#logicalPoolExtend").parent()).removeAttr("title");
            kimchi.listHostPartitions(function(data) {
                $('#loading-info', '#logicalPoolExtend').addClass('hidden');
                if (data.length > 0) {
                    for(var i=0;i<data.length;i++){
                        if (data[i].type === 'part' || data[i].type === 'disk') {
                            $('.host-partition', '#logicalPoolExtend').append(kimchi.substitute($('#logicalPoolExtendTmpl').html(), data[i]));
                        }
                    }
                } else {
                    $('.host-partition').html(i18n['KCHPOOL6011M']);
                    $('.host-partition').addClass('text-help');
                }
            }, function(err) {
                $('#loading-info', '#logicalPoolExtend').addClass('hidden');
                $('.host-partition').html(i18n['KCHPOOL6013M'] + '<br/>(' + err.responseJSON.reason + ')');
                $('.host-partition').addClass('text-help');
            });
        },
        beforeClose : function() { $('.host-partition', '#logicalPoolExtend').empty(); },
        buttons : [{
            class: "ui-button-primary",
            text: i18n.KCHAPI6007M,
            click: function(){
                var devicePaths = [];
                $("input[type='checkbox']:checked", "#logicalPoolExtend").each(function(){
                    devicePaths.push($(this).prop('value'));
                })
                kimchi.updateStoragePool($("#logicalPoolExtend").dialog("option", "poolName"),{disks: devicePaths},function(data){
                    var item = $("#"+$("#logicalPoolExtend").dialog("option", "poolName"));
                    $(".usage", $(".storage-name", item)).text((Math.round(data.allocated/data.capacity*100)||0)+"%");
                    $(".storage-text", $(".storage-capacity", item)).text(kimchi.changetoProperUnit(data.capacity,1));
                    $(".storage-text", $(".storage-allocate", item)).text(kimchi.changetoProperUnit(data.allocated,1));
                });
                $(this).dialog("close");
            }
        }]
    });
}

kimchi.storage_main = function() {
    if(kimchi.tabMode['storage'] === 'admin') {
        $('.tools').attr('style','display');
        $('#storage-pool-add').on('click', function() {
            kimchi.window.open('storagepool-add.html');
        });
        $('.list-title .title-actions').attr('style','display');
    }
    kimchi.doListStoragePools();
    kimchi.initLogicalPoolExtend();

    kimchi.topic('kimchi/storageVolumeAdded').subscribe(function() {
        pool = kimchi.selectedSP;
        var poolNode = $('.storage-li[data-name="' + pool + '"]');
        kimchi.doListVolumes(poolNode);
    });

    kimchi.topic('kimchi/volumeTransferProgress').subscribe(function(result) {
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
            var formatted = kimchi.formatMeasurement(downloaded);
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

    kimchi.topic('kimchi/volumeTransferFinished').subscribe(function(result) {
        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[2];
        var volumeName = uriElements.pop();
        var volumeBox = $('#volume' + poolName + ' [data-volume-name="' + volumeName + '"]');
        $('.volume-progress', volumeBox).addClass('hidden');
        kimchi.getStoragePoolVolume(poolName, volumeName, function(volume) {
            var html = kimchi._generateVolumeHTML(volume);
            $(volumeBox).replaceWith(html);
        }, function(err) {
            kimchi.message.error(err.responseJSON.reason);
        });
    });

    kimchi.topic('kimchi/volumeTransferError').subscribe(function(result) {
        // Error message from Async Task status
        if (result['message']) {
            var errText = result['message'];
        }
        // Error message from standard kimchi exception
        else {
            var errText = result['responseJSON']['reason'];
        }
        result && kimchi.message.error(errText);

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
