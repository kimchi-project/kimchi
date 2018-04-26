suite('CollisionDetector', function() {

	var testData = [
		{
			base:{
				top:0,
				left:0,
				right:3,
				bottom:3
			},
			queue:{
				top:0,
				left:2,
				right:4,
				bottom:2
			},
			collides:true
		},
		{
			base:{
				top:0,
				left:0,
				right:5,
				bottom:5
			},
			queue:{
				top:3,
				left:-3,
				right:3,
				bottom:6
			},
			collides:true
		},
		{
			base:{
				top:0,
				left:0,
				right:5,
				bottom:5
			},
			queue:{
				top:3,
				left:6,
				right:8,
				bottom:4
			},
			collides:false
		}
	];
	var thereIsBoxCollision = function(){
		var data = thereIsBoxCollision.data;
		var actual = wdi.CollisionDetector.thereIsBoxCollision(data.base, data.queue);
		assert.equal(data.collides, actual);
	};
	thereIsBoxCollision.data = null;
	var setCounter=0;
	for(var i=0; i < testData.length; i++) {
		thereIsBoxCollision.data = testData[i];
		test('thereIsBoxCollision will return correctData with set '+setCounter, thereIsBoxCollision);
		setCounter++;
	}

});
