suite('PacketExtractor', function() {
	var sut, socketQ;

	setup(function() {
		wdi.Debug.debug= false;
		socketQ = new wdi.SocketQueue();
		sut = new wdi.PacketExtractor({socketQ: socketQ});
	});

	suite('#getBytes()', function() {
		test('Check that callback is called once', function() {
			var size = 50, data = [], called = false;
			data.length = size;
			socketQ.rQ.setData(data);
			sut.getBytes(size, function(bytes) {
				called = true;
			});
			assert.isTrue(called, 'The callback is never called');
		});
		
		test('Check queue has enough bytes and return them', function() {
			var size = 50, data = [];
			data.length = size;
			socketQ.rQ.setData(data);
			sut.getBytes(size, function(bytes) {
				assert.equal(size, bytes.length, 'The gathered data it is not the expected size');
			});
		});

		test('Check callback is not called when not enough data', function() {
			var size = 50, data = [], called = false;
			data.length = 40;
			socketQ.rQ.setData(data);
			sut.getBytes(size, function(bytes) {
				called = true;
			});
			assert.isFalse(called, 'The callback is unexpectedly called');
		});

		test('Check callback is called when enough data is received', function() {
			var size = 50, data = [], called = false;
			data.length = 40;
			socketQ.rQ.setData(data);
			sut.getBytes(size, function(bytes) {
				called = true;
			});
			data.length = size;
			socketQ.rQ.setData(data);
			socketQ.fire('message');
			assert.isTrue(called, 'The callback is never called');
		});

		test('Check that scope passed is used', function() {
			var size = 50, data = [], called = false, callbackScope = {
				scopeCheck: function() {
					called = true;
				}
			};
			data.length = size;
			socketQ.rQ.setData(data);
			sut.getBytes(size, function(bytes) {
				this.scopeCheck();
			}, callbackScope);
			assert.isTrue(called, 'The callback is never called');
		});

		test.skip('Check callback is called with the expected size after multiple socketQ messages', function() {
			var size = 50, data = [], numBytes = 0;
			data.length = 30;
			socketQ.rQ.setData(data);
			sut.getBytes(size, function(bytes) {
				numBytes = bytes.length;
			});
			data = [];
			data.length = 10;
			socketQ.rQ.push(data);
			socketQ.fire('message');
			data = [];
			data.length = 10;
			socketQ.rQ.push(data);
			socketQ.fire('message');
			assert.equal(numBytes, size, 'The size of the received data is not the expected one');
		});

		test('When called without a callback it doesn\'t crash', function () {
			var size = 50, data = [];
			data.length = size;
			socketQ.rQ.setData(data);
			socketQ.fire('message');
		});
	});
});
