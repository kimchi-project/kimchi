/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013
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
                value.usage = parseInt(value.allocated / value.capacity * 100) || 0;
                value.capacity = kimchi.changetoProperUnit(value.capacity,1);
                value.allocated = kimchi.changetoProperUnit(value.allocated,1);
                if ('kimchi-iso' !== value.type) {
                    listHtml += kimchi.substitute(storageHtml, value);
                }
            });
            $('#storagepoolsList').html(listHtml);
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

    $('.storage-action').on('click', function() {
        var storage_action = $(this);
        var deleteButton = storage_action.find('.pool-delete');
        if ('active' === deleteButton.data('stat')) {
            deleteButton.attr('disabled', 'disabled');
        } else {
            deleteButton.removeAttr('disabled');
        }
    });

    $('#volume-doAdd').on('click', function() {
        kimchi.window.open('storagevolume-add.html');
    });
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

kimchi.doListVolumes = function(poolObj) {
    var volumeDiv = $('#volume' + poolObj.data('name'));
    var slide = poolObj.next('.volumes');
    var handleArrow = poolObj.children().last().children();
    kimchi.listStorageVolumes(poolObj.data('name'), function(result) {
        var volumeHtml = $('#volumeTmpl').html();
        if (result) {
            if (result.length) {
                var listHtml = '';
                $.each(result, function(index, value) {
                    value.poolname = poolObj.data('name');
                    value.capacity = kimchi.changetoProperUnit(value.capacity,1);
                    value.allocation = kimchi.changetoProperUnit(value.allocation,1);
                    listHtml += kimchi.substitute(volumeHtml, value);
                });
                volumeDiv.html(listHtml);
            } else {
                volumeDiv.html("<div class='pool-empty'>" + i18n['KCHPOOL6002M'] + "</div>");
            }
            poolObj.removeClass('in');
            kimchi.changeArrow(handleArrow);
            slide.slideDown('slow');
        }
    }, function(err) {
        kimchi.message.error(err.responseJSON.reason);
    });
}

kimchi.storage_main = function() {
    $('#storage-pool-add').on('click', function() {
        kimchi.window.open('storagepool-add.html');
    });
    kimchi.doListStoragePools();
}

kimchi.changeArrow = function(obj) {
    if ($(obj).hasClass('arrow-down')) {
        $(obj).removeClass('arrow-down').addClass('arrow-up');
    } else {
        $(obj).removeClass('arrow-up').addClass('arrow-down');
    }
}
