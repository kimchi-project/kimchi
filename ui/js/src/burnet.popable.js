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
burnet.popable = function() {
	$(document).click(function(e) {
		$('.popable').removeClass('open');
	});
	$(document).on("click", ".popable", function(e) {
		var isOpen = $(this).hasClass('open');
		$(".popable").removeClass('open');
		if (!isOpen) {
			$(this).addClass('open');
		}
		e.preventDefault();
		e.stopPropagation();
	});
};
