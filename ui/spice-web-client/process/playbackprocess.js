wdi.PlaybackProcess = $.spcExtend(wdi.EventObject.prototype, {
	_lastApp: null,
	started: false,
	minBuffSize: 1024*32,
	frequency: null,
	channels: null,
	audioContext: null,
	startTime: null, // controls the playback time if no delay occurs
	hasAudioSupport: true, //whether the browser supports HTML5 Web Audio API

	typedBuffer: null,
	position: null,


	init: function(c) {
		this.app = c.app;
		this.audioContext = this.getAudioContext();
		if (this.audioContext) {
			this.hasAudioSupport = true;
		} else {
			this.hasAudioSupport = false;
			wdi.Debug.warn('The client browser does not support Web Audio API');
		}
		this.startTime = 0;
		this.typedBuffer = new ArrayBuffer(1024*32);
		this.position = 0;
	},

	getAudioContext: function() {
		//standard browser object
		try {
			return new AudioContext();
		} catch(e) {

		}

		//chrome and safari
		try {
		   return new webkitAudioContext();

		} catch(e) {

		}

		return false;
	},

	process: function(spiceMessage) {

		// if (this.hasAudioSupport && !Modernizr.touch) {
		if (this.hasAudioSupport) {
			switch (spiceMessage.messageType) {
				case wdi.SpiceVars.SPICE_MSG_PLAYBACK_MODE:
					break;
				case wdi.SpiceVars.SPICE_MSG_PLAYBACK_START:
					var packet = spiceMessage.args;
					this.channels = packet.channels;
					this.frequency = packet.frequency;
					break;
				case wdi.SpiceVars.SPICE_MSG_PLAYBACK_STOP:
					this.startTime = 0;
					var packet = spiceMessage.args;
					this.flush();
					break;
				case wdi.SpiceVars.SPICE_MSG_PLAYBACK_DATA:
					// While we receive data chunks, we store them in a buffer, so than when it is full we play the sound and empty it.
					// With this we get a more fluid playback and better overall performance than if we just played the data the moment we got it
					var packet = spiceMessage.args;
					var dataTimestamp = spiceMessage.args.multimedia_time;


					var tmpview = new Uint8Array(this.typedBuffer);
					tmpview.set(packet.data, this.position);
					this.position += packet.data.length;
					this._lastApp = this.app;

					if(this.position >= this.minBuffSize) {
						// ok, the buffer is full. We send the data to be played and later we can empty it to make room for more audio
						this.flush(dataTimestamp);
					}
					break;
			}
		} else {
			//TODO:
			// If the browser doesn't support Web Audio, we could still attach a wav header to the raw PCM we receive from spice and use the more widespread supported audio tag
			// Meanwhile, we can skip all the audio packets and gain some performance at least
		}
	},

	/**
	 * Plays all the audio buffer and empties it
	 *
	 * @param app
	 * @param dataTimestamp
	 */
	flush: function(dataTimestamp) {
		if(this.position > 0) {
			if (this.started) {
				this.playSound(this.typedBuffer, dataTimestamp);
			}
			this.position = 0;
			this.typedBuffer = new ArrayBuffer(1024*32);
		}
	},

	/**
	 * Plays the raw pcm data passed as param using HTML5's Web Audio API
	 *
	 * @param buffer
	 */
	playSound: function(buffer, dataTimestamp) {
		if(this.channels == 2) {
			return this.playSoundStereo(buffer, dataTimestamp);
		}

		var audio = new Int16Array(buffer);

		var channelData = new Array(this.channels);
		for(var i = 0;i<this.channels;i++) {
			channelData[i] = new Float32Array(audio.length / 2);
		}

		var channelCounter = 0;
		for (var i = 0; i < audio.length; ) {
		  for(var c = 0; c < this.channels; c++) {
			  //because the audio data spice gives us is 16 bits signed int (32768) and we wont to get a float out of it (between -1.0' and 1.0)
			  channelData[c][channelCounter] = audio[i++] / 32768;
		  }
		  channelCounter++;
		}

		var source = this.audioContext['createBufferSource'](); // creates a sound source
		var audioBuffer = this.audioContext['createBuffer'](this.channels, channelCounter, this.frequency);
		for(var i=0;i < this.channels; i++) {
			audioBuffer['getChannelData'](i)['set'](channelData[i]);
		}

		this._play(source, audioBuffer, dataTimestamp);
	},

	/**
	 * Plays the raw pcm STEREO data passed as param using HTML5's Web Audio API
	 *
	 * @param buffer
	 */
	playSoundStereo: function(buffer, dataTimestamp) {
		// Each data packet is 16 bits, the first being left channel data and the second being right channel data (LR-LR-LR-LR...)
		var audio = new Int16Array(buffer);

		// We split the audio buffer in two channels. Float32Array is the type required by Web Audio API
		var left = new Float32Array(audio.length / 2);
		var right = new Float32Array(audio.length / 2);

		var channelCounter = 0;

		var audioContext = this.audioContext;
		var len = audio.length;

		for (var i = 0; i < len; ) {
		  //because the audio data spice gives us is 16 bits signed int (32768) and we wont to get a float out of it (between -1.0 and 1.0)
		  left[channelCounter] = audio[i++] / 32768;
		  right[channelCounter] = audio[i++] / 32768;
		  channelCounter++;
		}

		var source = audioContext['createBufferSource'](); // creates a sound source
		var audioBuffer = audioContext['createBuffer'](2, channelCounter, this.frequency);

		audioBuffer['getChannelData'](0)['set'](left);
		audioBuffer['getChannelData'](1)['set'](right);

		this._play(source, audioBuffer, dataTimestamp);
	},

	_play: function(source, audioBuffer, dataTimestamp) {
		var wait = 0;
		if (dataTimestamp) {
			var elapsedTime = Date.now() - this.app.lastMultimediaTime; // time passed since we received the last multimedia time from main channel
			var currentMultimediaTime = elapsedTime + this.app.multimediaTime; // total delay we have at the moment
			wait = dataTimestamp - currentMultimediaTime;
			if (wait < 0) {
				wait = 0;
			}
		}
		source['buffer'] = audioBuffer;
		source['connect'](this.audioContext['destination']);	   // connect the source to the context's destination (the speakers)

		//if (!Modernizr.touch) {
			source['start'](this.startTime + wait);						   // play the source now
		//} else {
		//	source.noteOn(0);
		//}

		this.startTime += audioBuffer.duration;
	},

	startAudio: function () {
		this.started = true;
		this.flush();
	}
});
