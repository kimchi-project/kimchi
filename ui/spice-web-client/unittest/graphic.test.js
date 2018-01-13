suite("Graphic suite", function () {
	var sut, clientGui;
	var imageData, brush, opaque;
	var imageDescriptor = {
		width: 10,
		height: 10
	};
	var header = {
		top_down: true
	};

	setup(function () {
		sut = wdi.graphics;

		var context = $('<canvas>')[0].getContext('2d');
		clientGui = {
			getContext: function (pos) {
				return context;
			}
		};
	});

	teardown(function () {

	});

	function testCheckingImageUncompressorIsCalled (method, self) {
		var imageUncompressor = new wdi.ImageUncompressor();
		var imageUncompressorStub = self.stub(imageUncompressor, 'process');
		var getInstanceStub = self.stub(wdi.ImageUncompressor, 'getSyncInstance')
			.returns(imageUncompressor);

		sut[method](imageDescriptor, imageData, brush, opaque, clientGui);

		sinon.assert.calledWithExactly(
			imageUncompressorStub, imageDescriptor, imageData,
			brush, opaque, clientGui, sinon.match.func, sut
		);
	}

	test('processQuic calls ImageUncompressor.process', sinon.test(function() {
		testCheckingImageUncompressorIsCalled('processQuic', this);
	}));

	test('processLz calls ImageUncompressor.process', sinon.test(function() {
		testCheckingImageUncompressorIsCalled('processLz', this);
	}));


	function testFunctionsReturnsImageData(method, self) {
		var processResult = new ArrayBuffer([1, 2, 3, 4]);
		var imageUncompressor = new wdi.ImageUncompressor();
		var imageUncompressorStub1 = self.stub(imageUncompressor, 'process',
			function(imageDescriptor, imageData, brush, opaque, clientGui, callback, scope) {
				callback.call(scope, processResult);
		});

		var imageUncompressorStub2 = self.stub(imageUncompressor, 'extractLzHeader').returns({
			header: header,
			imageData: 'an image Data'
		});

		var getInstanceStub = self.stub(wdi.ImageUncompressor, 'getSyncInstance')
			.returns(imageUncompressor);

		var u8 = new Uint8Array(processResult);
		var source_img = clientGui.getContext(0).createImageData(imageDescriptor.width, imageDescriptor.height);
		source_img.data.set(u8);

		var actual = sut[method](imageDescriptor, imageData, brush, opaque, clientGui);

		assert.deepEqual(actual, source_img);
	}


	test('processQuic returns an imageData', sinon.test(function() {
		testFunctionsReturnsImageData('processQuic', this);
	}));

	test('processLz returns an imageData', sinon.test(function() {
		testFunctionsReturnsImageData('processLz', this);
	}));

	function testFlip (self, processResult) {
		processResult = processResult || new ArrayBuffer([1, 2, 3, 4]);
		var imageUncompressor = new wdi.ImageUncompressor();
		var imageUncompressorStub = self.stub(imageUncompressor, 'process',
			function(imageDescriptor, imageData, brush, opaque, clientGui, callback, scope) {
				callback.call(scope, processResult);
		});

		var imageUncompressorStub2 = self.stub(imageUncompressor, 'extractLzHeader').returns({
			header: header,
			imageData: 'an image Data'
		});

		var getInstanceStub = self.stub(wdi.ImageUncompressor, 'getSyncInstance')
			.returns(imageUncompressor);

		sut.processLz(imageDescriptor, imageData, brush, opaque, clientGui);
	}

	test('processLz flips the image if topDown falsy in header', sinon.test(function () {
		header.top_down = false;

		var flipStub = this.stub(sut, 'imageFlip');
		var processResult = new ArrayBuffer([1, 2, 3, 4]);

		testFlip(this, processResult);

		var u8 = new Uint8Array(processResult);
		var source_img = clientGui.getContext(0).createImageData(imageDescriptor.width, imageDescriptor.height);
		source_img.data.set(u8);

		sinon.assert.calledWithExactly(flipStub, source_img);

	}));

	test('processLz never flips the image if topDown truthy in header', sinon.test(function () {
		header.top_down = true;

		var flipStub = this.stub(sut, 'imageFlip');

		testFlip(this);

		sinon.assert.notCalled(flipStub);
	}));
});
