suite('DisplayProcess', function() {
	var sut;

	setup(function(){
		wdi.Debug.debug = false; //disable debugging, it slows tests
	});

	suite('#processPacket()', function() {
		setup(function() {



			wdi.ExecutionControl.sync = true;
		});

		test('displayRouter packetProcess should execute the correct route', sinon.test(function() {
			var executed = false;
			sut = new wdi.DisplayRouter({
				routeList: {
					45: function() {
						executed = true;
					}
				}
			});

			sut.processPacket({messageType:45});
			assert.isTrue(executed);
		}));

	});
});
