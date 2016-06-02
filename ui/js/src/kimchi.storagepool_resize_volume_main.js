/*
 * Project Kimchi
 *
 * Copyright IBM Corp, 2016
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

kimchi.sp_resize_volume_main = function() {

    var addButton = $('#sp-resize-volume-button');
    var size = $('#volume-size');
    var form = $('form#form-sp-resize-volume');

    $(addButton).prop('disabled',true);
    $(size).on('keyup', function(){
        if($(this).val().length !==0) {
            addButton.prop('disabled', false);
        } else{
            addButton.prop('disabled',true);
        }
    });
    $(addButton).on('click',function(e){
        e.preventDefault();
        e.stopPropagation();
        $(form).submit();
    });
    $(form).on('submit',function(e){
        e.preventDefault();
        e.stopPropagation();
        var newsize = parseInt($(size).val());
        var bytes = newsize * 1048576;
        var data = {};
        data = {
            size: bytes
        };
      kimchi.resizeStoragePoolVolume(kimchi.selectedSP, kimchi.selectedVolumes[0], data, function() {
          $(size).prop('disabled', true);
          $(addButton).prop('disabled',true);
          wok.topic('kimchi/storageVolumeResized').publish();
          wok.window.close();
      }, function(err) {
          wok.message.error(err.responseJSON.reason, '#alert-modal-container');
          $(size).prop('disabled', false);
          $(addButton).prop('disabled',false);
          $(size).focus();
      });
  });
}
