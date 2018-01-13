suite('StuckKeysHandler:', function () {
	var sut;
	var testedKeys = [16, 17, 18];
	var i;

	setup(function () {
		wdi.Debug.debug = false; //disable debugging, it slows tests
		sut = new wdi.StuckKeysHandler();
	});

	function getExpectedEvent (keycode) {
		return sinon.match({
			charCode: 0,
			generated: true,
			keyCode: keycode,
			type: "keyup",
			which: keycode
		});
	}

	function getFakeJqueryEvent (type, keycode) {
		return {
			type: type,
			keyCode: keycode
		};
	}

	function getFunctionToTestHandleStuckKeysWhenPressing (keyCode) {
		return function () {
			var fakeJqueryEvent = getFakeJqueryEvent('keydown', keyCode);
			var expectedEvent = getExpectedEvent(keyCode);
			this.stub(global, 'setTimeout', function (callback, timeout) {
				callback();
			});
			this.stub(window.jQuery, 'Event', function (type) {
				return {type: type};
			});
			this.mock(sut)
				.expects('fire')
				.once()
				.withExactArgs('inputStuck', ['keyup', [expectedEvent]]);

			sut.handleStuckKeys(fakeJqueryEvent);
		};
	}

	function getFunctionToTestHandleStuckKeysWhenReleasing (keyCode) {
		return function () {
			var fakeTimeoutId = 'fakeTimeoutId' + keyCode;

			this.stub(global, 'setTimeout', function (callback, timeout) {
				return fakeTimeoutId;
			});

			this.mock(global)
				.expects('clearTimeout')
				.once()
				.withExactArgs(fakeTimeoutId);

			sut.handleStuckKeys(getFakeJqueryEvent('keydown', keyCode));
			sut.handleStuckKeys(getFakeJqueryEvent('keyup', keyCode));
		};
	}

	for (i = 0; i < testedKeys.length; i++) {
		test('handleStuckKeys fires an event when pressing keycode ' + testedKeys[i],
			sinon.test(getFunctionToTestHandleStuckKeysWhenPressing(testedKeys[i]))
		);
		test('handleStuckKeys calls clearTimeout when releasing the previous key ' + testedKeys[i],
			sinon.test(getFunctionToTestHandleStuckKeysWhenReleasing(testedKeys[i]))
		);
	}

	test('releaseAllKeys fires 300 events', sinon.test(function () {
		var expectedEvent = sinon.match({
			charCode: 0,
			generated: true,
			which: sinon.match.number,
			keyCode: sinon.match.number
		});
		this.mock(sut)
			.expects('fire')
			.exactly(300)
			.withExactArgs('inputStuck', ['keyup', [expectedEvent]]);
		;
		sut.releaseAllKeys();
	}));

	var keyupEvent = 'keyup',
		shiftKey = 16,
		ctrlKey = 17,
		altKey = 18;

	suite('#checkSpecialKeys', function () {
		var keydownEvent = 'keydown';

		function execute (event, keyCode) {
			sut.checkSpecialKey(event, keyCode);
		}

		test('set shiftKeyPressed = true when a shift is pressed', function () {
			execute(keydownEvent, shiftKey);
			assert.isTrue(sut.shiftKeyPressed);
		});

		test('set shiftKeyPressed = false when a shift is released', function () {
			execute(keyupEvent, shiftKey);
			assert.isFalse(sut.shiftKeyPressed);
		});

		test('set ctrlKeyPressed = true when a ctrl is pressed', function () {
			execute(keydownEvent, ctrlKey);
			assert.isTrue(sut.ctrlKeyPressed);
		});

		test('set ctrlKeyPressed = true when a ctrl is released', function () {
			execute(keyupEvent, ctrlKey);
			assert.isFalse(sut.ctrlKeyPressed);
		});

		test('set altKeyPressed = true when a alt is pressed', function () {
			execute(keydownEvent, altKey);
			assert.isTrue(sut.altKeyPressed);
		});

		test('set altKeyPressed = true when a alt is released', function () {
			execute(keyupEvent, altKey);
			assert.isFalse(sut.altKeyPressed);
		});
	});

	suite('#releaseSpecialKeysPressed', function () {
		function createKeyupEvent (keyCode) {
			var e = sinon.match({
				charCode: 0,
				generated: true,
				which: keyCode,
				keyCode: keyCode
			});
			return e;
		}

		test('fires an event when a shift is check as pressed', sinon.test(function () {
			sut.shiftKeyPressed = true;
			this.mock(sut)
				.expects('fire')
				.once()
				.withExactArgs('inputStuck', [ keyupEvent, [ createKeyupEvent(shiftKey) ] ]);
			sut.releaseSpecialKeysPressed();
		}));

		test('set shiftKeyPressed = false', function () {
			sut.shiftKeyPressed = true;
			this.stub(sut, 'fire');
			sut.releaseSpecialKeysPressed();
			assert.isFalse(sut.shiftKeyPressed);
		});

		test('fires an event when a ctrl is check as pressed', sinon.test(function () {
			sut.ctrlKeyPressed = true;
			this.mock(sut)
				.expects('fire')
				.once()
				.withExactArgs('inputStuck', [ keyupEvent, [ createKeyupEvent(ctrlKey) ] ]);
			sut.releaseSpecialKeysPressed();
		}));

		test('set ctrlKeyPressed = false', function () {
			sut.ctrlKeyPressed = true;
			this.stub(sut, 'fire');
			sut.releaseSpecialKeysPressed();
			assert.isFalse(sut.ctrlKeyPressed);
		});

		test('fires an event when a shift is check as pressed', sinon.test(function () {
			sut.altKeyPressed = true;
			this.mock(sut)
				.expects('fire')
				.once()
				.withExactArgs('inputStuck', [ keyupEvent, [ createKeyupEvent(altKey) ] ]);
			sut.releaseSpecialKeysPressed();
		}));

		test('set altKeyPressed = false', function () {
			sut.altKeyPressed = true;
			this.stub(sut, 'fire');
			sut.releaseSpecialKeysPressed();
			assert.isFalse(sut.altKeyPressed);
		});

	});
});
