suite('syncasynchandler', function () {
	var sut;
	var callbackWrapper;
	var asyncWorker;
	var scope;

	setup(function() {
		asyncWorker = {
			run: function () {}
		};

		var isAsync = true;

		asyncSut = new wdi.SyncAsyncHandler({
			asyncWorker: asyncWorker,
			isAsync: isAsync
		});


		syncSut = new wdi.SyncAsyncHandler({
			isAsync: !isAsync
		});

		callbackWrapper = {
			callback: function () {}
		};

		scope = {};
	});

	teardown(function () {

	});

	test('dispatch calls workerProcess dispatch when sync', sinon.test(function() {
		var stub = this.stub(window, 'workerDispatch');
		var buffer = 'one buffer';
		syncSut.dispatch(buffer, callbackWrapper.callback, scope);

		var isAsync = false;

		sinon.assert.calledWithExactly(stub, buffer, isAsync);
	}));

	test('dispatch calls callback with dispatch result when sync', sinon.test(function() {
		var resultFromDispatch = 'some result';
		var stub = this.stub(window, 'workerDispatch').returns(resultFromDispatch);
		var buffer = 'one buffer';
		var callbackStub = sinon.stub();
		syncSut.dispatch(buffer, callbackStub, scope);

		sinon.assert.calledWithExactly(callbackStub, resultFromDispatch);
	}));

	test('dispatch calls AsyncWorker dispatch when async', sinon.test(function() {
		var stub = this.stub(asyncWorker, 'run');
		var buffer = 'one buffer';
		asyncSut.dispatch(buffer, callbackWrapper.callback, scope);

		sinon.assert.calledWithExactly(stub, buffer, callbackWrapper.callback, scope);
	}));
});
