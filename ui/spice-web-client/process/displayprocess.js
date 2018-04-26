wdi.DisplayProcess = $.spcExtend(wdi.EventObject.prototype, {
	runQ: null,
	packetFilter: null,
	
	init: function(c) {
		this.runQ = c.runQ || wdi.ExecutionControl.runQ;
		this.packetFilter = c.packetFilter || wdi.PacketFilter;
		this.clientGui = c.clientGui;
		this.displayRouter = c.displayRouter || new wdi.DisplayRouter({clientGui:this.clientGui});
		this.started = false;
		this.waitingMessages = [];
		this.packetWorkerIdentifier = c.packetWorkerIdentifier || new wdi.PacketWorkerIdentifier();
	},

	process: function(spiceMessage) {
		//this._process(spiceMessage);
		//disable requestanimationframe equivalent for the moment
		//the remove redundant draws implementation is buggy
		//and there are considerations on how it is implemented


		var self = this;
		this.waitingMessages.push(spiceMessage);

		if(!this.started) {
			this.timer = setInterval(function() {
				self.flush();
			}, 50);
			this.started = true;
		}

	},

	flush: function() {
		if(this.waitingMessages.length === 0) {
			return;
		}

		var i = 0;
		var spiceMessage;

		//remove redundant draws
		this.removeRedundantDraws();

		var size = this.waitingMessages.length;

		while(i < size) {
			spiceMessage = this.waitingMessages[i];
			this._process(spiceMessage);
			i++;
		}

		this.waitingMessages = [];
	},

	removeRedundantDraws: function() {
		if(this.waitingMessages.length < 2) {
			return;
		}

		var size = this.waitingMessages.length;
		var message, body, imageProperties, rop, base;
		var collision_boxes = {};
		var to_delete = [];
		var deleted = false;
		var surface_id;
		var packetBox;
		var box;
		var i;
		var x;
		while(size--) {
			message = this.waitingMessages[size];
			//should remove any packet from the past overwritten by this one
			body = message.args;
			base = body.base;

			rop = body.rop_descriptor;
			deleted = false;

			//TODO TODO TODO: there is need for a special case for draw_copy_bits?!
			//we need base to have a box
			if(base) {
				surface_id = base.surface_id;
				packetBox = base.box;
				surface_id = base.surface_id;
				//check if this packet is occluded by another packet
				imageProperties = this.packetWorkerIdentifier.getImageProperties(message);
				//if there is no image properties, or there is but cache flags are 0
				if(!collision_boxes[surface_id]) {
					collision_boxes[surface_id] = [];
				}

				if((!imageProperties || (imageProperties && !(imageProperties.descriptor.flags & wdi.SpiceImageFlags.SPICE_IMAGE_FLAGS_CACHE_ME))) && surface_id === 0) {
					for(i=0; i<collision_boxes[surface_id].length; i++) {
						//check if base.box is inside one of the rectangles in collision_boxes
						box = collision_boxes[surface_id][i];
						if(box.bottom >= packetBox.bottom && box.top <= packetBox.top  && box.left <= packetBox.left
							&& box.right >= packetBox.right ) {

							deleted = true;
							to_delete.push(size);

							break;
						}
					}
				}

				//check if the message is still alive, and if it is, then put its box into collision_boxes if the message
				//will overWrite its screen area when painted
				//atm only drawcopy and drawfill have overwritescreenarea set
				if(!deleted && message.messageType === wdi.SpiceVars.SPICE_MSG_DISPLAY_COPY_BITS) {
					break;
				}

				if(!deleted && body.getMessageProperty('overWriteScreenArea', false) && base.clip.type == 0 && rop == wdi.SpiceRopd.SPICE_ROPD_OP_PUT) {
					collision_boxes[surface_id].push(base.box);
				}
			}
		}

		//itareate over messages marked for deletion and remove it from the array
		for(x = 0;x < to_delete.length;x++) {
			this.waitingMessages.splice(to_delete[x], 1);
		}
	},
		
	_process: function(spiceMessage) {
		if (wdi.logOperations) {
			wdi.DataLogger.log(spiceMessage, 0, null, true, '', '_decode');
		}
		//append the message to the runqueue
		//so the packet is not executed until the previous packets
		//finished processing
		this.runQ.add(function(proxy) {

			//pass the message through the packet filter
			//so the packet can be filtered, logged, etc
			this.packetFilter.filter(spiceMessage, function(message) {
				wdi.ExecutionControl.currentProxy = proxy;
				//process the packet
				this.displayRouter.processPacket(message);
				//post process operations
				this.postProcess();
			}, this, this.clientGui);


			//if the packet was synchronous, process next packet
			if (wdi.ExecutionControl.sync) {
				proxy.end();
			}
			//Now message could be asynchronous
		}, this, function() {
		   //this is executed when the message has finished processing
		   //we use processEnd to notify packetFilter about the ending of processing
		   //the current message
		   this.processEnd(spiceMessage, this.clientGui);

		});

		//if this is the first message in the queue, execute it
		//if not, this call will have no effect.
		this.runQ.process();

	},

	processEnd: function(spiceMessage, clientGui) {
		this.packetFilter.notifyEnd(spiceMessage, clientGui);
	},

	postProcess: function() {
		//TEST METHOD DON'T DELETE
	}
});

