/*
 * Project Wok
 *
 * Copyright IBM, Corp. 2015
 *
 * Code derived from Project Kimchi
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

$(function(){
$.widget("wok.line", {
    options: {
        xShift: true,
        minVal: 0,
        maxVal: 100,
        datasets: []
    },
    _create: function() {
        this._build();
    },
    _build: function() {
        this.element.empty();
        var maxX = this.element.width();
        var maxY = this.element.height();
        var svg = "<svg class='line' width='"+maxX+"' height='"+maxY+"'>";
        svg += "<line x1='0' y1='0' x2='"+maxX+"' y2='0' class='max'/>";
        svg += "<line x1='0' y1='"+maxY+"' x2='"+maxX+"' y2='"+maxY+"' class='min'/>";
        for(var i=0;i<this.options.datasets.length;i++){
            var data = this.options.datasets[i].data;
            var points = "";
            for(var j=0;j<data.length;j++){
               if(data[j]){
                   var xVal = maxX/(data.length-1)*j;
                   var yVal = (this.options.maxVal-data[j])*maxY/this.options.maxVal;
                   points += xVal+","+yVal+" ";
               }
            }
            svg += "<polyline points='"+points+"' style='stroke:"+this.options.datasets[i].color+";'/>";
        }
        svg += "</svg>";
        this.element.append(svg);
    },
    addData: function(values){
        if(values.length<this.options.datasets.length) return;
        for(var i=0;i<this.options.datasets.length;i++){
            this.options.datasets[i].data.push(values[i]);
            if(this.options.xShift) this.options.datasets[i].data.splice(0,1);
        }
        this._build();
    },
    removeData: function(){
        for(var i=0;i<this.options.datasets.length;i++){
            var data = this.options.datasets[i].data;
            data.splice(0,1);
            if(this.options.xShift) data.push(null);
        }
        this._build();
    },
    _destroy: function() {
        this.element.empty();
    }
});
});
