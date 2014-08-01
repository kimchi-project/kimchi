/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2014
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * pub/sub
 * Usage:
 *   Publish - kimchi.topic('eventname').publish(params);
 *   Subscribe - kimchi.topic('eventname').subscribe(listener);
 *   Unsubscribe - kimchi.topic('eventname').unsubscribe(listener);
 */
kimchi.topic = (function() {

    var topics = {};

    return function( id ) {
        var callbacks,
            method,
            topic = id && topics[ id ];

        if ( !topic ) {
            callbacks = jQuery.Callbacks();
            topic = {
                publish: callbacks.fire,
                subscribe: callbacks.add,
                unsubscribe: callbacks.remove
            };
            if ( id ) {
                topics[ id ] = topic;
            }
        }
        return topic;
    };
})();
