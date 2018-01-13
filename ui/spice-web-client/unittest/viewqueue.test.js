suite('ViewQueue', function() {
  setup(function(){
	wdi.Debug.debug = false; //disable debugging, it slows tests
  });

  suite('#getLength()', function() {
  	
	test('Should return 0 for empty queue', function() {
		var q = new wdi.ViewQueue();
		assert.strictEqual(q.getLength(), 0);
	});
  });
  
  suite('#push()', function() {
  	setup(function() {
  		this.q = new wdi.ViewQueue();
  	});
  	
  	test('Should be able to add elements as string', function() {
  		this.q.push('hello');
  		assert.strictEqual(this.q.getLength(), 5);
  	});
  	
  	test('Should be able to add arrays', function() {
  		this.q.push([1,2,3,4,5]);
  		assert.strictEqual(this.q.getLength(), 5);
  	});
  	
  	test('Should be able to push multiple arrays', function() {
  		this.q.push([1,2,3,4,5]);
  		this.q.push([1,2,3,4,5]);
  		assert.strictEqual(this.q.getLength(), 10);
  	});
  });
  
  suite('#shift()', function() {
  	setup(function() {
  		this.q = new wdi.ViewQueue();
  		this.q.push([1,2,3,4,5]);
  	});
  	
  	test('Should allways return array', function() {
  		var element = this.q.shift(1);
  		assert.isArray(element);
  	});
  	
  	test('Should read parts of the queue', function() {
  		var elements = this.q.shift(2);
  		assert.deepEqual(elements, [1,2]);
  	});
  	
  	test('Should read all the queue', function() {
  		var elements = this.q.shift(5);
  		assert.deepEqual(elements, [1,2,3,4,5]);
  	});
  	
  	test('Should empty all the queue', function() {
  		var elements = this.q.shift(5);
  		assert.strictEqual(this.q.getLength(), 0);
  	});
  	
  	test('Should empty parts of the queue', function() {
  		var elements = this.q.shift(2);
  		assert.strictEqual(this.q.getLength(), 3);
  	});
  });
  
  suite('#peek()', function() {
  	setup(function() {
  		this.q = new wdi.ViewQueue();
  		this.q.push([1,2,3,4,5]);
  	});
  	
  	test('Should read a single element', function() {
  		var element = this.q.peek(0, 1);
  		assert.deepEqual(element, [1]);
  	});
  	
  	test('Should read 3 elements of the queue', function() {
  		var elements = this.q.peek(1, 4);
  		assert.deepEqual(elements, [2,3,4]);
  	});
  	
  	test('Should read all the elements of the queue', function() {
  		var elements = this.q.peek(0);
  		assert.deepEqual(elements, [1,2,3,4,5]);
  	});
  	
  	test('Should be immutable', function() {
  		this.q.peek(1, 4);
  		assert.strictEqual(this.q.getLength(), 5);
  	});
  });
});
