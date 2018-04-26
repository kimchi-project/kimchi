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

wdi.SizeDefiner = $.spcExtend(wdi.DomainObject, {
	ERROR_CODE_SIZE: 4,
	status: null,
	STATUS_READY: 0,
	STATUS_REPLY: 1,
	STATUS_REPLY_BODY: 2,
	STATUS_ERROR_CODE: 3,
	STATUS_MESSAGE: 4,
	STATUS_HEADER: 5,
	STATUS_BODY: 6,
	isHeader: false,

	init: function(c) {
		this.status = this.STATUS_READY;
	},

	getSize: function(arr) {
		if (this.STATUS_READY === this.status) {
			this.status++;
			return wdi.SpiceLinkHeader.prototype.objectSize;
		} else if (this.STATUS_REPLY === this.status) {
			this.status++;
			return this.getReplyBodySize(arr);
		} else if (this.STATUS_REPLY_BODY === this.status) {
			this.status++;
			return this.ERROR_CODE_SIZE;
		} else if (this.STATUS_ERROR_CODE === this.status) {
			this.status++;
			this.isHeader = true;
			return 6; //wdi.SpiceDataHeader.prototype.objectSize access here is slow
		} else {
			if (this.isHeader) {
				this.isHeader = false;
				return this.getBodySizeFromArrayHeader(arr);
			} else {
				this.isHeader = true;
				return 6;//wdi.SpiceDataHeader.prototype.objectSize; access here is slow
			}
		}
	},

	getReplyBodySize: function (arr) {
		var queue = wdi.GlobalPool.create('ViewQueue');
		queue.setData(arr);
		var header = new wdi.SpiceLinkHeader().demarshall(queue);
		wdi.GlobalPool.discard('ViewQueue', queue);
		return header.size;
	},

	getBodySizeFromArrayHeader: function (arr) {
		var queue = wdi.GlobalPool.create('ViewQueue');
		queue.setData(arr);
		var header = new wdi.SpiceDataHeader().demarshall(queue);
		wdi.GlobalPool.discard('ViewQueue', queue);
		return header.size;
	},

	getStatus: function() {
		if (this.status === this.STATUS_MESSAGE && this.isHeader) {
			return this.STATUS_HEADER;
		} else if (this.status === this.STATUS_MESSAGE && !this.isHeader) {
			return this.STATUS_BODY;
		} else {
			return this.status;
		}
	}
});
