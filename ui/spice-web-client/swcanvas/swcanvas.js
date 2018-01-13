var SWCanvas = function(canvas) {
    this.arr = new ArrayBuffer(canvas.width*canvas.height*4);
    this.arr32 = new Uint32Array(this.arr);
    this.arr8 = new Uint8ClampedArray(this.arr);
    this.canvas = canvas;
    this.width = this.canvas.width;
    this.height = this.canvas.height;
};

SWCanvas.prototype.putImageData = function(imgData, x, y) {
    var srcArr = imgData.data.buffer;
    var w = imgData.width;
    var pos = imgData.height;
    var tmp;
    var canvasWidth = this.width;
    var tmpArr;
    while(pos--) {
        tmp = (y+pos)*canvasWidth+x;
        tmpArr = new Uint32Array(srcArr, w*pos*4, w);
        this.arr32.set(tmpArr, tmp);
    }
};

SWCanvas.prototype.getImageData = function(x, y, width, height) {
    var result = new Uint32Array(width*height);
    var arr = this.arr32;
    var pos=height;
    var tmp;
    var canvasWidth = this.width;
    while(pos--) {
        tmp = (y+pos)*canvasWidth+x;
        var line = arr.subarray(tmp,tmp+width);
        result.set(line, width*pos);
    }
    return new ImageData(new Uint8ClampedArray(result.buffer), width, height);
};

SWCanvas.prototype.fillRect = function(r, g, b, x, y, width, height) {
    var line = new Uint32Array(width);
    var color32 = 4278190080 | r  | g << 8 | b << 16;
    var canvasWidth = this.width;
    var w = width;
    while(w--) {
        line[w] = color32;
    }
    var tmp;
    while(height--) {
        tmp = (y+height)*canvasWidth+x;
        this.arr32.set(line, tmp);
    }
}

//copy from canvas to arr
SWCanvas.prototype.flushBack = function() {
    var arr8 = this.canvas.getContext('2d').getImageData(0, 0, this.width, this.height).data;
    this.arr8.set(arr8);
};

//copy from arr to canvas
SWCanvas.prototype.flush = function() {
    var imgData = new ImageData(this.arr8, this.width, this.height);
    this.canvas.getContext('2d').putImageData(imgData,0, 0);
};