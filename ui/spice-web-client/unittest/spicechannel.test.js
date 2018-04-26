suite('SpiceChannel', function() {
	var sut, socketQ, toRestore, packetReassembler, config;

	setup(function() {
		wdi.Debug.debug = false; //disable debugging, it slows tests
		config = {
			protocol: 'ws',
			host: 'localhost',
			port: 8000,
			vmHost: 'localhost',
			vmPort: 5900,
			type: 'spice',
			token: 'sdfjgsd8f'
		};
		socketQ = new wdi.SocketQueue();
		packetReassembler = wdi.ReassemblerFactory.getPacketReassembler(socketQ);
		sut = new wdi.SpiceChannel({socketQ: socketQ, packetReassembler: packetReassembler});
		toRestore = [];
	});

	teardown(function() {
		toRestore.forEach(function(item) {
			item.restore();
		});
	});
	
	suite('Networking', function() {

		test('When open event it sends SpiceLinkInit', function() {
			var header = new wdi.SpiceLinkHeader({magic:1363428690, major_version:2, minor_version:2, size:22}).marshall();
			var body = new wdi.SpiceLinkMess({
				connection_id:0,
				channel_type:1,
				caps_offset:18,
				num_common_caps: 1,
				common_caps: (1 << wdi.SpiceVars.SPICE_COMMON_CAP_MINI_HEADER)
			}).marshall();
			var args = header.concat(body);
			var packetOut;
			var stub = sinon.stub(socketQ, 'send', function(packet) {
				packetOut = packet;
			});
			toRestore.push(stub);
			socketQ.fire('open');
			assert.deepEqual(packetOut, args, 'The packet is not a RedLinkMess or some parameter is incorrect');
		});

		test('When close event it disconnects socketQueue', function() {
			var mock = sinon.mock(socketQ);
			var expectation = mock.expects('disconnect').once();
			toRestore.push(mock);
			socketQ.fire('close');
			expectation.verify();
		});

		test('When error event it disconnects socketQueue', function() {
			var mock = sinon.mock(socketQ);
			var expectation = mock.expects('disconnect').once();
			toRestore.push(mock);
			socketQ.fire('close');
			expectation.verify();
		});

		test.skip('When packetComplete event containing spicePacket fires message with packet', function() {
			var header = [1, 0, 9, 0, 0, 0]
			var body = [0, 0, 0, 0, 0, 0, 0, 0, 0];
			var arr = header.concat(body);
			var expectedData = new wdi.RawMessage({status: 'spicePacket', data: arr}), obtainedData;
			sut.addListener('message', function(e) {
				obtainedData = e[1];
			}, this);

			toRestore.push(sinon.stub(wdi.PacketLinkFactory, "extract"));

			packetReassembler.fire('packetComplete', expectedData);

			assert.equal(body.length, obtainedData.header.size, 'The data doesn\'t match');
		});

		test('When packetComplete event containing reply sends response', function() {
			var redLinkReply = [82,69,68,81,2,0,0,0,2,0,0,0,186,0,0,0,0,0,0,0,48,129,159,48,13,6,9,42,134,72,134,247,13,1,1,1,5,0,3,129,141,0,48,129,137,2,129,129,0,222,245,236,144,74,241,132,122,250,245,13,59,69,38,226,122,250,73,31,214,203,27,154,16,6,11,91,88,125,158,197,150,32,60,201,138,249,22,59,109,232,64,42,46,79,170,248,239,172,142,240,63,83,130,221,21,207,83,210,112,82,20,214,169,219,27,129,45,241,13,172,228,208,196,200,24,89,163,38,186,139,96,5,24,108,57,9,223,217,215,106,89,118,215,245,214,71,139,141,1,186,111,61,88,37,155,65,65,121,220,133,237,190,114,198,66,62,125,133,62,214,132,69,164,190,184,169,39,2,3,1,0,1,1,0,0,0,1,0,0,0,178,0,0,0,11,0,0,0,18,0,0,0];
			var packet = new wdi.RawMessage({status: 'reply', data: redLinkReply});
			var mock = sinon.mock(socketQ);
			var expectation = mock.expects('send').once();
			toRestore.push(mock);
			packetReassembler.fire('packetComplete', packet);
			expectation.verify();
		});

		test('When packetComplete event containing errorCode 0 in main channel sends response', function () {
			var errorCode = [0, 0, 0, 0];
			var packet = new wdi.RawMessage({status: 'errorCode', data: errorCode});
			var mock = sinon.mock(socketQ);
			var expectation = mock.expects('send').once();
			toRestore.push(mock);
			packetReassembler.fire('packetComplete', packet);
			expectation.verify();
		});

		test('When packetComplete event containing errorCode not 0 throws exception', function () {
			var errorCode = [1, 0, 0, 0];
			var packet = new wdi.RawMessage({status: 'errorCode', data: errorCode});
			assert.throws(function () {
				packetReassembler.fire('packetComplete', packet);
			});
		});

		test('When packetComplete event containing errorCode 0 in display channel sends response', function () {
			var errorCode = [0, 0, 0, 0];
			sut.channel = wdi.SpiceVars.SPICE_CHANNEL_DISPLAY;
			var packet = new wdi.RawMessage({status: 'errorCode', data: errorCode});
			var mock = sinon.mock(socketQ);
			var expectation = mock.expects('send').once();
			toRestore.push(mock);
			packetReassembler.fire('packetComplete', packet);
			expectation.verify();
		});

		test('When packetComplete event containing errorCode 0 fires channelConnected event', function () {
			var errorCode = [0, 0, 0, 0];
			var packet = new wdi.RawMessage({status: 'errorCode', data: errorCode});
			sinon.stub(socketQ, 'send', function () {});

			var fired = false;
			sut.addListener('channelConnected', function (e) {
				fired = true;
			}, this);

			packetReassembler.fire('packetComplete', packet);
			assert.equal(fired, true);
		});

	});
	
	suite.skip('#getRawSpiceMessage', function () {
		test('returns a valid rawSpiceMessage', function () {
			var data = [1, 0, 9, 0, 0, 0, 0,0,0,0,0,0,0,0,0];
			toRestore.push(sinon.stub(wdi.PacketLinkFactory, "extract"));
			var rsm = sut.getRawSpiceMessage(data);
			assert.equal(rsm.header.type, 1, "The header is not valid");
		});
	});

	suite('#connection', function() {

		test('connect should call socketQ connect with host and port if they are present', function() {
			var expectedString = config['protocol'] + '://' + config['host'] + ':' + config['port'] + '/websockify/host/' + config['vmHost'] + '/port/' + config['vmPort'] + '/type/' + config['type'];
			var mock = sinon.mock(socketQ);
			var stub = sinon.stub(packetReassembler, 'start');
			var expectation = mock.expects('connect').once().withArgs(expectedString);
			sut.connect(config);
			expectation.verify();
		});

        test('connect should call socketQ connect with destInfoToken if destHost and destPort are NOT present', function() {
            var tokenedConfig = {
                protocol: 'ws',
                host: 'localhost',
                port: 8000,
                vmInfoToken: 'token-token-token',
                type: 'spice',
                token: 'sdfjgsd8f'
            };
            var expectedString = tokenedConfig['protocol'] + '://' + tokenedConfig['host'] + ':' + tokenedConfig['port'] + '/websockify/destInfoToken/' + tokenedConfig['vmInfoToken'] + '/type/' + tokenedConfig['type'];
            var mock = sinon.mock(socketQ);
            var stub = sinon.stub(packetReassembler, 'start');
            var expectation = mock.expects('connect').once().withArgs(expectedString);
            sut.connect(tokenedConfig);
            expectation.verify();
        });

		test('disconnect should call socketQ disconnect', function() {
			var mock = sinon.mock(socketQ);
			var expectation = mock.expects('disconnect').once().withExactArgs();
			sut.disconnect();
			expectation.verify();
		});
	});
});
