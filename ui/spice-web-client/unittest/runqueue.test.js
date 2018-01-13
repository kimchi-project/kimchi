suite('RunQueue', function() {
	setup(function(){
		wdi.Debug.debug = false; //disable debugging, it slows tests
	});
	
	suite('#getTasksLength()', function() {
		test('Should return 0 for empty runqueue', function() {
			this.rQ = new wdi.RunQueue();
			assert.strictEqual(this.rQ.getTasksLength(), 0);
		});
	});
	
	suite('#add()', function() {
		setup(function() {
			this.rQ = new wdi.RunQueue();
		});
		
		test('Should add single tasks', function() {
			this.rQ.add(function(){}, this);
			assert.equal(this.rQ.getTasksLength(), 1);
		});
		
		test('Should add two tasks', function() {
			this.rQ.add(function(){}, this);
			this.rQ.add(function(){}, this);
			assert.equal(this.rQ.getTasksLength(), 2);
		});
	});
	
	suite('#clear()', function() {
		setup(function() {
			this.rQ = new wdi.RunQueue();
			this.rQ.add(function(){}, this);
			this.rQ.add(function(){}, this);
		});
		
		test('Should clear all tasks', function() {
			this.rQ.clear();
			assert.equal(this.rQ.getTasksLength(), 0);
		});
	});
	
	suite('#process()', function() {
		setup(function() {
			this.rQ = new wdi.RunQueue();
		});
		
		test('Should call single tasks', function() {
			var object = {method: function(proxy){proxy.end();}};
			var spy = sinon.spy(object, 'method');
			this.rQ.add(object.method, object);
			this.rQ.process();
			assert(spy.calledOnce);
		});
		
		test('Should keep scope', function() {
			var object = {method: function(proxy){proxy.end();}};
			var spy = sinon.spy(object, 'method');
			this.rQ.add(object.method, object);
			this.rQ.process();
			assert(spy.calledOn(object));
		});
		
		test('Should call two syncronous tasks', function() {
			var object = {method: function(proxy){proxy.end()}};
			var spy = sinon.spy(object, 'method');
			this.rQ.add(object.method, object);
			this.rQ.add(object.method, object);
			this.rQ.process();
			assert(spy.calledTwice);
		});
		
		test('Should call asynchronous task', function(done) {
			var object = {method: function(proxy){
				setTimeout(function() {
					proxy.end();
					done();
				}, 100);
			}};
			this.rQ.add(object.method, object);
			this.rQ.process();
		});
		
		test('Should return nothing if there are no tasks', function() {
			var runqueue = this.rQ.process();
			assert.isUndefined(runqueue);
		});

		test('Should not run process if runqueue is running', function(done) {
			var object = {method: function(proxy){
				setTimeout(function() {
					done();
				}, 100);
			}};
			var object2 = {method: function(proxy){proxy.end()}};
			var spy = sinon.spy(object2, 'method');
			this.rQ.add(object.method, object);
			this.rQ.add(object2.method, object2);
			this.rQ.process();
			this.rQ.process();
			assert(!spy.called);
		});
	});
});
