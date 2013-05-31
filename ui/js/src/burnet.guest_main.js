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
burnet.initVmButtonsAction = function() {
	$('.circle').circle();

	$(".vm-start").each(function(index) {
		if('running'===$(this).data('vmstate')) {
			$(this).hide();
		} else {
			$(this).show();
		}
	});

	$(".vm-stop").each(function(index) {
		if('running'===$(this).data('vmstate')) {
			$(this).show();
		} else {
			$(this).hide();
		}
	});

	$(".vm-start").on("click", function(event) {
		burnet.startVM($(this).data('vm'), function(result) {
			burnet.listVmsAuto();
		},function() {
			burnet.message.error('Failed to start');
		});
	});

	$(".vm-stop").on("click", function(event) {
		burnet.stopVM($(this).data('vm'), function(result) {
			burnet.listVmsAuto();
		},function() {
			burnet.message.error('Failed to stop');
		});
	});

	$(".vm-reset").on("click", function(event) {
		if('running'===$(this).data('vmstate')) {
			burnet.resetVM($(this).data('vm'), function(result) {
				burnet.listVmsAuto();
			},function() {
				burnet.message.error('Failed to reset');
			});
		} else {
			burnet.startVM($(this).data('vm'), function(result) {
				burnet.listVmsAuto();
			},function() {
				burnet.message.error('Failed to start');
			});
		}
	});

	$(".vm-delete").on("click", function(event) {
		burnet.deleteVM($(this).data('vm'), function(result) {
			burnet.listVmsAuto();
		},function() {
			burnet.message.error('Failed to delete');
		});
	});

	$(".vm-vnc").on("click", function(event) {
		burnet.vncToVM($(this).data('vm'));
	});
};

burnet.listVmsAuto = function() {
	if(burnet.vmTimeout) {
		clearTimeout(burnet.vmTimeout);
	}
	burnet.listVMs(function(result) {
		if(result && result.length) {
			var listHtml='';
			var guestTemplate = $('#tmpl-guest').html();
			$.each(result, function(index, value) {
				listHtml+=burnet.template(guestTemplate, value);
			});
			$('#guestList').html(listHtml);
			burnet.initVmButtonsAction();
		}
	},function() {
		burnet.message.error('Failed to list guests');
	});
	burnet.vmTimeout = window.setTimeout("burnet.listVmsAuto();", 5000);
};

burnet.guest_main = function() {
	$("#vm-add").on("click", function(event) {
		burnet.window.open('guest-add.html');
	});
	burnet.listVmsAuto();
};
