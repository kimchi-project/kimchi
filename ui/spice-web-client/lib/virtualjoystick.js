var VirtualJoystick	= function(opts)
{
	opts			= opts			|| {};
	this._container		= opts.container	|| document.body;
	this._stickEl		= opts.stickElement	|| this._buildJoystickStick();
	this._baseEl		= opts.baseElement	|| this._buildJoystickBase();
	this._mouseLeft = opts.mouseLeft || this._buildJoystickButton();
	this._mouseSupport	= 'mouseSupport' in opts? opts.mouseSupport	: false;
	this._range		= opts.range		|| 60;
	
	this._timer = null;
	
	this._callback	= 'callback' in opts? opts.callback	: false;
	this._callbackcontext = 'callbackcontext' in opts? opts.callbackcontext: this;
	this._callbackButton = 'callbackbutton' in opts? opts.callbackbutton : false;
	this._referenceItem = opts.referenceItem;

	this._container.style.position	= "relative";

	this._container.appendChild(this._baseEl);
	this._container.appendChild(this._mouseLeft);
	
	this._baseEl.style.position	= "absolute"
	this._baseEl.style.display	= "block";
	
	this._mouseLeft.style.position	= "absolute"
	this._mouseLeft.style.display	= "block";
		
	//calculate positions
	var jcnt = $(this._referenceItem);
	var baseTop = jcnt.height()-jcnt.offset().top-130;
	var baseLeft = 20;
	var baseRight = 20;
	this._baseEl.style.top = baseTop+'px';
	this._baseEl.style.left = baseLeft+'px';
	
	this._container.appendChild(this._stickEl);
	this._stickEl.style.position	= "absolute"
	this._stickEl.style.display	= "none";
	
	this._mouseLeft.style.top = baseTop+20+'px';
	this._mouseLeft.style.right = baseRight+'px';
	
	this._pressed	= false;
	this._baseX	= 0;
	this._baseY	= 0;
	this._stickX	= 0;
	this._stickY	= 0;

	__bind		= function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
	this._$onTouchStart	= __bind(this._onTouchStart	, this);
	this._$onTouchEnd	= __bind(this._onTouchEnd	, this);
	this._$onTouchMove	= __bind(this._onTouchMove	, this);
	this._$onTouchStartButton = __bind(this._onTouchStartButton, this);
	this._$onTouchEndButton = __bind(this._onTouchEndButton, this);
	this._baseEl.addEventListener( 'touchstart'	, this._$onTouchStart	, false );
	this._mouseLeft.addEventListener( 'touchstart'	, this._$onTouchStartButton	, false );
	this._mouseLeft.addEventListener( 'touchend'	, this._$onTouchEndButton	, false );
	this._container.addEventListener( 'touchend'	, this._$onTouchEnd	, false );
	this._container.addEventListener( 'touchmove'	, this._$onTouchMove	, false );
	if( this._mouseSupport ){
		this._$onMouseDown	= __bind(this._onMouseDown	, this);
		this._$onMouseUp	= __bind(this._onMouseUp	, this);
		this._$onMouseMove	= __bind(this._onMouseMove	, this);
		this._$onMouseDownButton = __bind(this._onMouseDownButton, this);
		this._$onMouseUpButton = __bind(this._onMouseUpButton, this);
		this._baseEl.addEventListener( 'mousedown'	, this._$onMouseDown	, false );
		this._container.addEventListener( 'mouseup'	, this._$onMouseUp	, false );
		this._mouseLeft.addEventListener( 'mousedown'	, this._$onTouchStartButton	, false );
		this._mouseLeft.addEventListener( 'mouseup'	, this._$onTouchEndButton	, false );
		this._container.addEventListener( 'mousemove'	, this._$onMouseMove	, false );
	}
}

VirtualJoystick.prototype.destroy	= function()
{
	this._container.removeChild(this._baseEl);
	this._container.removeChild(this._stickEl);
	
	this._mouseLeft.removeEventListener( 'touchstart'	, this._$onTouchStartButton	, false );
	this._mouseLeft.removeEventListener( 'touchend'		, this._$onTouchEndButton	, false );
	this._container.removeChild(this._mouseLeft);

	this._container.removeEventListener( 'touchstart'	, this._$onTouchStart	, false );
	this._container.removeEventListener( 'touchend'		, this._$onTouchEnd	, false );
	this._container.removeEventListener( 'touchmove'	, this._$onTouchMove	, false );
	if( this._mouseSupport ){
		this._container.removeEventListener( 'mouseup'		, this._$onMouseUp	, false );
		this._container.removeEventListener( 'mousedown'	, this._$onMouseDown	, false );
		this._container.removeEventListener( 'mousemove'	, this._$onMouseMove	, false );
	}
}

/**
 * @returns {Boolean} true if touchscreen is currently available, false otherwise
*/
VirtualJoystick.touchScreenAvailable	= function()
{
	return 'createTouch' in document ? true : false;
}

//////////////////////////////////////////////////////////////////////////////////
//										//
//////////////////////////////////////////////////////////////////////////////////

VirtualJoystick.prototype.deltaX	= function(){ return this._stickX - this._baseX;	}
VirtualJoystick.prototype.deltaY	= function(){ return this._stickY - this._baseY;	}

VirtualJoystick.prototype.up	= function(){
	if( this._pressed === false )	return false;
	var deltaX	= this.deltaX();
	var deltaY	= this.deltaY();
	if( deltaY >= 0 )	return false;
	if( Math.abs(deltaY) < this._range && Math.abs(deltaY) < Math.abs(deltaX) ){
		return false;
	}
	return true;
}
VirtualJoystick.prototype.down	= function(){
	if( this._pressed === false )	return false;
	var deltaX	= this.deltaX();
	var deltaY	= this.deltaY();
	if( deltaY <= 0 )	return false;
	if( Math.abs(deltaY) < this._range && Math.abs(deltaY) < Math.abs(deltaX) ){
		return false;
	}
	return true;	
}
VirtualJoystick.prototype.right	= function(){
	if( this._pressed === false )	return false;
	var deltaX	= this.deltaX();
	var deltaY	= this.deltaY();
	if( deltaX <= 0 )	return false;
	if( Math.abs(deltaX) < this._range && Math.abs(deltaY) > Math.abs(deltaX) ){
		return false;
	}
	return true;	
}
VirtualJoystick.prototype.left	= function(){
	if( this._pressed === false )	return false;
	var deltaX	= this.deltaX();
	var deltaY	= this.deltaY();
	if( deltaX >= 0 )	return false;
	if( Math.abs(deltaX) < this._range && Math.abs(deltaY) > Math.abs(deltaX) ){
		return false;
	}
	return true;	
}

//////////////////////////////////////////////////////////////////////////////////
//										//
//////////////////////////////////////////////////////////////////////////////////

VirtualJoystick.prototype._onUp	= function()
{
	this._pressed	= false; 
	this._stickEl.style.display	= "none";
	//this._baseEl.style.display	= "none";
	
	this._baseX	= this._baseY	= 0;
	this._stickX	= this._stickY	= 0;
	this._eraseInterval();
}

VirtualJoystick.prototype._onDown	= function(x, y)
{
	this._pressed	= true; 
	this._stickX	= x;
	this._stickY	= y;

	this._stickEl.style.display	= "";
	this._stickEl.style.left	= (this._stickX - this._stickEl.width /2)+"px";
	this._stickEl.style.top		= (this._stickY - this._stickEl.height/2)+"px";
	this._startInterval();

}

VirtualJoystick.prototype._onMove	= function(x, y)
{
	if( this._pressed === true ){
		this._stickX	= x;
		this._stickY	= y;
		this._stickEl.style.left	= (x - this._stickEl.width /2)+"px";
		this._stickEl.style.top		= (y - this._stickEl.height/2)+"px";
		this._startInterval();
	}
}

VirtualJoystick.prototype._startInterval = function(x, y) {
	this._eraseInterval();
	var centerXBase = $(this._baseEl).offset().left + ($(this._baseEl).width()/2);
	var centerXStick = $(this._stickEl).offset().left + ($(this._stickEl).width()/2);
	this.offsetX = parseInt((centerXStick - centerXBase) / 5);
	
	//////
	
	var centerYBase = $(this._baseEl).offset().top + ($(this._baseEl).height()/2);
	var centerYStick = $(this._stickEl).offset().top + ($(this._stickEl).height()/2);
	
	this.offsetY = parseInt((centerYStick - centerYBase) / 5);
	
	if(this.offsetX > 15) {
		this.offsetX = 15;
	}
	
	if(this.offsetY > 15) {
		this.offsetY = 15;
	}
	//calculate movements from offsets
	
	var self = this;
	this._timer = setInterval(function() {
		if(self._callback) {
			self._callback.call(self._callbackcontext, [self.offsetX, self.offsetY]);
		}
	}, 10);
	
}

VirtualJoystick.prototype._eraseInterval = function() {
	if(this._timer) {
		clearTimeout(this._timer);
		this._timer = null;
	}
}

//////////////////////////////////////////////////////////////////////////////////
//		bind touch events (and mouse events for debug)			//
//////////////////////////////////////////////////////////////////////////////////

VirtualJoystick.prototype._onMouseUp	= function(event)
{
	return this._onUp();
}

VirtualJoystick.prototype._onMouseDown	= function(event)
{
	var x	= event.pageX;
	var y	= event.pageY;
	return this._onDown(x, y);
}

VirtualJoystick.prototype._onMouseMove	= function(event)
{
	var x	= event.pageX;
	var y	= event.pageY;
	return this._onMove(x, y);
}

VirtualJoystick.prototype._onTouchStart	= function(event)
{
	if( event.touches.length != 1 )	return;

	event.preventDefault();

	var x	= event.touches[ 0 ].pageX;
	var y	= event.touches[ 0 ].pageY;
	return this._onDown(x, y)
}

VirtualJoystick.prototype._onTouchEnd	= function(event)
{
//??????
// no preventDefault to get click event on ios
event.preventDefault();

	return this._onUp()
}

VirtualJoystick.prototype._onTouchMove	= function(event)
{
	if(event.touches && event.touches.length != 1 )	return;

	event.preventDefault();

	var x	= event.touches[ 0 ].pageX;
	var y	= event.touches[ 0 ].pageY;
	return this._onMove(x, y)
}

VirtualJoystick.prototype._onTouchStartButton	= function(event)
{
	if( event.touches && event.touches.length != 1 )	return;

	event.preventDefault();
	this._callbackButton.call(this._callbackcontext, ['down']);
}

VirtualJoystick.prototype._onTouchEndButton	= function(event)
{
//??????
// no preventDefault to get click event on ios
event.preventDefault();
	this._callbackButton.call(this._callbackcontext, ['up']);
}
//////////////////////////////////////////////////////////////////////////////////
//		build default stickEl and baseEl				//
//////////////////////////////////////////////////////////////////////////////////

VirtualJoystick.prototype._buildJoystickBase	= function()
{
	var canvas	= document.createElement( 'canvas' );
	canvas.style.zIndex = 2;
	canvas.width	= 126;
	canvas.height	= 126;
	
	var ctx		= canvas.getContext('2d');
	ctx.beginPath(); 
	ctx.strokeStyle = "cyan"; 
	ctx.lineWidth	= 6; 
	ctx.arc( canvas.width/2, canvas.width/2, 40, 0, Math.PI*2, true); 
	ctx.stroke();	

	ctx.beginPath(); 
	ctx.strokeStyle	= "cyan"; 
	ctx.lineWidth	= 2; 
	ctx.arc( canvas.width/2, canvas.width/2, 60, 0, Math.PI*2, true); 
	ctx.stroke();
	
	return canvas;
}

VirtualJoystick.prototype._buildJoystickStick	= function()
{
	var canvas	= document.createElement( 'canvas' );
	canvas.style.zIndex = 2;
	canvas.width	= 86;
	canvas.height	= 86;
	var ctx		= canvas.getContext('2d');
	ctx.beginPath(); 
	ctx.strokeStyle	= "cyan"; 
	ctx.lineWidth	= 6; 
	ctx.arc( canvas.width/2, canvas.width/2, 40, 0, Math.PI*2, true); 
	ctx.stroke();
	return canvas;
}

VirtualJoystick.prototype._buildJoystickButton	= function()
{
	var canvas	= document.createElement( 'canvas' );
	canvas.style.zIndex = 2;
	canvas.width	= 86;
	canvas.height	= 86;
	var ctx		= canvas.getContext('2d');
	ctx.beginPath(); 
	ctx.strokeStyle	= "green"; 
	ctx.lineWidth	= 6; 
	ctx.arc( canvas.width/2, canvas.width/2, 40, 0, Math.PI*2, true); 
	ctx.stroke();
	return canvas;
}
