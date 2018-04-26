suite('EventObject', function() {
	setup(function() {
		wdi.Debug.debug = false; //disable debugging, it slows tests
	});
	
	suite('#addListener()', function() {
		setup(function () {
			this.eo = new wdi.EventObject();
		});
		
		test('Should add event to list', function() {
			this.eo.addListener('test', function(){});
			assert.strictEqual(this.eo.getListenersLength("test"), 1);
		});
		
		test('Should add two event to list', function() {
			this.eo.addListener('test', function(){});
			this.eo.addListener('test', function(){});
			assert.strictEqual(this.eo.getListenersLength("test"), 2);
		});
	});
	
	suite('#removeEvent()', function() {
		setup(function() {
			this.eo = new wdi.EventObject();
			this.eo.addListener('test', function() {});
			this.eo.addListener('test', function() {});
			this.eo.addListener('test2', function() {});
		});
		
		test('Should remove correct event', function() {
			this.eo.removeEvent('test');
			assert.notProperty(this.eo.eyeEvents, 'test');
		});
	});
	
	suite('#clearEvents()', function() {
		setup(function() {
			this.eo = new wdi.EventObject();
			this.eo.addListener('test', function(){});
			this.eo.addListener('test', function(){});
			this.eo.addListener('test', function(){});
		});
		
		test('Should remove all events and listeners', function() {
			this.eo.clearEvents();
			assert.strictEqual(this.eo.getListenersLength('test'), 0);
		});
	});
	
	suite('#fire()', function() {
		setup(function() {
			this.eo = new wdi.EventObject();
			this.callback = sinon.spy();
			this.eo.addListener('test', this.callback, this);
			this.eo.addListener('test', this.callback, this);
		});
		
		test('Should trigger selected event', function() {
			this.eo.fire('test');
			assert(this.callback.calledTwice);
		});
		
		test('Should keep scope', function() {
			this.eo.fire('test');
			assert(this.callback.calledOn(this));
		});
	});
});
