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
