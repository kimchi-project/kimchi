suite('ConnectionControl', function() {
	var sut, socket, config;

	setup(function() {
		config = {
			'heartbeatTimeout': 4000,
			'protocol': 'ws',
			'host': 'localhost',
			'port': 8000,
			'busHost': 'localhost',
            'heartbeatToken': 'heartbeat'
		};
		socket = {
			connect: function() {},
			setOnMessageCallback: function() {},
			disconnect: function() {}
		};
		sut = new wdi.ConnectionControl({socket: socket});
	});

	test('connect should call socket connect with uri', function() {
		var expectedString = config['protocol'] + '://' + config['host'] + ':' + config['port'] +
            '/websockify/destInfoToken/' + config['heartbeatToken']+'/type/raw';
		var mock = sinon.mock(socket);
		var expectation = mock.expects('connect').once().withArgs(expectedString);
		sut.connect(config);
		expectation.verify();
	});

	test('connect should call socket setOnMessageCallback with callback', function() {
		var mock = sinon.mock(socket);
		var expectation = mock.expects('setOnMessageCallback').once().withArgs(sinon.match.func);
		sut.connect(config);
		expectation.verify();
	});

	test('disconnect should call socket disconnect', function() {
		var mock = sinon.mock(socket);
		var expectation = mock.expects('disconnect').once().withArgs();
		sut.disconnect();
		expectation.verify();
	});
});
