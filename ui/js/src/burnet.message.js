/*
 * Project Burnet
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
burnet.message = function(msg, level) {
	if ($('#messageField').size() < 1) {
		$(document.body).append('<div id="messageField"></div>');
	}
	var message = '<div class="message ' + (level || '') + '" style="display: none;">';
	message += '<div class="close">X</div>';
	message += '<div class="content">' + msg + '</div>';
	message += '</div>';
	var $message = $(message);
	$('#messageField').append($message);
	$message.fadeIn(100);

	setTimeout(function() {
		$message.fadeOut(2000, function() {
			$(this).remove();
		});
	}, 2000);

	$('#messageField').on("click", ".close", function(e) {
		$(this).parent().fadeOut(200, function() {
			$(this).remove();
		});
	});
};

burnet.message.warn = function(msg) {
	burnet.message(msg, 'warn');
};
burnet.message.error = function(msg) {
	burnet.message(msg, 'error');
};
burnet.message.success = function(msg) {
	burnet.message(msg, 'success');
};
