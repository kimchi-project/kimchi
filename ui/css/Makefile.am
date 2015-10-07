#
# Project Wok
#
# Copyright IBM, Corp. 2013-2015
#
# Code derived from Project Kimchi
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

SUBDIRS = fontawesome opensans

EXTRA_DIST = theme-default

cssdir = $(datadir)/wok/ui/css
dist_css_DATA = theme-default.min.css jquery-ui.custom.css wok.css  bootstrap.custom.css bootstrap-select.custom.css

%.css: src/%.scss
	echo "Compiling .scss file $<"
	sassc -s expanded $< $(@:.scss=.css)

theme-default.min.css: theme-default/*.css
	cat $^ > $@

CLEANFILES = theme-default.min.css
