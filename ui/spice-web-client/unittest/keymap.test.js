suite("Keymap", function() {
	var sut;

	setup(function () {
		sut = wdi.Keymap;
	});

	suite('#handledByCharmap', function () {
		test('return true when type is inputmanager', function () {
			assert.isTrue(sut.handledByCharmap('inputmanager'));
		});

		test('return false when type is not inputmanager', function () {
			assert.isFalse(sut.handledByCharmap('fakeEvent'));
		});
	});
});
