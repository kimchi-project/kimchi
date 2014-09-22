# Copyright IBM Corp, 2014
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

SUBDIRS = zh_CN it_IT en_US zh_TW pt_BR ja_JP ru_RU ko_KR fr_FR de_DE es_ES

DITA_HTML_FILES = $(patsubst %.dita,%.html,$(wildcard */*.dita))
HTML_FILES = $(if $(DITA_HTML_FILES), $(DITA_HTML_FILES), $(wildcard */*.html))
DITA_XSL_FILE = dita-help.xsl

EXTRA_DIST = gen-index.py\
			 $(DITA_XSL_FILE)
helpdir = $(datadir)/kimchi/ui/pages/help

dist_help_DATA = kimchi.css

all: $(HTML_FILES) $(wildcard */*.dita)
	@$(foreach dir, $(dir $(wildcard */)), $(shell pwd)/gen-index.py $(wildcard $(dir)*.dita) > $(dir)/index.html;)

%.html: %.dita $(DITA_XSL_FILE)
	xsltproc -o $@ $(DITA_XSL_FILE) $<

CLEANFILES = $(HTML_FILES)
