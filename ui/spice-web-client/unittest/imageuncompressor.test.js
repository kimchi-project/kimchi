suite("Image uncompressor suite", function () {
	var syncAsyncHandler, sut, clientGui, context, headerType,
		imageDescriptor, opaque, callback, scope;

	setup(function () {
		callback = function () {};
		scope = {};

		opaque = 1;

		headerType = 1;

		imageDescriptor = {
			type: wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_RGB,
			width: 10,
			height: 10
		};

		var context = window.$('<canvas>')[0].getContext('2d');
		clientGui = {
			getContext: function (pos) {
				return context;
			}
		};
		syncAsyncHandler = {
			dispatch: function () {}
		};
		sut = new wdi.ImageUncompressor({syncAsyncHandler: syncAsyncHandler});
	});

	teardown(function () {

	});

	test.skip('processLz calls syncAsyncHandler.dispatch', sinon.test(function() {
		var stub = stubSyncAsync(this);
		var demarshallStub = stubDemarshall(this);

		var imageData = [1,2,3];

		var bufferData = [1,2,3];
		var buffer = new ArrayBuffer(bufferData.length + 8);
		u8 = new Uint8Array(buffer);

		u8[0] = 1; //LZ_RGB
		u8[1] = opaque;
		u8[2] = headerType;
		u8[3] = 0; //padding

		u8[4] = 144;
		u8[5] = 1;
		u8[6] = 0;
		u8[7] = 0;

		u8.set(bufferData, 8);

		var brush = true;

		sut.processLz(imageData, brush, opaque, clientGui, callback, scope);

		sinon.assert.calledWithExactly(stub, buffer, callback, scope);
	}));

	function stubDemarshall(self) {
		return self.stub(wdi.LZSS, 'demarshall_rgb').returns({
			type: headerType,
			width: 10,
			height: 10
		});
	}

	function stubSyncAsync(self) {
		return self.stub(syncAsyncHandler, 'dispatch');
	}

	test('processLz calls LZSS.demarshall_rgb when brush', sinon.test(function () {
		var dispatchStub = stubSyncAsync(this);
		var stub = stubDemarshall(this);

		var imageData = [1,2,3];

		var brush = true;

		sut.processLz(imageData, brush, opaque, clientGui, callback, scope);

		sinon.assert.calledWithExactly(stub, imageData);
	}));

	test('processLz calls LZSS.demarshall_rgb when no brush and imageData is array', sinon.test(function () {
		var dispatchStub = stubSyncAsync(this);
		var stub = stubDemarshall(this);

		var imageData = [];
		imageData.length = 32;
		imageData.push(1);
		imageData.push(2);
		imageData.push(3);

		expectedData = [];
		expectedData.length = 32;

		var brush = false;

		sut.processLz(imageData, brush, opaque, clientGui, callback, scope);

		sinon.assert.calledWithExactly(stub, expectedData);
	}));

	test('processLz calls LZSS.demarshall_rgb when no brush and imageData is typedArray', sinon.test(function () {
		var dispatchStub = stubSyncAsync(this);
		var stub = stubDemarshall(this);

		var buffer = new ArrayBuffer(35);
		u8ImageData = new Uint8Array(buffer);

		var expectedData = [0,0,0,0,0,0,0,0,
							0,0,0,0,0,0,0,0,
							0,0,0,0,0,0,0,0,
							0,0,0,0,0,0,0,0];

		var brush = false;

		sut.processLz(u8ImageData, brush, opaque, clientGui, callback, scope);

		sinon.assert.calledWithExactly(stub, expectedData);
	}));

	function quicTestOpaque (opaque, self) {
		var obtainedBuff;
		var dispatchStub = self.stub(syncAsyncHandler, 'dispatch', function (buff) {
			obtainedBuff = buff;
		});

		var imageData = [];

		var buffer = new ArrayBuffer(4);
		var view = new Uint8Array(buffer);

		view[3] = opaque ? 1 : 0;
		view[0] = 0; //quic
		sut.processQuic(imageData, opaque, clientGui, callback, scope);

		sinon.assert.calledWithExactly(dispatchStub, buffer, callback, scope);

		// sinon.deepEqual cannot acces the data inside the arrayBuffer
		// so we check also the data.
		var obtainedView = new Uint8Array(obtainedBuff);
		assert.deepEqual(view, obtainedView, "The data inside the buffer does not match");
	}

	test('processQuic calls syncAsyncHandler.dispatch with opaque', sinon.test(function () {
		opaque = true;
		quicTestOpaque(opaque, this);
	}));

	test('processQuic calls syncAsyncHandler.dispatch without opaque', sinon.test(function () {
		opaque = false;
		quicTestOpaque(opaque, this);
	}));

	test('process calls processQuic when image is quic', sinon.test(function () {
		var stub = this.stub(sut, 'processQuic');

		var imageData = [], brush = 1;

		imageDescriptor.type = wdi.SpiceImageType.SPICE_IMAGE_TYPE_QUIC;

		sut.process(imageDescriptor, imageData, brush, opaque, clientGui, callback, scope);

		sinon.assert.calledWithExactly(stub, imageData, opaque, clientGui, callback, scope);
	}));

	test('process calls processLz when image is lz', sinon.test(function () {
		var stub = this.stub(sut, 'processLz');

		var imageData = [], brush = 1;

		imageDescriptor.type = wdi.SpiceImageType.SPICE_IMAGE_TYPE_LZ_RGB;

		sut.process(imageDescriptor, imageData, brush, opaque, clientGui, callback, scope);

		sinon.assert.calledWithExactly(stub, imageData, brush, opaque, clientGui, callback, scope);
	}));

	test('extractLzHeader returns an imagedata with the header extracted when no brush', sinon.test(function() {
		var brush = false;
		var expected = 123;
		var imageData = [];
		imageData.length = sut.lzHeaderSize;
		imageData.push(expected);
		var result = sut.extractLzHeader(imageData, brush);
		assert.equal(result.imageData[0], expected, "header not extracted correctly from imageData");
	}));
});
