suite('PacketProcess', function() {
  setup(function(){
	wdi.Debug.debug = false; //disable debugging, it slows tests
  });

  suite('#process()', function() {
	setup(function() {
		this.toRestore = [];
		this.packetProcess = new wdi.PacketProcess({
			mainProcess: true,
			displayProcess: true,
			cursorProcess: true,
			inputsProcess: true,
			playbackProcess: true
		});
	});

	test('Should throw an exception for invalid channels', function() {
		var failed = false;
		try {
			this.packetProcess.process({channel:99});
		} catch (e) {
			failed = true;
		}
		assert(failed, 'Exception expected for invalid channel');
	});

	test('Should throw an exception for null messages', function() {
		var failed = false;
		try {
			this.packetProcess.process();
		} catch (e) {
			failed = true;
		}
		assert(failed, 'Exception expected for null messages');
	});

	teardown(function() {
		this.toRestore.forEach(function(item) {
			item.restore();
		});
	});
  });
});
