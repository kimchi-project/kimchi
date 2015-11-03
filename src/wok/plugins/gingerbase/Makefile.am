#
# Ginger Base
#
# Copyright IBM Corp, 2015
#
# Code derived from Project Kimchi
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

SUBDIRS = contrib control docs model po tests ui

gingerbase_PYTHON = $(filter-out config.py, $(wildcard *.py))

nodist_gingerbase_PYTHON = config.py

wokdir = $(pythondir)/wok
gingerbasedir = $(pythondir)/wok/plugins/gingerbase

confdir = $(sysconfdir)/wok/plugins.d
dist_conf_DATA = gingerbase.conf

name=ginger-base
distdir=$(name)-$(PACKAGE_VERSION)

AUTOMAKE_OPTIONS = foreign

ACLOCAL_AMFLAGS = --install -I m4

EXTRA_DIST = \
	config.rpath \
	API.json \
	autogen.sh \
	COPYING.ASL2 \
	COPYING.LGPL \
	CONTRIBUTE.md \
	VERSION \
	build-aux/pkg-version \
	config.py.in \
	$(NULL)


PEP8_BLACKLIST = *config.py,*i18n.py,*tests/test_config.py

I18N_FILES = ./i18n.py \
	$(NULL)

check-local:
	contrib/check_i18n.py $(I18N_FILES)
	find . -path './.git' -prune -type f -o \
		-name '*.py' -o -name '*.py.in'  | xargs $(PYFLAKES) | \
		while read LINE; do echo "$$LINE"; false; done

	$(PEP8) --version
	$(PEP8) --filename '*.py,*.py.in' --exclude="$(PEP8_BLACKLIST)" .


# Link built mo files in the source tree to enable use of translations from
# within the source tree
all-local:
	while read L && test -n "$$L"; do                  \
		dir=mo/$$L/LC_MESSAGES ;                       \
		$(MKDIR_P) $$dir ;                             \
		ln -sf ../../../po/$$L.gmo $$dir/gingerbase.mo ;   \
	done < po/LINGUAS

do_substitution = \
	sed -e 's,[@]prefix[@],$(prefix),g'             \
	-e 's,[@]datadir[@],$(datadir),g'               \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g'         \
	-e 's,[@]localstatedir[@],$(localstatedir),g'   \
	-e 's,[@]pkgdatadir[@],$(pkgdatadir),g'         \
	-e 's,[@]wokdir[@],$(wokdir),g'           \
	-e 's,[@]gingerbasedir[@],$(gingerbasedir),g'           \
	-e 's,[@]gingerbaseversion[@],$(PACKAGE_VERSION),g' \
	-e 's,[@]gingerbaserelease[@],$(PACKAGE_RELEASE),g' \
	-e 's,[@]withspice[@],$(WITH_SPICE),g'

config.py: config.py.in Makefile
	$(do_substitution) < $(srcdir)/config.py.in > config.py


#
# Packaging helpers
#

install-deb: install
	cp -R $(top_srcdir)/contrib/DEBIAN $(DESTDIR)/
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/gingerbase
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/gingerbase/debugreports


deb: contrib/make-deb.sh
	$(top_srcdir)/contrib/make-deb.sh

gingerbase.spec: contrib/gingerbase.spec.fedora contrib/gingerbase.spec.suse
	@if test -e /etc/redhat-release; then                   \
		ln -sf contrib/gingerbase.spec.fedora $@ ;              \
	elif test -e /etc/SuSE-release; then                    \
		ln -sf contrib/gingerbase.spec.suse $@ ;                \
	else                                                    \
		echo "Unable to select a spec file for RPM build" ; \
		/bin/false ;                                        \
	fi

rpm: dist gingerbase.spec
	$(MKDIR_P) rpm/BUILD rpm/RPMS rpm/SOURCES rpm/SPECS rpm/SRPMS
	cp $(top_srcdir)/gingerbase.spec rpm/SPECS/gingerbase.spec
	cp $(DIST_ARCHIVES) rpm/SOURCES
	rpmbuild -ba --define "_topdir `pwd`/rpm" rpm/SPECS/gingerbase.spec

fedora-rpm: contrib/gingerbase.spec.fedora
	ln -sf contrib/gingerbase.spec.fedora gingerbase.spec
	$(MAKE) rpm

suse-rpm: contrib/gingerbase.spec.suse
	ln -sf contrib/gingerbase.spec.suse gingerbase.spec
	$(MAKE) rpm

ChangeLog:
	@if test -d .git; then                                   \
		$(top_srcdir)/build-aux/genChangelog --release > $@; \
	fi

install-data-local:
	$(MKDIR_P) $(DESTDIR)/$(localstatedir)/lib/gingerbase/
	$(MKDIR_P) $(DESTDIR)$(gingerbasedir)
	$(INSTALL_DATA) API.json $(DESTDIR)$(gingerbasedir)/API.json
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/gingerbase/debugreports

uninstall-local:
	@if test -f $(DESTDIR)/etc/systemd/system/wokd.service.d/gingerbase.conf; then \
		$(RM) $(DESTDIR)/etc/systemd/system/wokd.service.d/gingerbase.conf; \
	fi; \
	$(RM) $(DESTDIR)$(gingerbasedir)/API.json
	$(RM) -rf $(DESTDIR)/$(localstatedir)/lib/gingerbase/debugreports

VERSION:
	@if test -d .git; then                                \
		git describe --abbrev=0 > $@;                     \
	fi

.PHONY: deb install-deb rpm fedora-rpm suse-rpm ChangeLog VERSION


clean-local:
	rm -rf mo rpm

BUILT_SOURCES = config.py
CLEANFILES = config.py gingerbase.spec `find "$(top_srcdir)" -type f -name "*.pyc" -print`
