#
# Ginger Base
#
# Copyright IBM, Corp. 2015
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

EXTRA_DIST = src

jsdir = $(datadir)/wok/plugins/gingerbase/ui/js

dist_js_DATA = gingerbase.min.js $(filter-out gingerbase.min.js, $(wildcard *.js))

gingerbase.min.js: src/*.js
	cat $(sort $^) > $@

CLEANFILES = gingerbase.min.js
