wdi.DisplayPreProcess = $.spcExtend(wdi.EventObject.prototype, {
	displayProcess: null,
	queued: [],
	inProcess: [],
	idleConsumers : [],
	consumers: [],

	init: function(c) {
		this.superInit();
		this.displayProcess = c.displayProcess || new wdi.DisplayProcess({
			clientGui: c.clientGui
		});
		this.clientGui = c.clientGui;

		/**

		Since javascript do not provide an API to check
		the number of cpu cores available, the best case for average computers
		and devices is 4.

		If the computer doesn't have 4 or more available cores, there is only a little
		memory waste creating the threads and a bit of cpu overheat doing context
		switching.

		There is an ongoing draft in w3c to standarize a way to detect this:

		http://www.w3.org/2012/sysapps/device-capabilities/#cpu

		**/
		if(c.numConsumers == null || c.numConsumers == undefined) c.numConsumers = 4;
		var numConsumers = c.numConsumers;

		for(var i = 0;i<numConsumers; i++) {
			var consumer = new wdi.AsyncConsumer();
			this.consumers.push(consumer);
			this.idleConsumers.push(consumer);
			consumer.addListener('done', this.onConsumerDone, this);
		}
	},
		
	onConsumerDone: function(e) {
		//we don't care about who has finished, only about the
		//state of the last item in queue
		var waitingTask = this.inProcess[0];
		var task = null;
		var i = 0;
		
		while(waitingTask && waitingTask.state === 1) {
			task = this.inProcess.shift();
			try {
				this.displayProcess.process(task.message);
			} catch(e) {
				wdi.Debug.error("DisplayPreProcess error: ", e);
			}
			waitingTask = this.inProcess[0];
			i++;
		}
	
		//put the consumer as idle
		this.idleConsumers.push(e);
		//continue processing!
		if(this.queued.length > 0) {
			this.executeConsumer();
		}
	},
	
	process: function(spiceMessage) {
		this.addTask(spiceMessage); //first of all, queue it
		//it is the only item in the list?
		//we are the only message in the queue... process?
		this.executeConsumer();
	},

	addTask: function(spiceMessage) {
		this.queued.push({
			message: spiceMessage,
			clientGui: this.clientGui
		});
	},

	getNextTask : function () {
		var task = this.queued.shift();
		while(typeof task == 'undefined' && this.queued.length != 0) {
			task = this.queued.shift();
		}

		//we found a task?
		if(typeof task == 'undefined') {
			return false;
		}

		task.state = 0;
		this.inProcess.push(task); //add the task to the inProcess list
		return task;
	},

	executeConsumer: function() {
		//check if there are idle consumers
		if(this.idleConsumers.length > 0) {
			wdi.Debug.log('DisplayPreProcess: available workers: '+this.idleConsumers.length);
			wdi.Debug.log('DisplaypreProcess: pending tasks: '+this.queued.length);
			//idle consumer found
			var consumer = this.idleConsumers.shift();
			//execute the next task in this consumer
			var task = this.getNextTask();

			if(task) {
				consumer.consume(task);
			}

		}
	},

	dispose: function () {
		this.consumers.forEach(function (consumer) {
			consumer.dispose();
		});
	}
});
