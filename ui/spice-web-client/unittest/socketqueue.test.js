suite('SocketQueue', function() {
	setup(function(){
		wdi.Debug.debug = false; //disable debugging, it slows tests
	});
	
	suite('#connect()', function() {
		setup(function() {
			this.socket = new wdi.Socket();
			this.mock = sinon.mock(this.socket);
			this.expectation = this.mock.expects('connect').once();
			this.socketQ = new wdi.SocketQueue({socket: this.socket});
		});
		
		test('Should call method connect from socket', function() {
			this.socketQ.connect('ws://localhost');
			this.expectation.verify();
		});
		
		teardown(function() {
			this.mock.restore();
		});
	});
	
	suite('#disconnect()', function() {
		setup(function() {
			this.socket = new wdi.Socket();
			this.mock = sinon.mock(this.socket);
			this.expectation = this.mock.expects('disconnect').once();
			this.socketQ = new wdi.SocketQueue({socket: this.socket});
		});
		
		test('Should call method disconnect from socket', function() {
			this.socketQ.disconnect();
			this.expectation.verify();
		});
		
		teardown(function() {
			this.mock.restore();
		});
	});
	
	suite('#getStatus()', function() {
		setup(function() {
			this.socket = new wdi.Socket();
			this.mock = sinon.mock(this.socket);
			this.expectation = this.mock.expects('getStatus').once();
			this.socketQ = new wdi.SocketQueue({socket:this.socket});
		});
		
		test('Should call method getStatus from socket', function() {
			this.socketQ.getStatus();
			this.expectation.verify();
		});
		
		teardown(function() {
			this.mock.restore();
		});
	});
	
	suite('#send()', function() {
		setup(function() {
			this.queue = new wdi.Queue();
			this.mock = sinon.mock(this.queue);
			this.expectation = this.mock.expects('push').once();
			this.socketQ = new wdi.SocketQueue({sQ:this.queue});
			this.socketQ.connect('ws://localhost');
		});
		
		test('Should call send queue push on send(data, false)', function() {
			this.socketQ.send([0x23], false);
			this.expectation.verify();
		});
		
		teardown(function() {
			this.mock.restore();
		});
	});
	
	suite('#flush()', function() {
		setup(function() {
			this.socket = new wdi.Socket();
			this.mock = sinon.mock(this.socket);
			this.expectation = this.mock.expects('send').once();
			this.socketQ = new wdi.SocketQueue({socket: this.socket});
			this.socketQ.connect('ws://localhost');
		});
		
		test('Should call socket send', function() {
			this.socketQ.flush();
			this.expectation.verify();
		});
		
		teardown(function() {
			this.mock.restore();
		});
	});
});
