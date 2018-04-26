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
                 pool.discard(this.retained[objectType][i].poolIndex);
             }
             this.retained[objectType] = [];
        } else {
            wdi.Debug.error("GlobalPool: cleanPool called with invalid objectType: ",objectType);
        }
    }
}
