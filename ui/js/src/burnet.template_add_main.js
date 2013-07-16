/*
 * Project Burnet
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Xin Ding <xinding@cn.ibm.com>
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
burnet.template_add_main = function() {

	function init_iso_location_box() {
		$('#iso_location_box').hide();
		$('#iso_local').prop('checked', false);
		$('#iso_internet').prop('checked', false);
	}
	function init_iso_file_box() {
		$('#iso_file_box').hide();
		$('#iso_file').val('');
		$('#btn-template-iso-create').attr('disabled', 'disabled');
	}
	function init_iso_url_box() {
		$('#iso_url_box').hide();
		$('#iso_url').val('');
		$('#btn-template-url-create').attr('disabled', 'disabled');
	}

	$('#iso_file').on('input', function() {
		if ($('#iso_file').val()) {
			$('#btn-template-iso-create').removeAttr('disabled');
		} else {
			$('#btn-template-iso-create').attr('disabled', 'disabled');
		}
	});
	$('#iso_url').on('input', function() {
		if ($('#iso_url').val()) {
			$('#btn-template-url-create').removeAttr('disabled');
		} else {
			$('#btn-template-url-create').attr('disabled', 'disabled');
		}
	});

	$('#iso_specify').click(function() {
		$('#iso_location_box').slideDown();
		init_iso_field();
	});
	$('#iso_local').click(function() {
		$('#iso_file_box').slideDown();
		init_iso_url_box();
	});
	$('#iso_internet').click(function() {
		init_iso_file_box();
		$('#iso_url_box').slideDown();
	});

	$('#btn-template-iso-create').click(function() {
		var data = {
			"name" : 'Template' + new Date().getTime(),
			"cdrom" : $('#iso_file').val()
		};
		burnet.createTemplate(data, function() {
			burnet.doListTemplates();
			burnet.window.close();
		}, function() {
			burnet.message.error('Failed to create template');
		});
	});

	$('#btn-template-url-create').click(function() {
		var data = {
			"name" : 'Template' + new Date().getTime(),
			"cdrom" : $('#iso_url').val()
		};
		burnet.createTemplate(data, function() {
			burnet.doListTemplates();
			burnet.window.close();
		}, function() {
			burnet.message.error('Failed to create template');
		});
	});

};
