/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014
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
kimchi.sp_add_volume_main = function() {
    // download from remote server or upload from local file
    var type = 'download';

    var addButton = $('#sp-add-volume-button');
    var remoteURLBox = $('#volume-remote-url');
    var localFileBox = $('#volume-input-file');
    var typeRadios = $('input.volume-type');

    var isValidURL = function() {
        var url = $(remoteURLBox).val();
        return kimchi.template_check_url(url);
    };

    var isValidFile = function() {
        var fileName = $(localFileBox).val();
        return fileName.length > 0;
    };

    $(typeRadios).change(function(event) {
        $('.volume-input').prop('disabled', true);
        $('.volume-input.' + this.value).prop('disabled', false);
        type = this.value;
        if(type == 'download') {
            $(addButton).prop('disabled', !isValidURL());
        }
        else {
            $(addButton).prop('disabled', !isValidFile());
        }
    });

    $(remoteURLBox).on('input propertychange', function(event) {
        $(addButton).prop('disabled', !isValidURL());
    });

    $(localFileBox).on('change', function(event) {
        $(addButton).prop('disabled', !isValidFile());
    });

    var onError = function(result) {
        $(this).prop('disabled', false);
        $(typeRadios).prop('disabled', false);
        if(!result) {
            return;
        }
        var msg = result['message'] || (
            result['responseJSON'] && result['responseJSON']['reason']
        );
        kimchi.message.error(msg);
    };

    var fetchRemoteFile = function() {
        var volumeURL = remoteURLBox.val();
        var volumeName = volumeURL.split(/(\\|\/)/g).pop();
        kimchi.downloadVolumeToSP({
            sp: kimchi.selectedSP,
            url: volumeURL
        }, function(result) {
            kimchi.window.close();
            kimchi.topic('kimchi/storageVolumeAdded').publish();
        }, onError);
    };

    var uploadFile = function() {
        var blobFile = $(localFileBox)[0].files[0];
        var fileName = blobFile.name;
        var fd = new FormData();
        fd.append('name', fileName);
        fd.append('file', blobFile);
        kimchi.uploadVolumeToSP({
            sp: kimchi.selectedSP,
            formData: fd
        }, function(result) {
            kimchi.window.close();
            kimchi.topic('kimchi/storageVolumeAdded').publish();
        }, onError);
    };

    $(addButton).on('click', function(event) {
        $(this).prop('disabled', true);
        $(typeRadios).prop('disabled', true);
        if(type === 'download') {
            fetchRemoteFile();
        }
        else {
            uploadFile();
        }
        event.preventDefault();
    });
};
