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
