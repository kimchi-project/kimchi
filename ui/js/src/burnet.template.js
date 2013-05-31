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
burnet.template = function(templateStr, data, tag) {
	tag = tag || /\{([^\}]+)\}/g;

	return templateStr.replace(tag, function(matchResult, express) {
		var propertyArray = express.split('!');
		var defaultValue = propertyArray[1] || '';
		propertyArray = propertyArray[0].split('.');
		var value = data, i = 0, l = propertyArray.length, property;
		for (; i < l; i++) {
			property = propertyArray[i];
			if (value) {
				value = value[property];
			} else {
				break;
			}
		}
		return value || defaultValue;
	});
};
