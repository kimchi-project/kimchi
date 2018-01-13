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

wdi.PacketFilter = {
	restoreContext: false,
	start: null,
	filter: function(spiceMessage, fn, scope, clientGui) {
		if(wdi.logOperations) {
			this.start = Date.now();
		}

		//TODO: design an architecture for loading
		//dynamic filters, instead of filtering here.
		//This should be just the entry point for filters.
		if (wdi.graphicDebug && wdi.graphicDebug.debugMode) {
			wdi.graphicDebug.printDebugMessageOnFilter(spiceMessage, clientGui);
		}
		//end of hardcoded filter

        // MS Word Benchmark startup
        if (wdi.IntegrationBenchmark && wdi.IntegrationBenchmark.benchmarking) {
            var date = new Date();
            wdi.IntegrationBenchmark.setStartTime(date.getTime());
        }

		//check clipping
		if(spiceMessage.args.base) {
			if(spiceMessage.args.base.clip.type === wdi.SpiceClipType.SPICE_CLIP_TYPE_RECTS) {
				var context = clientGui.getContext(spiceMessage.args.base.surface_id);
				context.save();
				context.beginPath();
				var rects = spiceMessage.args.base.clip.rects.rects;
				var len = rects.length;
				while(len--) {
					var box = wdi.graphics.getBoxFromSrcArea(rects[len]);
					context.rect(box.x, box.y, box.width, box.height);
				}
				context.clip();
				this.restoreContext = spiceMessage.args.base.surface_id;
			}
		}
        fn.call(scope, spiceMessage);
	},

    notifyEnd: function(spiceMessage, clientGui) {
		if(this.restoreContext !== false) {
			var context = clientGui.getContext(this.restoreContext);
			context.restore();
			this.restoreContext = false;
		}

        if(wdi.SeamlessIntegration) {
			var filterPosition = null;
			if(spiceMessage.args.base && spiceMessage.args.base.box) {
				filterPosition = spiceMessage.args.base.box;
			}
            clientGui.fillSubCanvas(filterPosition);
        }

		if (wdi.graphicDebug && wdi.graphicDebug.debugMode) {
			wdi.graphicDebug.printDebugMessageOnNotifyEnd(spiceMessage, clientGui);
		}

        // MS Word Benchmark
        if (wdi.IntegrationBenchmark && wdi.IntegrationBenchmark.benchmarking) {
            var date = new Date();
            wdi.IntegrationBenchmark.setEndTime(date.getTime());
        }

        // clear the tmpcanvas
        wdi.GlobalPool.cleanPool('Canvas');
		wdi.GlobalPool.cleanPool('Image');
		if(wdi.logOperations) {
			wdi.DataLogger.log(spiceMessage, this.start);
		}
	}



}

