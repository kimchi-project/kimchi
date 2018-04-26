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

wdi.RunQueue = $.spcExtend(wdi.DomainObject, {
	tasks: null,
	isRunning: false,
	
	init: function() {
		this.tasks = [];
	},
	
	getTasksLength: function() {
		return this.tasks.length;
	},
	
	add: function(fn, scope, endCallback, params) {
		this.tasks.push({
			fn: fn,
			scope: scope,
            fnFinish: endCallback,
            params: params
		});
		
		return this;
	},
	
	clear: function() {
		this.tasks = [];
		
		return this;
	},
	
	_process: function() {
		wdi.ExecutionControl.sync = true;
		var proxy, self = this;
		this.isRunning = true;
		var task = this.tasks.shift();
		
		if (!task) {
			this.isRunning = false;
			return;
		}
		
		proxy = {
			end: function() {
                if(task.fnFinish) {
                    task.fnFinish.call(task.scope);
                }
				self._process();
			}
		};

		try {
			task.fn.call(task.scope, proxy, task.params);
		} catch(e) {
			wdi.Debug.error(e.message);
			proxy.end();
		}
		
		return this;
	},

	process: function() {
		if (!this.isRunning) {
			this._process();
		} else {
			return;
		}
	}
});

//wdi.ExecutionControl = $.spcExtend(wdi.DomainObject, {
//	currentProxy: null,
//	sync: true,
//	runQ: null,
//	init: function(c) {
//		this.runQ = c.runQ || new wdi.RunQueue(); 
//	}
//});

//TODO: make an instance of it on each channel
wdi.ExecutionControl = {
	currentProxy: null,
	sync: true,
	runQ: new wdi.RunQueue()
};
