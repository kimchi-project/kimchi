/*
 * Project Kimchi
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
(function($) {
	$.fn.serializeObject = function() {
		var formDataArray = $(this).serializeArray();
		var formData = {};
		$.each(formDataArray, function(index, data) {
			if (formData[data.name] === undefined) {
				formData[data.name] = data.value;
			} else {
				if (formData[data.name] instanceof Array) {
					formData[data.name].push(data.value);
				} else {
					var oldValue = formData[data.name];
					formData[data.name] = [];
					formData[data.name].push(oldValue);
					formData[data.name].push(data.value);
				}
			}
		});
		return formData;
	};
}(jQuery));
