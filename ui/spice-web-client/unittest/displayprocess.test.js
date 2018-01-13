suite('DisplayProcess', function() {
	var sut;
	var runQ;
	var fakePacketFilter;
	var fakeClientGui;
	var displayRouter;
	var packetWorkerIdentifier;

	setup(function(){
		wdi.Debug.debug = false; //disable debugging, it slows tests
	});

	suite('#process()', function() {
		setup(function() {
			runQ = new wdi.RunQueue();

			fakePacketFilter = {
				notifyEnd: function() {

				},

				filter: function(o, fn, scope) {
					fn.call(scope, o);
				}
			};

			fakeClientGui =  {};

			displayRouter = new wdi.DisplayRouter();

			packetWorkerIdentifier = {
				getImageProperties: function() {
					return false;
				}
			};

			displayRouter.packetProcess = function(spiceMessage) {}; //replace packetProcess, because of partial mocking
			sut = new wdi.DisplayProcess({
				runQ: runQ,
				packetFilter: fakePacketFilter,
				clientGui: fakeClientGui,
				displayRouter: displayRouter,
				packetWorkerIdentifier: packetWorkerIdentifier
			});


			wdi.ExecutionControl.sync = true;
		});

		test('displayProcess process should call packetFilfer process', sinon.test(function() {
			var fakeProxy = {
				end:function() {

				}
			};
			runQ.add = function(fnStart, scope, fnEnd) {
				fnStart.call(scope, fakeProxy);
			}
			this.mock(fakePacketFilter)
				.expects('filter')
				.once();
			sut._process(false);
		}));

		test('displayProcess process should call packetFilfer notifyEnd', sinon.test(function() {
			runQ.add = function(fn, scope, endFn) {
				fn.call(scope,{end:function(){}});
				endFn.call(scope);
			};

			this.mock(fakePacketFilter)
				.expects('notifyEnd')
				.once();
			sut._process(false);
		}));

		test('displayProcess process should call runq add', sinon.test(function() {
			this.mock(runQ)
				.expects('add')
				.once();
			sut._process(false);
		}));


		test('displayProcess process should call runq process', sinon.test(function() {
			this.mock(runQ)
				.expects('process')
				.once();
			sut._process(false);
		}));

		test('displayProcess process should call runq process', sinon.test(function() {
			this.mock(runQ)
				.expects('process')
				.once();
			sut._process(false);
		}));
	});
});
