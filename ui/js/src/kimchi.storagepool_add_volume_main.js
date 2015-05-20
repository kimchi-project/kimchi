/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014-2015
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
        var chunkSize = 8 * 1024 * 1024; // 8MB
        var uploaded = 0;

        var blobFile = $(localFileBox)[0].files[0];

        var createUploadVol = function() {
            kimchi.createVolumeWithCapacity(kimchi.selectedSP, {
                name: blobFile.name,
                format: '',
                capacity: blobFile.size,
                upload: true
            }, function(result) {
                kimchi.window.close();
                trackVolCreation(result.id);
            }, onError);
        };

        var uploadRequest = function(blob) {
            var fd = new FormData();
            fd.append('chunk', blob);
            fd.append('chunk_size', blob.size);

            kimchi.uploadVolumeToSP(kimchi.selectedSP, blobFile.name, {
                formData: fd
            }, function(result) {
                if (uploaded < blobFile.size)
                    setTimeout(doUpload, 500);
            }, onError);

            uploaded += blob.size
        };

        // Check file exists and has read permission
        try {
            var blob = blobFile.slice(0, 20);
            var reader = new FileReader();
            reader.onloadend = function(e) {
                if (e.loaded == 0)
                    kimchi.message.error.code('KCHAPI6008E');
                else
                    createUploadVol();
            };

            reader.readAsBinaryString(blob);
        } catch (err) {
            kimchi.message.error.code('KCHAPI6008E');
            return;
        }

        var doUpload = function() {
            try {
                var blob = blobFile.slice(uploaded, uploaded + chunkSize);
                var reader = new FileReader();
                reader.onloadend = function(e) {
                    if (e.loaded == 0)
                        kimchi.message.error.code('KCHAPI6009E');
                    else
                        uploadRequest(blob);
                };

                reader.readAsBinaryString(blob);
            } catch (err) {
                kimchi.message.error.code('KCHAPI6009E');
                return;
            }
        }

        var trackVolCreation = function(taskid) {
            var onTaskResponse = function(result) {
                var taskStatus = result['status'];
                var taskMsg = result['message'];
                if (taskStatus == 'running') {
                    if (taskMsg != 'ready for upload') {
                        setTimeout(function() {
                            trackVolCreation(taskid);
                        }, 2000);
                    } else {
                        kimchi.topic('kimchi/storageVolumeAdded').publish();
                        doUpload();
                    }
                }
            };
            kimchi.getTask(taskid, onTaskResponse, onError);
        };
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
