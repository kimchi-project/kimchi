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

Uint8Array.prototype.toJSArray = function() {
    if(this.length == 1) {
        return [this[0]];
    }

    var len = this.length;
    var arr = new Array(len);

    for(var i=0;i<len;i++) {
        arr[i] = this[i];
    }
    return arr;
}

wdi.FixedQueue = $.spcExtend(wdi.DomainObject, {
	q: null,
	size: 1024*1024*10,
    grow: 1024*1024*10,
	woffset: 0,
    roffset: 0,

	init: function(c) {
		this.q = new Uint8Array(this.size);
	},

    setData: function(q) {
        this.woffset = q.length;
        this.roffset = 0;
        this.q.set(q);
    },

	shift: function(elements) {
        if(this.roffset + elements > this.woffset) {
            throw "Not enough queue to read";
        }
        var toreturn = this.q.subarray(this.roffset, this.roffset + elements);
        this.roffset = this.roffset + elements;
        if(this.woffset == this.roffset) {
            this.woffset = 0;
            this.roffset = 0;
        }
		return toreturn;
	},

	push: function(collection) {
        if(this.woffset + collection.byteLength > this.size) {
            //we need to make the queue bigger...
            var oldq = this.q;
            this.size += this.grow;
            this.q = new Uint8Array(this.size);
            this.q.set(oldq);
        }
        this.q.set(collection, this.woffset);
        this.woffset += collection.byteLength;
	},

	getLength: function() {
		return this.woffset-this.roffset;
	}
});


wdi.Queue = $.spcExtend(wdi.DomainObject, {
	q: null,
    raw: false,
	
	init: function(c) {
        if(c.raw) {
            this.raw = c.raw;
        }
		this.q = new Uint8Array(0);
	},
	
	getData: function() {
		return this.toJSArray(this.q);
	},
	
	setData: function(q) {
        this.q = new Uint8Array(q.length);
		this.q.set(q);
	},
	
	shift: function() {
		var elements = arguments[0] || this.getLength();

		if (elements === this.q.length) {
			var toreturn = this.q;
			this.q = new Uint8Array(0);
		} else {
			var toreturn = this.q.subarray(0, elements);
			this.q = this.q.subarray(elements);
		}

        return this.toJSArray(toreturn)
	},
	
	peek: function(begin, end) {
        var tmp = null;
        if(begin == 0 && !end) {
            tmp = this.q; //read the entire queue
        } else {
            tmp = this.q.subarray(begin, end);
        }
		return this.toJSArray(tmp);
	},
	
	push: function(collection) {
		if (typeof collection == 'string') {
            var len = collection.length;
            var newq = new Uint8Array(this.q.length+len);
            newq.set(this.q);
            for(var i=0;i<len;i++) {
                newq[i+this.q.length] = collection[i];
            }
            this.q = newq;
		} else {
			if(this.getLength() === 0) {
				this.q = new Uint8Array(collection.length);
                this.q.set(collection);
			} else {
                var newq = new Uint8Array(collection.length+this.q.length);
                newq.set(this.q);
                newq.set(collection, this.q.length);
				this.q = newq;
			}
		}
	},
	
	getLength: function() {
		return this.q.length;
	},

    toJSArray: function(data) {
        if(this.raw) {
            return data;
        }

        return data.toJSArray();
    }
});

wdi.ViewQueue = $.spcExtend(wdi.DomainObject, {
	q: null,
	at: null,
	
	init: function() {
		this.q = new Uint8Array();
		this.at = 0;
	},
	
	getData: function() {
		return this.toJSArray(this.q.subarray(this.at));
	},

    getDataOffset: function(pos) {
   		return this.toJSArray(this.q.subarray(pos));
   	},

    getRawData: function() {
   		return this.q.subarray(this.at);
   	},

    getRawDataOffset: function(pos) {
        return this.q.subarray(pos);
    },
	
	setData: function(q) {
		this.q = new Uint8Array(q.length);
        this.q.set(q);
		this.at = 0;
	},
	
	shift: function(length) {
		var elements = length || this.getLength();
		if(elements > this.getLength()) {
			elements = this.getLength();
		}
		var ret = this.q.subarray(0+this.at, elements+this.at);
		this.at += elements;
		return this.toJSArray(ret);
	},

    eatBytes: function(bytes) {
        this.at += bytes;
    },

    getByte: function(pos) {
        return this.q[pos+this.at];
    },
	
	peek: function(begin, end) {
        var tmp = null;
        if(begin == 0 && !end) {
            tmp = this.q; //read the entire queue
        } else {
            if(end) {
                end += this.at;
            }
            tmp = this.q.subarray(begin+this.at, end);
        }
		return this.toJSArray(tmp);
	},
	
    push: function(collection) {
   		if (typeof collection == 'string') {
               var len = collection.length;
               var newq = new Uint8Array(this.q.length+len);
               newq.set(this.q);
               for(var i=0;i<len;i++) {
                   newq[i+this.q.length] = collection[i];
               }
               this.q = newq;
   		} else {
   			if(this.getLength() === 0) {
   				this.q = new Uint8Array(collection.length);
                   this.q.set(collection);
   			} else {
               var newq = new Uint8Array(collection.length+this.q.length);
               newq.set(this.q);
               newq.set(collection, this.q.length);
   				this.q = newq;
   			}
   		}
   	},
	
	getLength: function() {
		return this.q.length-this.at;
	},

	getPosition: function() {
		return this.at;
	},
    toJSArray: function(data) {
        if(data.length == 1) {
            return [data[0]];
        }
        return data.toJSArray();
    }
});

