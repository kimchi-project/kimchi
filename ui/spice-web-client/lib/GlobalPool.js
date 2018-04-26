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

wdi.GlobalPool = {
    pools: {},
    retained: null,
    init: function() {
        this.retained = {};
        var self = this;
        this.pools['ViewQueue'] = new wdi.GenericObjectPool([function() {
            //factory
            return new wdi.ViewQueue();
        }, function(obj, index) {
            //reset
            obj.poolIndex = index; //update index at pool
            obj.setData([]); //reset the object
        }]);

        this.pools['RawSpiceMessage'] = new wdi.GenericObjectPool([function() {
            //factory
            return new wdi.RawSpiceMessage();
        }, function(obj, index) {
            //reset
            obj.poolIndex = index; //update index at pool
            obj.set(null, null, null); //reset the object
        }]);

		this.retained['Image'] = [];
        this.pools['Image'] = new wdi.GenericObjectPool([function() {
            //factory
            return new Image();
        }, function(obj, index) {
            //reset
            obj.poolIndex = index;
            obj.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';//Blank image 1x1 pixel (avoids console error GET null image)
            obj.onload = null;
			obj.keepAlive = false;
			self.retained['Image'][index] = obj;
        }]);


        this.retained['Canvas'] = [];
        this.pools['Canvas'] = new wdi.GenericObjectPool([function() {
            //factory
            return self.createCanvas();
        }, function(obj, index) {
            //reset
            obj.keepAlive = false;
            //obj.getContext('2d').clearRect(0, 0, obj.width, obj.height);
            obj.poolIndex = index;
            self.retained['Canvas'][index] = obj;
        }]);
    },

    createCanvas: function() {
    	return $('<canvas/>')[0];
    },

    create: function(objectType) {
        return this.pools[objectType].create();
    },

    discard: function(objectType, obj) {
        //check if its an autorelease pool
        if(this.retained.hasOwnProperty(objectType)) {
            delete this.retained[objectType][obj.poolIndex];
        }
        return this.pools[objectType].discard(obj.poolIndex);
    },

    cleanPool: function(objectType) {

        if(this.retained.hasOwnProperty(objectType)) {
             var pool = this.pools[objectType];

             for(var i in this.retained[objectType]) {
                 if(pool.discard(this.retained[objectType][i].poolIndex)) {
                     delete this.retained[objectType][i];
                 }
             }
        } else {
            wdi.Debug.error("GlobalPool: cleanPool called with invalid objectType: ",objectType);
        }
    }
}
