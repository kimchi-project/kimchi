suite('SpiceConnection', function() {
	setup(function(){
		wdi.Debug.debug = false; //disable debugging, it slows tests
	});
	
	suite('#connect()', function() {
		setup(function() {
			this.mainChannel = new wdi.SpiceChannel();
			this.mock = sinon.mock(this.mainChannel);
			this.sut = this.spcConnect = new wdi.SpiceConnection({
				mainChannel:this.mainChannel,
				connectionControl: {
					connect: function() {},
					addListener: function() {}
				}
			});
			
		});

		test('Should call connect on the main channel', function() {
			this.expectation = this.mock.expects('connect').once();
			this.spcConnect.connect('localhost', 8000);
			this.mock.verify();
		});
		
		test('Should call connect on the main channel with the correct arguments', function() {
			this.expectation = this.mock.expects('connect').once().withArgs({host:'localhost', port:8000}, wdi.SpiceVars.SPICE_CHANNEL_MAIN);
			this.spcConnect.connect({host:'localhost', port:8000});
			this.mock.verify();
		});

		test('Should call connect on the connectionControl with the correct arguments', function() {
			var connectionInfo = {
				connectionControl: true
			};
			this.expectation = this.mock.expects('connect').once().withArgs(connectionInfo);
			this.spcConnect.connect(connectionInfo);
			this.mock.verify();
		});

		test.skip('When a channel fire a channelConnected message should fire channelConnected message with channel', function() {
			var channel;
			this.sut.addListener('channelConnected', function (e) {
				channel = e[1];
			}, this);

			this.mainChannel.fire('channelConnected');

			assert.equal(channel, wdi.SpiceVars.SPICE_CHANNEL_MAIN);
		});

	});
	
	suite('#connectionId()', function() {
		setup(function()  {
			this.mainChannel = new wdi.SpiceChannel();
			this.stub = sinon.stub(this.mainChannel, "connect", function() {
				this.fire("connectionId", "12345");
				this.fire("channelListAvailable", [1,2]);
			});
			
			this.displayChannel = new wdi.SpiceChannel();
			this.mock = sinon.mock(this.displayChannel);
			
			this.spcConnect = new wdi.SpiceConnection({
				mainChannel:this.mainChannel,
				displayChannel:this.displayChannel,
				connectionControl: {
					connect: function() {},
					addListener: function() {}
				}
			});
		});
		
		test('Should call connect on display channel when connectionId is available', function() {
			this.expectation = this.mock.expects('connect').once();
			this.spcConnect.connect('localhost', 8000);
			this.mock.verify();
		});
	});

});
	
