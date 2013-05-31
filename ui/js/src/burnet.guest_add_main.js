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
burnet.guest_add_main = function() {
	burnet.listTemplates(function(result) {
		if(result && result.length) {
			var html='';
			var tmpl = $('#tmpl-template').html();
			$.each(result, function(index, value) {
				html+=burnet.template(tmpl, value);
			});
			$('#templateTile').html(html);
		}
	},function() {
		burnet.message.error('Failed to list templates');
	});

	$('#vm-doAdd').on('click', function(event) {
		var formData = $('#form-vm-add').serializeObject();

		if(!formData.template) {
			burnet.message.warn('Please choose a template!');
			return;
		}
		burnet.createVM(formData,function() {
			burnet.listVmsAuto();
			burnet.window.close();
		},function() {
			burnet.message.error('Failed to create vm');
		});
	});
};
