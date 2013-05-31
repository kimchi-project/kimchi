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
burnet.window = {
	open : function(url) {
		if ($("#windowField").size() < 1) {
			$(document.body).append('<div id="windowField" class="bgmask" style="display: none;"></div>');
			$('#windowField').on('click', '.window .close', function(event) {
				burnet.window.close();
			});
		}
		$("#windowField").load(url).fadeIn(100);
	},
	close : function() {
		$("#windowField").fadeOut(100, function() {
			$(this).empty();
		});
	}
};
