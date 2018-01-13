suite('ClusterNodeChooser', function () {
	var sut;
	var shuffleStub;

	setup(sinon.test(function () {
		sut = new wdi.ClusterNodeChooser();
	}));

	function addListWithNumberOfNodesToSut(sut, n) {
		var i;
		var list = [];
		for (i = 1; i <= n; i++) {
			list.push({
				host: 'somehost' + i,
				port: 10000 + i
			});
		}
		sut.setNodeList(list);
	}

	test('setNodeList should shuffle the received list', sinon.test(function () {
		var list = 'fake list';
		this.mock(sut)
			.expects('_shuffle')
			.once()
			.withExactArgs(list)
			.returns(list);

		sut.setNodeList(list);
	}));

	test('2 consecutive calls to getAnother should return different nodes when there are more than 1', sinon.test(function () {
		addListWithNumberOfNodesToSut(sut, 2);
		var first;
		var second;
		first = sut.getAnother();
		second = sut.getAnother();
		assert.notDeepEqual(first, second, "returned nodes on 2 consecutive calls should not be equal if there are more than one node");
	}));

	test('consecutive calls to getAnother should return always the same node when there is only one', sinon.test(function () {
		addListWithNumberOfNodesToSut(sut, 1);
		var first;
		var second;
		first = sut.getAnother();
		second = sut.getAnother();
		assert.deepEqual(first, second, "returned nodes on 2 consecutive calls should be equal if there is only one node");
	}));

	test('n+1 consecutive calls to getAnother return the same node on first call and on n+1 call', sinon.test(function () {
		var n = 5;
		addListWithNumberOfNodesToSut(sut, n);

		var i;
		var first = sut.getAnother();
		var ignored;
		for (i = 1; i < n; i++) {
			// do n-1 calls so at the end of the loop we've done n calls
			ignored = sut.getAnother();
		}
		var n_plus_one = sut.getAnother();

		assert.deepEqual(first, n_plus_one, "returned node on call 1 and on call n+1 should be the same");
	}));

});
