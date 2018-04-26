suite('PacketController', function() {
	var sut, sizeDefiner, packetExtractor, toRestore;

	setup(function() {
		wdi.Debug.debug = false;
		sizeDefiner = new wdi.SizeDefiner();
		packetExtractor = new wdi.PacketExtractor({
			socketQ: new wdi.SocketQueue()
		});
		toRestore = [];
		sut = new wdi.PacketController({
			sizeDefiner: sizeDefiner,
			packetExtractor: packetExtractor
		});
	});

	teardown(function() {
		toRestore.forEach(function(item) {
			item.restore();
		});
	});

	suite('#getNextPacket()', function() {

		test('It fires chunkComplete event', function() {
			var called = false;
			var times = 0;
			var stub = sinon.stub(sizeDefiner, 'getSize');
			toRestore.push(stub);
			stub = sinon.stub(packetExtractor, 'getBytes', function(numBytes, callback, scope) {
				if (!times++)
					callback.call(scope, [0, 4, 3, 3, 5, 2, 4]);
			});
			toRestore.push(stub);
			sut.addListener('chunkComplete', function() {
				called = true;
			}, this);
			sut.getNextPacket();
			assert.isTrue(called, 'The chunkComplete event never fired');
		});

		test('It calls getStatus from SizeDefiner', function() {
			var times = 0;
			var stub = sinon.stub(sizeDefiner, 'getSize');
			toRestore.push(stub);
			stub = sinon.stub(packetExtractor, 'getBytes', function(numBytes, callback, scope) {
				if (!times++)
					callback.call(scope, [0, 4, 3, 3, 5, 2, 4]);
			});
			toRestore.push(stub);
			var mock = sinon.mock(sizeDefiner);
			var expectation = mock.expects('getStatus').once();
			toRestore.push(mock);
			sut.getNextPacket();
			expectation.verify();
		});

		test('It calls getSize from sizeDefiner', function() {
			var mock = sinon.mock(sizeDefiner);
			var expectation = mock.expects('getSize').once();

			toRestore.push(mock);
			var stub = sinon.stub(packetExtractor, 'getBytes');
			toRestore.push(stub);
			sut.getNextPacket();
			expectation.verify();
		});

		test('It calls getBytes from packetExtractor', function() {
			var mock = sinon.mock(packetExtractor);
			var expectation = mock.expects('getBytes').once();

			toRestore.push(mock);
			var stub = sinon.stub(sizeDefiner, 'getSize');
			toRestore.push(stub);
			sut.getNextPacket();
			expectation.verify();
		});

		test('It calls getSize from sizeDefiner with the last data acquired', function() {
			var header = [4, 0, 12, 0, 0, 0];
			var mock = sinon.mock(sizeDefiner);
			var expectation = mock.expects('getSize').once().withArgs(header);

			toRestore.push(mock);
			var stub = sinon.stub(packetExtractor, 'getBytes');
			toRestore.push(stub);
			sut.getNextPacket(header);
			expectation.verify();
		});
	});
});
