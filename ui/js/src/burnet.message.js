/*
 * Project Burnet
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwanghl@cn.ibm.com>
 *
 * All Rights Reserved.
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
