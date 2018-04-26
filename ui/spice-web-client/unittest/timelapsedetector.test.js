suite('TimeLapseDetector:', function () {
	var sut;
	var clock;
	var now;

	setup(function () {
		wdi.Debug.debug = false; //disable debugging, it slows tests
		now = Date.now();
		clock = sinon.useFakeTimers(now);

		sut = new wdi.TimeLapseDetector();
	});

	teardown(function () {
		clock.restore();
	});

	test('when the timer is running normally, lastTime is updated', function () {
		sut.startTimer();

		clock.tick(wdi.TimeLapseDetector.defaultInterval);
		var expected = now + wdi.TimeLapseDetector.defaultInterval;
		assert.equal(expected, sut.getLastTime());
	});

	test('when the timer is running late an event is fired', function () {
		sut.startTimer();
		sut.setLastTime(now - (wdi.TimeLapseDetector.maxIntervalAllowed));

		var expected = wdi.TimeLapseDetector.maxIntervalAllowed + wdi.TimeLapseDetector.defaultInterval;

		var mock = sinon.mock(sut);
		var expectation = mock.expects('fire')
			.once()
			.withExactArgs('timeLapseDetected', expected);

		clock.tick(wdi.TimeLapseDetector.defaultInterval);

		expectation.verify();
	});

	test('when the timer is running late, lastTime is updated', function () {
		sut.startTimer();
		var passedTime = wdi.TimeLapseDetector.maxIntervalAllowed + 123;
		var expected = 0;
		while (expected + wdi.TimeLapseDetector.defaultInterval <= passedTime) {
			expected += wdi.TimeLapseDetector.defaultInterval;
		}
		expected += now;

		clock.tick(passedTime);
		assert.equal(expected, sut.getLastTime());
	});
});
