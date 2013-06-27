/*
 * Project Burnet
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Mei Na Zhou <zhmeina@cn.ibm.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *	 http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
burnet.doListTemplates = function() {
	burnet.listTemplates(function(result) {
		var titleValue = {'tempnum': result.length};
		var titleTemp = $('#titleTmpl').html();
		var titleHtml = '';
		if (result.length) {
			titleHtml = burnet.template(titleTemp,titleValue);
		}
		else {
			titleHtml = titleTemp.replace('{tempnum}', '0');
		}
		$('#templateTitle').html(titleHtml);
		var templateHtml = $('#templateTmpl').html();
		if(result && result.length) {
			var listHtml='';
			$.each(result, function(index, value) {
				listHtml += burnet.template(templateHtml,value);
			});
			$('#templateList').html(listHtml);
			burnet.bindClick();
		}
		else {
			$('#templateList').html("");
		}
	},function() {
		burnet.message.error(i18n['burnet.list.template.fail.msg']);
	});
};

burnet.bindClick=function() {
	$('.template-edit').on('click', function(event) {
		var templateName = $(this).data('template');
		burnet.selectedTemplate = templateName;
		burnet.window.open("template-edit.html");
	});
	$('.template-delete').on('click', function(event) {
		var templateName = $(this).data('template');
		burnet.deleteTemplate(templateName,"","");
		burnet.doListTemplates();
	});
}
burnet.hideTitle = function() {
	$('#tempTitle').hide();
};

burnet.template_main = function() {
	$("#template-add").on("click", function(event) {
		burnet.window.open('template-add.html');
	});
	burnet.doListTemplates();
};
