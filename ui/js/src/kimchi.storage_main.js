/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2013-2017
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
    $('.wok-mask').removeClass('hidden');
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
            if($('#storageGrid').hasClass('wok-datagrid')) {
                $('#storageGrid').dataGrid('destroy');
            }
            $('#storagepoolsList').html(listHtml);
            if(wok.tabMode['storage'] === 'admin') {
                $('.storage-button').attr('style','display');
            } else {
                $('.storage-allocate').addClass('storage-allocate-padding-user');
            }
            $('#storageGrid').dataGrid({enableSorting: false});
            $('#storageGrid').removeClass('hidden');
            $('.wok-mask').fadeOut(300, function() {});
            $('input', $('.grid-control', '.storage')).on('keyup', function(){
                $('#storageGrid').dataGrid('filter', $(this).val());
            });
            kimchi.storageBindClick();
        } else {
            $('.wok-mask').fadeOut(300, function() {});
            $('#storagepoolsList').html('');
        }
    }, function(err) {
        $('.wok-mask').fadeOut(300, function() {});
        wok.message.error(err.responseJSON.reason);
    });
};

kimchi.storageBindClick = function() {

   $('.volumes').on('click','.toggle-gallery',function(e){
        e.preventDefault();
        e.stopPropagation();
        var button = $(this);
        var volumeBlock = $(this).parent().parent().parent();
        var text = $('span.text', button).text();
        $(".wok-list, .wok-gallery",volumeBlock).toggleClass("wok-list wok-gallery");
        $('span.text', button).text(text == i18n['KCHTMPL6005M'] ? i18n['KCHTMPL6004M'] : i18n['KCHTMPL6005M']);
    });

    if(wok.tabMode['storage'] === 'admin') {

        $('.volumes').on('click','.volume-delete',function(e){
            e.preventDefault();
            e.stopPropagation();
            var button = $(this);
            $('.dropdown.pool-action.open .dropdown-toggle').dropdown('toggle');
            kimchi.selectedSP = $(this).data('name');
            var volumeBlock = $(this).data('name');
            var volumes = $('[data-name="'+kimchi.selectedSP+'"] input:checkbox:checked').map(function(){
              return this.value;
            }).get();
            kimchi.selectedVolumes = volumes.slice();
            var formatedVolumes = '';
            if(kimchi.selectedVolumes.length && !button.parent().is('disabled')){
                for (i = 0; i < kimchi.selectedVolumes.length; i++) {
                    formatedVolumes += "<li>" + kimchi.selectedVolumes[i] + "</li>";
                }
                var confirmMessage = i18n['KCHPOOL6010M'].replace('%1','<ul>'+formatedVolumes+'</ul>'+i18n['KCHPOOL6009M']);
                var settings = {
                    title : i18n['KCHAPI6001M'],
                    content : confirmMessage,
                    confirm : i18n['KCHAPI6002M'],
                    cancel : i18n['KCHAPI6003M']
                };
                wok.confirm(settings, function() {
                    $('[data-name="'+kimchi.selectedSP+'"] input:checkbox:checked').prop('disabled',true);
                    $.each(kimchi.selectedVolumes, function(i,j) {
                        $('[data-volume-name="'+j+'"] .volume-inline-progress').removeClass('hidden');
                        volumes = jQuery.grep(volumes, function(value) {
                          return value != j;
                        });
                        kimchi.deleteStoragePoolVolume(kimchi.selectedSP,j,function(){
                            wok.topic('kimchi/storageVolumeDeleted').publish();
                        },function(err){
                            wok.message.error(err.responseJSON.reason);
                        });
                        if(volumes.length === 0){
                            kimchi.selectedVolumes = '';
                            wok.topic('kimchi/storageVolumeDeleted').publish();
                        }
                    });
                });
            }else {
                return false;
            }
        });

        $('.volumes').on('click','.volume-wipe',function(e){
            e.preventDefault();
            e.stopPropagation();
            var button = $(this);
            $('.dropdown.pool-action.open .dropdown-toggle').dropdown('toggle');
            kimchi.selectedSP = $(this).data('name');
            var volumeBlock = $(this).data('name');
            var volumes = $('[data-name="'+kimchi.selectedSP+'"] input:checkbox:checked').map(function(){
              return this.value;
            }).get();
            kimchi.selectedVolumes = volumes.slice();
            var formatedVolumes = '';
            if(kimchi.selectedVolumes.length && !button.parent().is('disabled')){
                for (i = 0; i < kimchi.selectedVolumes.length; i++) {
                    formatedVolumes += "<li>" + kimchi.selectedVolumes[i] + "</li>";
                }
                var confirmMessage = i18n['KCHPOOL6017M'].replace('%1','<ul>'+formatedVolumes+'</ul>'+i18n['KCHPOOL6009M']);
                var settings = {
                    title : i18n['KCHPOOL6018M'],
                    content : confirmMessage,
                    confirm : i18n['KCHAPI6002M'],
                    cancel : i18n['KCHAPI6003M']
                };
                wok.confirm(settings, function() {
                    $('[data-name="'+kimchi.selectedSP+'"] input:checkbox:checked').prop('disabled',true);
                    $.each(kimchi.selectedVolumes, function(i,j) {
                        $('[data-volume-name="'+j+'"] .volume-inline-progress').removeClass('hidden');
                        volumes = jQuery.grep(volumes, function(value) {
                          return value != j;
                        });
                        kimchi.wipeStoragePoolVolume(kimchi.selectedSP,j,function(){
                            wok.topic('kimchi/storageVolumeWiped').publish();
                        },function(err){
                            wok.message.error(err.responseJSON.reason);
                        });
                        if(volumes.length === 0){
                            kimchi.selectedVolumes = '';
                            wok.topic('kimchi/storageVolumeWiped').publish();
                        }
                    });
                });
            }else {
                return false;
            }
        });

        $('.volumes').on('click','.volume-resize',function(e){
            e.preventDefault();
            e.stopPropagation();
            var button = $(this);
            $('.dropdown.pool-action.open .dropdown-toggle').dropdown('toggle');
            kimchi.selectedSP = $(this).data('name');
            var volumes = $('[data-name="'+kimchi.selectedSP+'"] input:checkbox:checked').map(function(){
              return this.value;
            }).get();
            kimchi.selectedVolumes = volumes.slice(0,1);
            if(kimchi.selectedVolumes.length && !button.parent().is('disabled')){
                wok.window.open('plugins/kimchi/storagepool-resize-volume.html');
            }else {
                return false;
            }
        });

        $('.volumes').on('click','.volume-clone',function(e){
            e.preventDefault();
            e.stopPropagation();
            var button = $(this);
            $('.dropdown.pool-action.open .dropdown-toggle').dropdown('toggle');
            kimchi.selectedSP = $(this).data('name');
            var volumeBlock = $(this).data('name');
            var volumes = $('[data-name="'+kimchi.selectedSP+'"] input:checkbox:checked').map(function(){
              return this.value;
            }).get();
            kimchi.volumesToClone = volumes.slice();
            var formatedVolumes = '';
            if(kimchi.volumesToClone.length && !button.parent().is('disabled')){
                    $.each(kimchi.volumesToClone, function(i,j) {
                        volumes = jQuery.grep(volumes, function(value) {
                          return value != j;
                        });
                        var data = {};
                        data = {
                            pool: kimchi.selectedSP
                        }
                        kimchi.cloneStoragePoolVolume(kimchi.selectedSP,j,data,function(){
                            wok.topic('kimchi/storageVolumeCloned').publish();
                        },function(err){
                            wok.message.error(err.responseJSON.reason);
                        });
                        if(volumes.length === 0){
                            kimchi.volumesToClone = '';
                            wok.topic('kimchi/storageVolumeCloned').publish();
                        }
                    });
            }else {
                return false;
            }
        });

        $('.volumes').on('click','.wok-datagrid-row',function(e){
            if (!$(e.target).is("input[type='checkbox']") && !$(e.target).is("label")) {
                var volumeBlock = $(this);
                var checkbox = volumeBlock.find('[name="selected-volume[]"]');
                checkbox.trigger('click');
            }
        });

        $('.volumes').on('change','[name="selected-volume[]"]',function(e){
            var checkbox = $(this);
            var volumeBlock = $(this).closest('.wok-datagrid-row');
            var volumesBlock = $(this).closest('.volumeslist');
            var poolType = volumesBlock.data('type')
            var selectedVolumes = $('[name="selected-volume[]"]:checked',volumesBlock)
            var disabled = [];
            var enabled = [];

            // No volume selected
            if (selectedVolumes.length === 0) {
                disabled = ['volume-resize','volume-clone','volume-wipe','volume-delete'];
                enabled = [];
            // One or more volumes selected
            } else {
                // Read-write pools
                if (poolType !== 'scsi' && poolType !== 'iscsi') {
                    // Not able to resize more than one volume
                    // Logical pools don't enable resize of their volumes
                    if (selectedVolumes.length > 1 || poolType === 'logical') {
                        disabled = ['volume-resize'];
                        enabled = ['volume-clone','volume-wipe','volume-delete'];
                    } else {
                        disabled = [];
                        enabled = ['volume-resize','volume-clone','volume-wipe', 'volume-delete'];
                    }
                }
            }

            for (i = 0; i < disabled.length; i++) {
                $('.'+disabled[i],volumesBlock).parent().addClass('disabled');
            }

            for (i = 0; i < enabled.length; i++) {
                $('.'+enabled[i],volumesBlock).parent().removeClass('disabled');
            }

            if(checkbox.is(":checked")){
                volumeBlock.addClass('selected');
            }else {
                volumeBlock.removeClass('selected');
            }
        });

    }

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

    $('.volume-add').each(function(index) {
        var canAddVolume =
            $(this).data('stat') === 'active' &&
            $(this).data('type') !== 'iscsi' &&
            $(this).data('type') !== 'scsi';
        if(canAddVolume) {
            $(this).parent().removeClass('disabled');
        }
        else {
            $(this).parent().addClass('disabled');
        }
    });

    $('.volumeslist').each(function(index) {
        var rwpool = $(this).data('type') !== 'iscsi' &&
                      $(this).data('type') !== 'scsi'

        if (!rwpool)
            $('.pool-action', $(this)).addClass('hidden');
    });

    if(wok.tabMode['storage'] === 'admin') {
        $('.pool-delete').on('click', function(event) {
            event.preventDefault();
            var $pool = $(this);
            var poolName = $pool.data('name');
            var confirmMessage = i18n['KCHPOOL6001M'].replace('%1', '<strong>'+poolName+'</strong>');
            var in_use = $pool.data('inuse');
            if ('active' === $pool.data('stat') || in_use) {
                $pool.parent().addClass('disabled');
                return false;
            } else {
                $pool.parent().removeClass('disabled');
            }
            var settings = {
                title : i18n['KCHAPI6001M'],
                content : confirmMessage,
                confirm : i18n['KCHAPI6002M'],
                cancel : i18n['KCHAPI6003M']
            };
            wok.confirm(settings, function() {
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
            var confirmMessage = i18n['KCHPOOL6012M'].replace('%1', '<strong>'+poolName+'</strong>');
            var $poolDeactivate = $(this);
            var in_use = $poolDeactivate.data('inuse');
            if (in_use) {
                $poolDeactivate.parent().addClass('disabled');
                return false;
            } else {
                $poolDeactivate.parent().removeClass('disabled');
            }
            var settings = {
                title : i18n['KCHAPI6001M'],
                content : confirmMessage,
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

        $('.volume-add').on('click', function(event) {
            event.preventDefault();
            var poolName = $(this).data('name');
            kimchi.selectedSP = poolName;
            wok.window.open('plugins/kimchi/storagepool-add-volume.html');
        });

        $('.storage-action').on('click', function(event) {
            event.preventDefault();
            var storage_action = $(this);
            var deleteButton = storage_action.find('.pool-delete');
            var deactivateButton = storage_action.find('.pool-deactivate');
            var in_use = deleteButton.data('inuse');
            if ('active' === deleteButton.data('stat') || in_use) {
                deleteButton.parent().addClass('disabled');
            } else {
                deleteButton.parent().removeClass('disabled');
            }

            if (in_use) {
                deactivateButton.parent().addClass('disabled');
            } else {
                deactivateButton.parent().removeClass('disabled');
            }
        });

        $('.pool-extend').on('click', function(event) {
            event.preventDefault();
            var poolName = $(this).data('name');
            kimchi.selectedSP = poolName;
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
};

kimchi._generateVolumeHTML = function(volume) {
    if(volume['type'] === 'kimchi-iso') {
        return '';
    }
    var volumeHtml = $('#volumeTmpl').html();
    volume.used_by_formatted = '';
    volume.used_by_text = '';
    volume.checkbox = volume.name.replace(/[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/gi,'-'),
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
    if(volume.used_by.length){
        for (var i = 0; i < volume.used_by.length; i++) {
                    (i + 1 < volume.used_by.length) ? volume.used_by_text += volume.used_by[i] +', ' : volume.used_by_text += volume.used_by[i];
                    (i + 1 < volume.used_by.length) ? volume.used_by_formatted += volume.used_by[i] +'<br />' : volume.used_by_formatted += volume.used_by[i];
        }
    }else {
        volume.used_by_formatted = '';
        volume.used_by_text = '--';
    }
    volume.capacity = wok.changetoProperUnit(volume.capacity,1);
    volume.allocation = wok.changetoProperUnit(volume.allocation,1);
    volumeHtml = wok.substitute(volumeHtml, volume);
    volumeHtml = $.trim(volumeHtml);
    volumeHtml = $.parseHTML(volumeHtml);
    if(!volume.used_by.length){
        $('i.fa.fa-exclamation-circle',volumeHtml).remove();
        $('span.format-text',volumeHtml).removeAttr('title data-toggle data-original-title data-placement');
    }
    return volumeHtml[0].outerHTML;
};


kimchi.getPoolUsageIcon = function(usage) {
    if (usage <= 100 && usage >= 85)
        return 'icon-high';

    if (usage <= 85 && usage >= 75)
        return 'icon-med';

    return 'icon-low';
};


kimchi.doUpdateStoragePool = function(poolObj){
    var poolName = poolObj.data('name');
    kimchi.getStoragePool(poolName, function(result) {
        result.usage = Math.round(result.allocated / result.capacity * 100) || 0;
        result.icon = kimchi.getPoolUsageIcon(result.usage);
        result.allocated = wok.changetoProperUnit(result.allocated,1);
        $('> .column-usage > .usage-icon',poolObj).attr('class', 'usage-icon').addClass(result.icon).text(result.usage);
        $('> .column-allocated',poolObj).attr('val',result.allocated).text(result.allocated);
    },function(){
        return false;
    });
};

kimchi.doListVolumes = function(poolObj) {
    var poolName = poolObj.data('name');

    var getOngoingVolumes = function() {
        var result = {};
        var clone = 'status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/storagepools/.+/storagevolumes/.+/clone');
        var filter = 'status=running&target_uri=' + encodeURIComponent('^/plugins/kimchi/storagepools/' + poolName + '/*');
        kimchi.getTasksByFilter(filter, function(tasks) {
            for(var i = 0; i < tasks.length; i++) {
                if(tasks[i].message !== 'cloning volume') {
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
            }
        }, null, true);
        kimchi.getTasksByFilter(clone, function(tasks) {
            for(var i = 0; i < tasks.length; i++) {
                if(tasks[i].message === 'cloning volume') {
                    var volumeName = tasks[i].target_uri.split('/')[6];
                    result[volumeName] = tasks[i];

                    if(kimchi.trackingTasks.indexOf(tasks[i].id) >= 0) {
                        continue;
                    }

                    kimchi.trackTask(tasks[i].id, function(result) {
                        wok.topic('kimchi/volumeCloneFinished').publish(result);
                    }, function(result) {
                        wok.topic('kimchi/volumeCloneError').publish(result);
                    }, function(result) {
                        wok.topic('kimchi/volumeCloneProgress').publish(result);
                    });
                }
            }
        }, null, true);
        return result;
    };

    var volumeDiv = $('#volume-' + poolName);
    var volumeDatatable = $('.wok-datagrid > .wok-datagrid-body',volumeDiv);
    var slide = $('.volumes', poolObj);
    var handleArrow = $('.arrow-down', poolObj);
    kimchi.listStorageVolumes(poolName, function(result) {
        var listHtml = '';
        var ongoingVolumes = [];
        var ongoingVolumesMap = getOngoingVolumes();
        $.each(ongoingVolumesMap, function(volumeName, task) {
            ongoingVolumes.push(volumeName);
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
            if (ongoingVolumes.indexOf(value.name) === -1) {
                $(volumeDatatable).empty();
                value.poolname = poolName;
                listHtml += kimchi._generateVolumeHTML(value);
            }
        });

        if (listHtml.length > 0) {
            $(volumeDatatable).empty();
            $('.filter',volumeDiv).prop('disabled',false);
            $('.toggle-gallery',volumeDiv).prop('disabled',false);
            $(volumeDatatable).html(listHtml);

        } else {
            $(volumeDatatable).empty();
            $('.filter',volumeDiv).prop('disabled',true);
            $('.toggle-gallery',volumeDiv).prop('disabled',true);
            $(volumeDatatable).html("<div class='pool-empty wok-datagrid-row'><span class='volume-empty'>" + i18n['KCHPOOL6002M'] + "</span></div>");
        }

        $.each(ongoingVolumesMap, function(volumeName, task) {
            wok.topic('kimchi/volumeTransferProgress').publish(task);
        });

        var checkbox = volumeDiv.find('[name="selected-volume[]"]');
        checkbox.trigger('change');
        checkbox.prop('checked',false);
        poolObj.removeClass('in');
        kimchi.changeArrow(handleArrow);
        slide.slideDown('slow');

        $(window).resize(function() {
          $('.pool-action.open', volumeDiv).removeClass('open');
        });

        $('.pool-action', volumeDiv).on('show.bs.dropdown', function () {
            $(volumeDiv).scrollTop(0);
            $(volumeDiv).bind('mousewheel DOMMouseScroll', function(e) {
                e.preventDefault();
            });
        });

        $('.pool-action', volumeDiv).on('hide.bs.dropdown', function () {
            $(volumeDiv).unbind('mousewheel DOMMouseScroll');
            $(this).removeAttr( 'style' );
            $('.toggle-gallery',volumeDiv).removeAttr( 'style' );
        });

        kimchi.doUpdateStoragePool(poolObj);

        $('[data-toggle="tooltip"]', volumeDiv).tooltip();

        volumeDivId = volumeDiv.attr('id');

        volumeOptions = {
            valueNames: ['volume-name-filter', 'volume-format-filter', 'volume-type-filter']
        };
        volumeFilterList = new List(volumeDivId, volumeOptions);

        volumeFilterList.sort('volume-name-filter', {
            order: "asc"
        });

    }, function(err) {
        wok.message.error(err.responseJSON.reason);
    }, false);
};

kimchi.initLogicalPoolExtend = function() {
    $('#logicalPoolExtend').on('hidden.bs.modal', function () {
        $('.host-partition', '#logicalPoolExtend').empty();
    });

    $('#logicalPoolExtend').on('show.bs.modal', function() {
        // Make any change in the form fields enables the
        // 'savePartitions' button if all the visible form
        // fields are filled, disables it otherwise.
        $('#logicalPoolExtend').on('input change propertychange', function() {
            if ($("input[name=devices]:checked").length === 0) {
                $("#savePartitions").attr("disabled", true);
            }
            else {
                $("#savePartitions").attr("disabled", false);
            }
        });

        kimchi.listHostPartitions(function(data) {
            if (data.length > 0) {
                var deviceHtml = $('#partitionTmpl').html();
                var listHtml = '<table class="table table-hover"><thead><tr><th></th><th>Device</th><th>Path</th><th>Size (GiB)</th></tr></thead><tbody>';
                valid_types = ['part', 'disk', 'mpath'];
                $.each(data, function(index, value) {
                    if (valid_types.indexOf(value.type) !== -1) {
                        value.size = (value.size / 1000000000).toFixed(2);
                        listHtml += wok.substitute(deviceHtml, value);
                    }
                });
                listHtml += '</tbody></table>';
                var infoHtml = '<h3>' + i18n['KCHPOOL6019M'].replace('%1', '<strong>' + kimchi.selectedSP + '</strong>') + '</h3>';
                $('.host-partition', '#logicalPoolExtend').html(infoHtml + listHtml);
            } else {
                $('.host-partition').html(i18n['KCHPOOL6011M']);
                $('.host-partition').addClass('text-help');
            }
        }, function(err) {
            $('.host-partition').html(i18n['KCHPOOL6013M'] + '<br/>(' + err.responseJSON.reason + ')');
            $('.host-partition').addClass('text-help');
        });

        $('#savePartitions', '#logicalPoolExtend').on('click', function(event) {
            event.preventDefault();
            var devicePaths = [];
            $("input[type='checkbox']:checked", "#logicalPoolExtend").each(function() {
                devicePaths.push($(this).prop('value'));
            });
            kimchi.updateStoragePool(kimchi.selectedSP, {
                disks: devicePaths
            }, function(pool) {
                $('#logicalPoolExtend').modal('hide');
                var item = '#' + pool.name;
                var usage = Math.round(pool.allocated / pool.capacity * 100) || 0;
                var usageIcon = kimchi.getPoolUsageIcon(usage);
                $(".usage-icon", $(".column-usage", item)).attr('class', 'usage-icon').addClass(usageIcon).text(usage);
                $(".column-capacity", item).text(wok.changetoProperUnit(pool.capacity, 1));
                $(".column-allocated", item).text(wok.changetoProperUnit(pool.allocated, 1));
            }, function(err) {
                $('#savePartitions', '#logicalPoolExtend').prop('disabled', true);
                $('#logicalPoolExtend').modal('hide');
            });
        });

    });

};

kimchi.storage_main = function() {
    $('body').removeClass('wok-list wok-gallery');

    var toolsHtml = '<li><a id="storage-pool-add" class="btn-tool" href="javascript:void(0);">'
    toolsHtml += '<i class="fa fa-plus-circle"></i><span>' + i18n['KCHPOOL6020M'] + '</span></a></li>'

    if(wok.tabMode['storage'] === 'admin') {
        $('#toolbar ul.tools').html(toolsHtml);
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

    wok.topic('kimchi/storageVolumeDeleted').subscribe(function() {
        pool = kimchi.selectedSP;
        var poolNode = $('.storage-li[data-name="' + pool + '"]');
        kimchi.doListVolumes(poolNode);
    });

    wok.topic('kimchi/storageVolumeWiped').subscribe(function() {
        pool = kimchi.selectedSP;
        var poolNode = $('.storage-li[data-name="' + pool + '"]');
        kimchi.doListVolumes(poolNode);
    });
    wok.topic('kimchi/storageVolumeCloned').subscribe(function() {
        pool = kimchi.selectedSP;
        var poolNode = $('.storage-li[data-name="' + pool + '"]');
        kimchi.doListVolumes(poolNode);
    });

    wok.topic('kimchi/storageVolumeResized').subscribe(function() {
        pool = kimchi.selectedSP;
        var poolNode = $('.storage-li[data-name="' + pool + '"]');
        kimchi.doListVolumes(poolNode);
    });

    wok.topic('kimchi/volumeTransferProgress').subscribe(function(result) {
        var extractProgressData = function(data) {
            var sizeArray = /(\d+)\/(\d+)/g.exec(data) || [0, 0, 0];
            var downloaded = sizeArray[1];
            var total = sizeArray[2];
            var percent = 0;
            if(downloaded) {
                if(!isNaN(total)) {
                    percent = downloaded / total * 100;
                }
            }
            var formatted = wok.formatMeasurement(downloaded, { base: 10,  converter: wok.localeConverters["number-locale-converter"]});
            var formattedTotal = !isNaN(total) ? wok.formatMeasurement(total, { base: 10,  converter: wok.localeConverters["number-locale-converter"]}) : '';
            var size = (1.0 * formatted['v']).toFixed(1) + formatted['s'] + ( formattedTotal !== '' ? ' / '+ (1.0 * formattedTotal['v']).toFixed(1) + formattedTotal['s'] : formattedTotal );
            return {
                size: size,
                percent: percent
            };
        };

        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[4];
        var volumeName = uriElements.pop();
        var progress = extractProgressData(result['message']);
        var size = progress['size'];
        var percent = progress['percent'];
        volumeBox = $('#volume-' + poolName + ' [data-volume-name="' + volumeName + '"]').closest('.wok-datagrid-row');
        $('.volume-progress', volumeBox).removeClass('hidden');
        $('.column-progress', volumeBox).removeClass('hidden');
        $('.column-progress', '.wok-datagrid-header').removeClass('hidden');
        $('.volume-inline-progress', volumeBox).removeClass('hidden');
        $('.column-format > .format-text', volumeBox).text('--');
        $('.progress-bar', volumeBox).attr('aria-valuenow',percent+'%').css('width',percent+'%');
        $('input[type="checkbox"]',volumeBox).prop('disabled',true);
        $(volumeBox).addClass('in-progress')
        $('.volume-box-inner', volumeBox).attr({'data-toggle':'tooltip','data-original-title': i18n['KCHPOOL6014M'] + ' ' +size});
        $('.tooltip-inner', volumeBox).text(i18n['KCHPOOL6014M']+' '+size);
        $('.progress-transferred', volumeBox).text(size);
        $('.progress-status', volumeBox).text(i18n['KCHPOOL6014M']);
        $('[data-toggle="tooltip"]',volumeBox).tooltip();
    });

    wok.topic('kimchi/volumeTransferFinished').subscribe(function(result) {
        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[4];
        var volumeName = uriElements.pop();
        volumeBox = $('#volume-' + poolName + ' [data-volume-name="' + volumeName + '"]').closest('.wok-datagrid-row');
        $(volumeBox).removeClass('in-progress')
        $('.volume-progress', volumeBox).addClass('hidden');
        $('.column-progress', volumeBox).addClass('hidden');
        $('.column-progress', '.wok-datagrid-header').addClass('hidden');
        $('.volume-inline-progress', volumeBox).addClass('hidden');
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
        var poolName = uriElements[4];
        var volumeName = uriElements.pop();
        volumeBox = $('#volume-' + poolName + ' [data-volume-name="' + volumeName + '"]').closest('.wok-datagrid-row');
        $('.progress-status', volumeBox).text(i18n['KCHPOOL6015M']);
    });

    wok.topic('kimchi/volumeCloneFinished').subscribe(function(result) {
        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[4];
        var poolNode = $('.storage-li[data-name="' + poolName + '"]');
        kimchi.doListVolumes(poolNode);
    });

    wok.topic('kimchi/volumeCloneProgress').subscribe(function(result) {
        var uriElements = result.target_uri.split('/');
        var poolName = uriElements[4];
        var volumeName = uriElements[6];
        volumeBox = $('#volume-' + poolName + ' [data-volume-name="' + volumeName + '"]').closest('.wok-datagrid-row');
        $('.column-progress', volumeBox).removeClass('hidden');
        $('.column-progress', '.wok-datagrid-header').removeClass('hidden');
        $('.volume-inline-progress', volumeBox).removeClass('hidden');
        $('.column-format > .format-text', volumeBox).text('--');
        $('input[type="checkbox"]',volumeBox).prop('disabled',true);
        $(volumeBox).addClass('in-progress')
        $('.volume-box-inner', volumeBox).attr({'data-toggle':'tooltip','data-original-title': i18n['KCHPOOL6014M'] });
        $('.tooltip-inner', volumeBox).text(i18n['KCHPOOL6014M']);
        $('.progress-status', volumeBox).text(i18n['KCHPOOL6014M']);
        $('[data-toggle="tooltip"]',volumeBox).tooltip();
    });

    wok.topic('kimchi/volumeCloneError').subscribe(function(result) {
        // Error message from Async Task status
        if (result['message']) {
            var errText = result['message'];
        }
        // Error message from standard kimchi exception
        else {
            var errText = result['responseJSON']['reason'];
        }
        result && wok.message.error(errText);
    });

};

kimchi.changeArrow = function(obj) {
    if ($(obj).hasClass('arrow-down')) {
        $(obj).removeClass('arrow-down').addClass('arrow-up');
    } else {
        $(obj).removeClass('arrow-up').addClass('arrow-down');
    }
};
