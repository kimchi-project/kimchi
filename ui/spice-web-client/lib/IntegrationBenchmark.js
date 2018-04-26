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

wdi.IntegrationBenchmark = {
    benchmarking: false,
	startTime: 0,
    timeoutInterval: 3000,  // in ms, amount of time after it will be considered that
                            // we have received all packets and can stop counting
    timeOutId: undefined,

    busConnection: undefined,

    setEndTime: function() {
        var self = this;
        this.timeOutId = setTimeout(function() {
            // if 3000 ms have passed since the last packet we assume we have processed them all and can launch MS Word
            self.timeOutId = undefined;
            self.benchmarking = false;
            var now = new Date().getTime();
            var elapsed = now - self.startTime - self.timeoutInterval;
            self.onEndBenchmarkCallback(elapsed);
            var message = {
                "type": wdi.BUS_TYPES.killApplicationDoNotUseInProductionEver,
                "application": "EXCEL.EXE"
            };
            self.busConnection.send(message);
        }, this.timeoutInterval);
    },

    setStartTime: function() {
        if (this.timeOutId !== undefined) {
            clearTimeout(this.timeOutId);
        }
    },

    launchApp: function(busConnection, onEndBenchmarkCallback) {
        this.busConnection = busConnection;
        wdi.IntegrationBenchmark.benchmarking = true;
        wdi.IntegrationBenchmark.setStartTime();
        this.onEndBenchmarkCallback = onEndBenchmarkCallback;
        this.startTime = new Date().getTime();
        var message = {
            "type": wdi.BUS_TYPES.launchApplication,
            "file": "c:\\Users\\eyeos\\Desktop\\test.xlsx"
        };
        this.busConnection.send(message);
    }
};
