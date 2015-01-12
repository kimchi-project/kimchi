/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2015
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 * How to use:
 * $(".selector").gaugeFlat({
 *     value: 25,  // Value that you the gauge is going to show, varies from 0 to 100.
 *     color: "red" // Color showed, currently only "red", "yellow", "blue" and "purple" are supported.
 * });
 *
 * Set value:
 * $(".selector").gaugeFlat("value", <value>); // Replace <value> with the value that is going to be showed.
 *
 * Get value:
 * $(".selector").gaugeFlat("value"); // This returns the value of gauge.
 *
 */

(function( $ ) {

return $.widget( "kimchi.gaugeFlat", {
    version: "@VERSION",
    options: {
        max: 100,
        value: 0,
        color: "red"
    },

    min: 0,

    _create: function() {
        this.oldValue = this.options.value = this._constrainedValue();

        this.element
            .addClass( "ui-gauge-flat ui-widget ui-widget-content ui-corner-all" )
            .attr({
                role: "gaugeflat",
                "aria-valuemin": this.min
            });
        var color = this.options.color;
        if(color != "red" && color != "yellow" && color != "blue" && color != "purple") {
            color = "red";
        }

        this.valueDiv = $( "<div class='ui-gauge-flat-value " + color + " ui-widget-header ui-corner-left'></div>" )
            .appendTo( this.element );

        this._refreshValue();
    },

    _destroy: function() {
        this.element
            .removeClass( "ui-gauge-flat ui-widget ui-widget-content ui-corner-all" )
            .removeAttr( "role" )
            .removeAttr( "aria-valuemin" )
            .removeAttr( "aria-valuemax" )
            .removeAttr( "aria-valuenow" );

        this.valueDiv.remove();
    },

    value: function( newValue ) {
        if ( newValue === undefined ) {
            return this.options.value;
        }

        this.options.value = this._constrainedValue( newValue );
        this._refreshValue();
    },

    _constrainedValue: function( newValue ) {
        if ( newValue === undefined ) {
            newValue = this.options.value;
        }

        this.indeterminate = newValue === false;

        if ( typeof newValue !== "number" ) {
            newValue = 0;
        }

        return this.indeterminate ? false :
            Math.min( this.options.max, Math.max( this.min, newValue ) );
    },

    _setOptions: function( options ) {
        var value = options.value;
        delete options.value;

        this._super( options );

        this.options.value = this._constrainedValue( value );
        this._refreshValue();
    },

    _percentage: function() {
        return this.indeterminate ? 100 : 100 * ( this.options.value - this.min ) / ( this.options.max - this.min );
    },

    _refreshValue: function() {
        var value = this.options.value,
            percentage = this._percentage();

        this.valueDiv
            .toggle( this.indeterminate || value > this.min )
            .toggleClass( "ui-corner-right", value === this.options.max )
            .width( percentage.toFixed(0) + "%" );
    }
});

})(jQuery);
