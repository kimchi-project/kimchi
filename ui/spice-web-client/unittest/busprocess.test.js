suite("BusProcess:", function() {
	var sut;
	var clientGui, busConnection;

	setup(function () {
		clientGui = {};
		busConnection = {};
		sut = new wdi.BusProcess({ clientGui: clientGui, busConnection: busConnection });
	});

	suite('#parseMessage', function () {
		test('Should fire "wrongPathError" when the type is "launchApplication" and the event is "applicationLauncherWrongAppPathError"', sinon.test(function () {
			var body = {
				type: wdi.BUS_TYPES.launchApplication,
				event: "applicationLauncherWrongAppPathError"
			};
			this.mock(sut)
				.expects('fire')
				.once()
				.withExactArgs('wrongPathError', body);
			sut.parseMessage(body);
		}));
		test('Should not fire "wrongPathError" when the type is "launchApplication" and the event is not "applicationLauncherWrongAppPathError"', sinon.test(function () {
					var body = {
						type: wdi.BUS_TYPES.launchApplication,
						event: "fakeEvent"
					};
					this.mock(sut)
						.expects('fire')
						.never();
					sut.parseMessage(body);
				}));

		test('Should fire "applicationLaunchedSuccessfully" when the type is "launchApplication" and the event is "applicationLaunchedSuccessfully"', sinon.test(function () {
			var body = {
				type: wdi.BUS_TYPES.launchApplication,
				event: "applicationLaunchedSuccessfully"
			};
			this.mock(sut)
				.expects('fire')
				.once()
				.withExactArgs('applicationLaunchedSuccessfully', body);
			sut.parseMessage(body);
		}));
	});
});
