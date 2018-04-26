/*
Generic Object Pooling from:
https://github.com/miohtama/objectpool.js/
MIT License

Copyright (C) 2013 Mikko Ohtamaa

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Version: 65c7399c30a3f6f3593bb4bfca3d9cde65675b84 (git commit)
 */


wdi.GenericObjectPool = $.spcExtend(wdi.EventObject.prototype, {

    /** How fast we grow */
    expandFactor : 0.2,

    /** Minimum number of items we grow */
    expandMinUnits : 16,

    elems : null,

    /** List of discarded element indexes in our this.elems pool */
    freeElems : null,

    allocator: null,
    resetor: null,

    /**
     * Generic object pool for Javascript.
     *
     * @param {Function} allocator return new empty elements
     *
     * @param {Function} resetor resetor(obj, index) is called on all new elements when they are (re)allocated from pool.
     *                   This is mostly useful for making object to track its own pool index.
     */
    init : function(params) {
        var allocator = params[0];
        var resetor = params[1];
        // Start with one element
        this.allocator = allocator;
        this.resetor = resetor;
        // Set initial state of 1 object
        this.elems = [this.allocator()];
        this.freeElems = [0];
    },

    /**
     * @return {[type]} [description]
     */
    create : function() {

        if(!this.freeElems.length) {
            this.expand();
        }

        // See if we have any allocated elements to reuse
        var index = this.freeElems.pop();
        var elem = this.elems[index];
        this.resetor(elem, index);
        return elem;

    },

    /**
     * How many allocated units we have
     *
     * @type {Number}
     */
    length : function() {
        return this.elems.length - this.freeElems.length;
    },

    /**
     * Make pool bigger by the default growth parameters.
     *
     */
    expand : function() {

        var oldSize = this.elems.length;

        var growth = Math.ceil(this.elems.length * this.expandFactor);

        if(growth < this.expandMinUnits) {
            growth = this.expandMinUnits;
        }

        this.elems.length = this.elems.length + growth;

        for(var i=oldSize; i<this.elems.length; i++) {
            this.elems[i] = this.allocator();
            this.freeElems.push(i);
        }
    },

    /**
     * Deallocate object at index n
     *
     * @param  {Number} n
     * @return {Object} discarded object
     */
    discard : function(n) {

        // Cannot double deallocate
        if(this.freeElems.indexOf(n) >= 0) {
            throw "GeneircObjectPool: Double-free for element index: "+n;
        }

        if(this.elems[n].keepAlive) {
            return false;
        }

        this.freeElems.push(n);
        return true;
    },

    /**
     * Return object at pool index n
     */
    get : function(n) {
        return this.elems[n];
    }
});
