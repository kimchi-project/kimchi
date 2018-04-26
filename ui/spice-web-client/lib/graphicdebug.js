/*
 eyeOS Spice Web Client
Copyright (c) 2015 eyeOS S.L.

Contact Jose Carlos Norte (jose@eyeos.com) for more information about this software.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License version 3 as published by the
Free Software Foundation.
 
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
details.
 
You should have received a copy of the GNU Affero General Public License
version 3 along with this program in the file "LICENSE".  If not, see 
<http://www.gnu.org/licenses/agpl-3.0.txt>.
 
See www.eyeos.org for more details. All requests should be sent to licensing@eyeos.org
 
The interactive user interfaces in modified source and object code versions
of this program must display Appropriate Legal Notices, as required under
Section 5 of the GNU Affero General Public License version 3.
 
In accordance with Section 7(b) of the GNU Affero General Public License version 3,
these Appropriate Legal Notices must retain the display of the "Powered by
eyeos" logo and retain the original copyright notice. If the display of the 
logo is not reasonably feasible for technical reasons, the Appropriate Legal Notices
must display the words "Powered by eyeos" and retain the original copyright notice. 
 */

wdi.GraphicDebug = $.spcExtend(wdi.DomainObject, {
	debugMode: null,
	spiceGraphicMessageTypes: [],
	cloneSpiceMessage: null,
	clientGui: null,
	tmpCanvas: null,
	tmpContext: null,
	originalCanvas: null,
	spiceMessageData: null,
	endCanvas: null,
	currentOperation: null,

	init: function(c) {
		this.debugMode = c.debugMode;
		if (this.debugMode) {
			this._generateArray();
			this._showDebug();
		} else {
			this._hideDebug();
		}
	},

	_generateArray: function() {
		var self = this;
		$.each(wdi.SpiceVars, function(key, value) {
			if (key.search("SPICE_MSG_DISPLAY_") != -1) {
				self.spiceGraphicMessageTypes[value] = key;
			}
		});
	},

	_showDebug: function() {
		$('#canvasSpace').show();
		$('#graphicDebug').show();
	},

	_hideDebug: function() {
		$('#canvasSpace').hide();
		$('#graphicDebug').hide();
	},

    printDebugMessageOnFilter: function(spiceMessage, clientGui) {
        if(spiceMessage.channel === wdi.SpiceVars.SPICE_CHANNEL_DISPLAY && this.debugMode && ($('#logActive').prop('checked'))) {
            var surface_id = null;
			this.clientGui = clientGui;
			this.cloneSpiceMessage = $.extend(true, {}, spiceMessage);
			if(this.cloneSpiceMessage.args.base && this.cloneSpiceMessage.args.base.surface_id !== null) {
				surface_id = this.cloneSpiceMessage.args.base.surface_id;
				var box = wdi.graphics.getBoxFromSrcArea(this.cloneSpiceMessage.args.base.box);
				var spiceMessageDiv = $('<div/>')
					.append(prettyPrint(this.cloneSpiceMessage))
					.hide();

				this.originalCanvas =  this._copyCanvasFromSurfaceId(surface_id);
				this.spiceMessageData = spiceMessage.args.originalData;
				this.currentOperation = this.spiceGraphicMessageTypes[this.cloneSpiceMessage.messageType];

				$('#debugInfo')
					.append($('<br/>'))
					.append($('<hr/>'))
					.append(this._copyAndHighlightCanvas(surface_id, box))
					.append($('<br/>'))
					.append($('<div/>')
						.append(this.currentOperation + ' (Click to hide/show)')
						.css('cursor', 'pointer')
						.css('color', 'blue')
						.css('text-decoration', 'underline')
						.click(function() {
							spiceMessageDiv.toggle();
						})
					).append(spiceMessageDiv);

				if (this.cloneSpiceMessage.args.hasOwnProperty('image')) {
					this._printImage(spiceMessageDiv);
				}
			}
		}
	},

	_printImage: function(spiceMessageDiv) {
		wdi.graphics.getImageFromSpice(this.cloneSpiceMessage.args.image.imageDescriptor, this.cloneSpiceMessage.args.image.data, this.clientGui, function(srcImg) {
			if(srcImg) {
				spiceMessageDiv.append(
					$('<div/>').css('font-size', '12px')
						.append('Image inside spiceMessage:')
						.append($('<br/>'))
						.css('border', '1px solid black')
						.append(srcImg)
				);
			}
		}, this);
	},

	printDebugMessageOnNotifyEnd: function(spiceMessage, clientGui) {
		this.clientGui = clientGui;
		if(spiceMessage.channel === wdi.SpiceVars.SPICE_CHANNEL_DISPLAY && this.debugMode && ($('#logActive').prop('checked'))) {
			var surface_id = null;
			if(spiceMessage.args.base && spiceMessage.args.base.surface_id !== null) {
				var self = this;
				var createTestClickCallback = function (currentSpiceMessage, originalCanvas, endCanvas, currentOperation) {
					return function () {
						self.createImageTest(currentSpiceMessage, originalCanvas, endCanvas, currentOperation);
					};
				};
				var createReplayClickCallback = function (currentSpiceMessage, originalCanvas, endCanvas, currentOperation) {
					return function () {
						self.createReplay(currentSpiceMessage, originalCanvas, endCanvas, currentOperation);
					};
				};
				surface_id = spiceMessage.args.base.surface_id;
				var box = wdi.graphics.getBoxFromSrcArea(spiceMessage.args.base.box);
				var currentCanvas = this._copyCanvasFromSurfaceId(surface_id);
				$('#debugInfo')
					.append($('<br/>'))
					.append($('<div/>')
						.append($('<button>Create test</button>')
							.css('cursor', 'pointer')
							.click(createTestClickCallback(this.spiceMessageData, this.originalCanvas, currentCanvas, this.currentOperation))
						)
						.append($('<button>Create replay window</button>')
							.css('cursor', 'pointer')
							.click(createReplayClickCallback(this.spiceMessageData, this.originalCanvas, currentCanvas, this.currentOperation))
						)
					).append($('<br/>'))
					.append(this._copyAndHighlightCanvas(surface_id, box));
			}
		}
	},

	createImageTest: function (spiceMessage, originalCanvas, endCanvas, currentOperation) {
		var name = prompt('Name of the test', currentOperation);
		var data1 = originalCanvas.toDataURL('image/png');
		var data2 = endCanvas.toDataURL('image/png');
		var dataObj = {
			origin: data1,
			expected: data2,
			object: spiceMessage,
			name: name
		};
		var data = JSON.stringify(dataObj);
		var fileName = name.replace(/\s/g, '_');

		$.post('graphictestgenerator.php','data=' + data + '&name=' + fileName).done(function (data,status,xhr) {
			alert('Test created');
		}).fail(function(jqXHR, textStatus, errorThrown) {
			alert('Test creation failed.\n\nGot response: ' + jqXHR.status + ' '
				+ jqXHR.statusText + '\n\n' + jqXHR.responseText);
		});

	},

	createReplay: function (spiceMessage, originalCanvas) {
		var data1 = originalCanvas.toDataURL('image/png');
		var dataObj = {
			origin: data1,
			object: spiceMessage,
			width: originalCanvas.width,
			height: originalCanvas.height
		};
		var data = JSON.stringify(dataObj);

		$.post('graphictestgenerator.php','data=' + data + '&replay=true').done(function (data,status,xhr) {
			window.open('replay.html', 'replay');
		}).fail(function(jqXHR, textStatus, errorThrown) {
			alert('Replay failed.\n\nGot response: ' + jqXHR.status + ' '
				+ jqXHR.statusText + '\n\n' + jqXHR.responseText);
		});
	},

	_copyCanvasFromSurfaceId: function (surface_id) {
		var context = this.clientGui.getContext(surface_id);
		this.tmpCanvas = context.canvas;
		var myCanvas = document.createElement('canvas');
		myCanvas.width = this.tmpCanvas.width;
		myCanvas.height = this.tmpCanvas.height;
		myCanvas.getContext('2d').drawImage(this.tmpCanvas, 0, 0);

		return myCanvas;
	},

	_copyAndHighlightCanvas: function(surface_id, box) {
		var myCanvas = this._copyCanvasFromSurfaceId(surface_id);

		context = myCanvas.getContext('2d');

		context.fillStyle = "rgba(255,0,0,0.3)";
		context.fillRect(box.x, box.y, box.width, box.height);
		return myCanvas;
	}


});
