/*
 eyeOS Spice Web Client
Copyright (c) 2015 eyeOS S.L.

Contact Jose Carlos Norte (jose@eyeos.com) for more information about this software.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License version 3 as published by the
Free Software Foundation.
 
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
details.
 
You should have received a copy of the GNU Affero General Public License
version 3 along with this program in the file "LICENSE".  If not, see 
<http://www.gnu.org/licenses/agpl-3.0.txt>.
 
See www.eyeos.org for more details. All requests should be sent to licensing@eyeos.org
 
The interactive user interfaces in modified source and object code versions
of this program must display Appropriate Legal Notices, as required under
Section 5 of the GNU Affero General Public License version 3.
 
In accordance with Section 7(b) of the GNU Affero General Public License version 3,
these Appropriate Legal Notices must retain the display of the "Powered by
eyeos" logo and retain the original copyright notice. If the display of the 
logo is not reasonably feasible for technical reasons, the Appropriate Legal Notices
must display the words "Powered by eyeos" and retain the original copyright notice. 
 */

wdi.ClusterNodeChooser = $.spcExtend(wdi.EventObject.prototype, {
	init: function (c) {
	},

	setNodeList: function (nodeList) {
		this._nodeList = this._shuffle(nodeList);
		this._nodeListLength = this._nodeList.length;
		this._currentIndex = 0;
	},

	getAnother: function () {
		var toReturn = this._nodeList[this._currentIndex++ % this._nodeListLength];
		return toReturn;
	},

	// recipe from: http://stackoverflow.com/a/6274398
	_shuffle: function (list) {
		var counter = list.length,
			temp,
			index;
		while (counter > 0) {
			index = Math.floor(Math.random() * counter);
			counter--;
			temp = list[counter];
			list[counter] = list[index];
			list[index] = temp;
		}
		return list;
	}
});
