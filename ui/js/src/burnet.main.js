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
burnet.main = function() {
	burnet.popable();

	$('#nav-menu a.item').on('click', function() {
	    var href = $(this).attr('href');
	    burnet.vmTimeout && clearTimeout(burnet.vmTimeout);
	    $('#main').load(href);
	    var left = $(this).parent().position().left;
	    var width = $(this).parent().width();
	    $('.menu-arrow').stop().animate({
		left: left+width/2-10
	    });
	    return false;
	});

	var currentMenu = $('.nav-menu .item.current');
	var left = currentMenu.parent().position().left;
	var width = currentMenu.parent().width();
	$('.menu-arrow').css('left', left+width/2-10);

	$('#main').load('guest.html');
};
