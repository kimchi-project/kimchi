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

//If we are in NODE
if (typeof module !== "undefined" && module.exports) {

	jQuery = $ = {
		isArray: function (obj) {
			return Object.prototype.toString.apply(obj) === "[object Array]"
		},
		isPlainObject: function( obj ) {
			var key;

			// Must be an Object.
			// Because of IE, we also have to check the presence of the constructor property.
			// Make sure that DOM nodes and window objects don't pass through, as well
			if ( !obj || jQuery.type(obj) !== "object" || obj.nodeType || jQuery.isWindow( obj ) ) {
				return false;
			}

			// Not own constructor property must be Object
			if ( obj.constructor &&
				!core_hasOwn.call(obj, "constructor") &&
				!core_hasOwn.call(obj.constructor.prototype, "isPrototypeOf") ) {
				return false;
			}

			// Own properties are enumerated firstly, so to speed up,
			// if last one is own, then all properties are own.
			for ( key in obj ) {}

			return key === undefined || core_hasOwn.call( obj, key );
		},
		extend: function() {
			var options, name, src, copy, copyIsArray, clone,
				target = arguments[0] || {},
				i = 1,
				length = arguments.length,
				deep = false;

			// Handle a deep copy situation
			if ( typeof target === "boolean" ) {
				deep = target;
				target = arguments[1] || {};
				// skip the boolean and the target
				i = 2;
			}

			// extend jQuery itself if only one argument is passed
			if ( length === i ) {
				target = this;
				--i;
			}

			for ( ; i < length; i++ ) {
				// Only deal with non-null/undefined values
				if ( (options = arguments[ i ]) != null ) {
					// Extend the base object
					for ( name in options ) {
						src = target[ name ];
						copy = options[ name ];

						// Prevent never-ending loop
						if ( target === copy ) {
							continue;
						}

						// Recurse if we're merging plain objects or arrays
						if ( deep && copy && ( this.isPlainObject(copy) || (copyIsArray = this.isArray(copy)) ) ) {
							if ( copyIsArray ) {
								copyIsArray = false;
								clone = src && this.isArray(src) ? src : [];

							} else {
								clone = src && this.isPlainObject(src) ? src : {};
							}

							// Never move original objects, clone them
							target[ name ] = this.extend( deep, clone, copy );

						// Don't bring in undefined values
						} else if ( copy !== undefined ) {
							target[ name ] = copy;
						}
					}
				}
			}

			// Return the modified object
			return target;
		}
	};
}

$.extend({
	spcExtend: function(obj) {
		var f = function(c) {
			if(typeof this['init'] !== 'undefined') {
				this.init(c || {});
			}
		};
		f.prototype.superInit = obj.init;
		var args = [];
		args.push(f.prototype);
		var length = arguments.length;
		for(var i =0; i<length;i++) {
			args.push(arguments[i]);
		}

		$.extend.apply($, args);
		return f;
	}
});

$.extend(String.prototype, {
	lpad: function(padString, length) {
		var str = this;
		while (str.length < length)
		   str = padString + str;
		return str;
	},

	rpad: function(padString, length) {
		var str = this;
		while (str.length < length)
		   str = str + padString;
		return str;
	}
});

wdi = {};

wdi.DomainObject = {};

wdi.RawMessage = $.spcExtend(wdi.DomainObject, {
	status: null,
	data: null,

	init: function(c) {
		this.status = c.status;
		this.data = c.data;
	}
});

wdi.RawSpiceMessage = $.spcExtend(wdi.DomainObject, {
	header: null,
	body: null,
	channel: null,

	set: function(header, body, channel) {
		this.header = header;
		this.body = body;
		this.channel = channel;
	}
});

wdi.SpiceMessage = $.spcExtend(wdi.DomainObject, {
	messageType: null,
	args: null,
	channel: null,

	init: function(c) {
		this.channel = c.channel;
		this.messageType = c.messageType;
		this.args = c.args;
	}
});

wdi.EventObject = $.spcExtend(wdi.DomainObject, {
	events: null,

	init: function() {
		this.eyeEvents = {};
	},

	getListenersLength: function(eventName) {
		if (this.eyeEvents[eventName] == undefined) {
			this.eyeEvents[eventName] = [];
		}

		return this.eyeEvents[eventName].length;
	},

	addListener: function(eventName, fn, scope) {
		scope = scope || this;

		if (this.eyeEvents[eventName] == undefined) {
			this.eyeEvents[eventName] = [];
		}

		this.eyeEvents[eventName].push({
			fn: fn,
			scope: scope
		});
	},

	removeEvent: function(eventName) {
		this.eyeEvents[eventName] = undefined;
	},

	clearEvents: function() {
		this.eyeEvents = {};
	},

	fire: function(eventName, params) {
		var listeners = this.eyeEvents[eventName];
		if(listeners) {
			var size = listeners.length;
			while(size--) {
				listeners[size].fn.call(listeners[size].scope, params);
			}
		}
	}
});

wdi.CHANNEL_STATUS = {
	disconnected:-1,
	idle:0,
	establishing:1,
	established:2
};

wdi.Debug = {
	debug: false,

	/* these logging functions accept multiple parameters, and will be passed
	 * directly to console.{log,info,warn,error}(), so we can have better
	 * messages.
	 *
	 * Call them with multiple params instead of concatenating:
	 * YES: wdi.Debug.log("something happened: ", whatever);
	 * NO : wdi.Debug.log("something happened: " + whatever);
	 */

	log: function(variable_list_of_args /* , ... */) {
		if (this.debug) {
			console.log.apply(console, Array.prototype.slice.call(arguments));
		}
	},

	warn: function(variable_list_of_args /* , ... */) {
		console.warn.apply(console, Array.prototype.slice.call(arguments));
	},

	info: function(variable_list_of_args /* , ... */) {
		if (this.debug) {
			console.info.apply(console, Array.prototype.slice.call(arguments));
		}
	},

	error: function(variable_list_of_args /* , ... */) {
		console.error.apply(console, Array.prototype.slice.call(arguments));
	}
};

wdi.Utils = {
    generateWebSocketUrl: function(protocol, host, port, destHost, destPort, type, destInfoToken) {
        /**
         * Generates websockify URL.
         * If destHost and destPort are available, they are used to form explicit URL with host and port.
         * If not, an URL with destInfoToken is generated, host and port are resolved by backend service.
         */
        if ( ! destHost || ! destPort ) {
            url = protocol + '://' + host + ':' + port + '/websockify/destInfoToken/' + destInfoToken + '/type/' + type;
        } else {
            url = protocol + '://' + host + ':' + port + '/websockify/host/' + destHost + '/port/' + destPort + '/type/' + type;
        }
        return url;
    }
};

wdi.postMessageW3CCompilant = typeof window !== "undefined" && window['bowser'] && !(window['bowser']['msie'] && window['bowser']['version'] >= 10);

wdi.Exception = $.spcExtend(wdi.DomainObject, {
	errorCode: null,
	message: null,

	init: function(c) {
		this.message = c.message || '';
		this.errorCode = c.errorCode || 0;
	}
});

try {
	new ImageData(1,1);
} catch(e) {
	if (typeof window !== 'undefined') {//Just in case it is nodejs
		window.ImageData = function(arr, width, height) {
			var canvas = document.createElement('canvas');
			var context = canvas.getContext('2d');
			var imgData = context.createImageData(width, height);
			imgData.data.set(arr);
			return imgData;
		}
	}
}

wdi.bppMask = [];
wdi.bppMask[1] = [128, 64, 32, 16, 8, 4, 2, 1];
wdi.bppMask[4] = [240, 15];
wdi.bppMask[8] = [255];

wdi.SeamlessIntegration = true;
wdi.Debug.debug = false;
wdi.exceptionHandling = true;
wdi.IntegrationBenchmarkEnabled = false; // MS Excel loading time benchmark
wdi.useWorkers = true;
wdi.logOperations = false;
