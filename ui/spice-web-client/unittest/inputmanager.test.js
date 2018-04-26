suite("InputManager", function() {
	var sut;
	var input;
	var stuckKeysHandler;
	var window;
	var jQuery;
	var document;
	var input = 'test';
	var inputElement = {remove: function() {}};
	var inputElementMock;
	var expAddListeners;

	setup(function () {
		jQuery = function(elem) {return elem;};
		input = {
			on: function () {},
			select: function () {},
			focus: function () {},
			blur: function () {},
			val: function (a) {
				if (typeof(a) !== 'undefined') {
					this.value = a;
				} else {
					return this.value;
				}
			}
		};
		document = {
			body: {
				prepend: function() {}
			},
			getElementById: function() { return input;}
		};
		window = {
			on: function () {}
		};
		stuckKeysHandler = {
			releaseKeyPressed: function (a) { return a; },
			releaseSpecialKeysPressed: function () {}
		};
		sut = new wdi.InputManager({disableInput: true, input: input, stuckKeysHandler: stuckKeysHandler, window: window, jQuery: jQuery});
	});

	suite('#setCurrentWindow', function() {
		setup(function() {
			window = [{document: document}];
			sut.inputElement = inputElement;
			inputElementMock = sinon.mock(inputElement);
			expAddListeners = sinon.mock(sut).expects('addListeners').once().withExactArgs(window);
		});

		teardown(function() {
			inputElementMock.restore();
		});

		test('Should call addListeners with provided window', function() {
			sut.setCurrentWindow(window);
			expAddListeners.verify();
		});

		test('Should set currentWindow with provided window', function() {
			sut.setCurrentWindow(window);
			assert.equal(window, sut.currentWindow, 'Windows are not the same');
		});

		test('Should set currentWindow with provided window', function() {
			sut.setCurrentWindow(window);
			assert.equal(input, sut.input, 'Inputs are not the same');
		});

		test('Should call prepend with provided window', function() {
			var expectation = sinon.mock(document.body).expects('prepend').once().withExactArgs(inputElement);
			sut.setCurrentWindow(window);
			expectation.verify();
		});

		test('Should call remove from input element if there is currentWindow', function() {
			sut.currentWindow = {unbind: function() {}};
			var expectation = inputElementMock.expects('remove').once();
			sut.setCurrentWindow(window);
			expectation.verify();
		});

		test('Should call unbind when there is currentWindow', function() {
			sut.currentWindow = {unbind: function() {}};
			inputElementMock.expects('remove').once();
			var expectation = sinon.mock(sut.currentWindow).expects('unbind').once().withExactArgs('blur');
			sut.setCurrentWindow(window);
			expectation.verify();
		});
	});

	suite('#_onBlur', function () {
		test('Should call to window.on(blur)', sinon.test(function () {
			this.mock(window)
				.expects('on')
				.once()
				.withExactArgs('blur', sinon.match.func);
			sut._onBlur(window);
		}));

		test('Should call to input.focus when window.blur is triggered and checkFocus = true', sinon.test(function () {
			this.stub(window, 'on', function (event, callback) {
				callback();
			});
			this.mock(input)
				.expects('focus')
				.once()
				.withExactArgs();
			sut.checkFocus = true;
			sut._onBlur(window);
		}));

		test('Should not call to input.select when blur is triggered and checkFocus = false', sinon.test(function () {
			this.stub(input, 'on', function (event, callback) {
				callback();
			});
			this.mock(input)
				.expects('select')
				.never();
			sut._onBlur(window);
		}));

		test('Should fire releaseKey for shift, ctrl & alt', function () {
			this.stub(input, 'on', function (event, callback) {
				callback();
			});
			this.mock(sut)
				.expects('fire')
				.thrice();
			sut._onBlur(window);
		});
	});

	suite('#_onInput', function () {
		test('Should call to input.on(input)', sinon.test(function () {
			this.mock(input)
				.expects('on')
				.once()
				.withExactArgs('input', sinon.match.func);
			sut._onInput();
		}));

		test('Should reset the value when the input value has length > 1', sinon.test(function () {
			this.stub(input, 'on', function (event, callback) {
				callback();
			});
			input.val('a fake value');
			sut._onInput();
			assert.equal(input.val(), '');
		}));

		test('Should preserve the value when the input value has length = 1', sinon.test(function () {
			var aLetter = 'A';
			this.stub(input, 'on', function (event, callback) {
				callback();
			});
			input.val(aLetter);
			sut._onInput();
			assert.equal(input.val(), aLetter);
		}));
	});

	suite('#enable', function () {
		test('Should call to input.select', sinon.test(function () {
			this.mock(input)
				.expects('select')
				.once()
				.withExactArgs();
			sut.enable();
		}));

		test('Should set checkFocus = true', function () {
			sut.enable();
			assert.isTrue(sut.checkFocus);
		});
	});

	suite('#disable', function () {
		test('Should call to input.blur', sinon.test(function () {
			this.mock(input)
				.expects('blur')
				.once()
				.withExactArgs();
			sut.disable();
		}));

		test('Should set checkFocus = false', function () {
			sut.checkFocus = true;
			sut.disable();
			assert.isFalse(sut.checkFocus);
		});
	});

	suite('#reset', function () {
		test('Should call to input.val', sinon.test(function () {
			this.mock(input)
			.expects('val')
			.once()
			.withExactArgs("");
			sut.reset();
		}));
	});

	suite('#getValue', function () {
		var aValue = "fake value";

		test('Should call to input.val', sinon.test(function () {
			this.mock(input)
			.expects('val')
			.once()
			.withExactArgs();
			sut.getValue();
		}));

		test('Should reset the input when there is a value', sinon.test(function () {
			this.stub(input, 'val').returns(aValue);
			this.mock(sut)
				.expects('reset')
				.once()
				.withExactArgs();
			sut.getValue();
		}));

		test('Should do not reset the input when there is a value', sinon.test(function () {
			this.mock(sut)
				.expects('reset')
				.never();
			sut.getValue();
		}));

		test('Should return a value', function () {
			this.stub(input, 'val').returns(aValue);
			assert.equal(sut.getValue(), aValue);
		});
	});

	suite('#manageChar', function () {
		var TestCase = [
			{ val: "a", charCode: 97 },
			{ val: "A", charCode: 65 },
			{ val: "s", charCode: 115 },
			{ val: "S", charCode: 83 }
		];

		TestCase.forEach(function (data) {
			test('returns a updated params', function () {
				var params = [{ type: 'anotherType', charCode: 0 }],
					expected = [{ type: 'inputmanager', charCode: data.charCode }],
					curr = sut.manageChar(data.val, params);
				assert.deepEqual(curr, expected);
			});
		});

		test('the returned data is different from the params passed', function () {
			var params = [{ type: 'anotherType', charCode: 0 }],
				curr = sut.manageChar('h', params);
			assert.notDeepEqual(curr, params);
		});
	});

});
