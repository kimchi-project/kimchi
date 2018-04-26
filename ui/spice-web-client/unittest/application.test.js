suite('Application', function() {
	var sut, spiceConnection, fakeClientGui, clientGuiMock, toRestore = [];
	var timeLapseDetector;
	var connectionControl, fakeBusProcess, fakeBusConnection;

	setup(function() {
		wdi.Debug.debug = false; //disable debugging, it slows tests
		connectionControl = new wdi.ConnectionControl();
		spiceConnection = new wdi.SpiceConnection({
			connectionControl: new wdi.ConnectionControl()
		});
		fakeClientGui = {};
		fakeClientGui['addListener'] = function() {};
		fakeClientGui['releaseAllKeys'] = function() {};
		fakeClientGui['setClipBoardData'] = function() {};
		clientGuiMock = sinon.mock(fakeClientGui);
		fakeBusProcess = {addListener: function() {}};
		fakeBusConnection = {disconnect: function() {}, addListener: function() {}};
		timeLapseDetector = new wdi.TimeLapseDetector();
		sut = new Application({
			spiceConnection: spiceConnection,
			busConnection: fakeBusConnection,
			clientGui: fakeClientGui,
			busProcess: fakeBusProcess,
			timeLapseDetector: timeLapseDetector
		});
	});

	teardown(function () {
		toRestore.forEach(function (item) {
			item.restore();
		});
	});

	test('disconnect should call spiceConnection disconnect', function() {
		var mock = sinon.mock(spiceConnection);
		var expectation = mock.expects('disconnect').once().withArgs();
		sut.disconnect();
		expectation.verify();
	});

	test('disconnect should call busConnection disconnect', function() {
		sinon.stub(spiceConnection);
		var mock = sinon.mock(fakeBusConnection);
		var expectation = mock.expects('disconnect').once().withArgs();
		sut.disconnect();
		expectation.verify();
	});

	test('When spiceConnection fires channelConnected with channel inputs should call clientGui releaseAllKeys ', function () {

		var expectation = clientGuiMock.expects('releaseAllKeys').once();
		toRestore.push(clientGuiMock);

		spiceConnection.fire('channelConnected', wdi.SpiceVars.SPICE_CHANNEL_INPUTS);

		expectation.verify();
	});

	test('onTimeLapseDetected calls executeExternalCallback with the lapse', sinon.test(function () {
		var event = 'timeLapseDetected';
		var elapsed = 'fakeElapsedTime';

		this.mock(sut)
			.expects('executeExternalCallback')
			.once()
			.withExactArgs(event, elapsed);
		timeLapseDetector.fire(event, elapsed);
	}));

	function testObjectFiringEventCallsExternalCallbackWithError(self, object, event, params) {
		self.mock(sut)
			.expects('executeExternalCallback')
			.once()
			.withExactArgs('error', params);
		object.fire(event, params);
	}

	test('on spiceConnection.error event calls externalCallback with error', sinon.test(function () {
		testObjectFiringEventCallsExternalCallbackWithError(this, spiceConnection, 'error', 'fakeParams');
	}));

	test.skip('onClipBoardData calls executeExternalCallback when externalClipboardHandling', sinon.test(function () {
		var string = 'string to paste';
		sut.externalClipoardHandling = true;
		this.mock(sut)
			.expects('executeExternalCallback')
			.once()
			.withExactArgs('clipboardEvent', string);
		sut.onClipBoardData([0, string]);
	}));

	test.skip('onClipBoardData calls clientGui setClipBoardData when not externalClipboardHandling', sinon.test(function () {
		var string = 'string to paste';
		sut.externalClipoardHandling = false;
		this.mock(fakeClientGui)
			.expects('setClipBoardData')
			.once()
			.withExactArgs(string);
		sut.onClipBoardData([0, string]);
	}));

	test('onWrongPathError calls to executeExternalCallback', sinon.test(function () {
		var params = "fake params";
		this.mock(sut)
			.expects('executeExternalCallback')
			.once()
			.withExactArgs('wrongPathError', params);
		sut.onWrongPathError(params);
	}));

	test('onApplicationLaunchedSuccessfully calls to executeExternalCallback', sinon.test(function () {
		var params = "fake params";
		this.mock(sut)
			.expects('executeExternalCallback')
			.once()
			.withExactArgs('applicationLaunchedSuccessfully', params);
		sut.onApplicationLaunchedSuccessfully(params);
	}));

});
