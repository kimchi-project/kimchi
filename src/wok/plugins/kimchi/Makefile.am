#
# Kimchi
#
# Copyright IBM Corp, 2013
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

SUBDIRS = contrib control distros.d docs model po tests ui xmlutils

kimchi_PYTHON = $(filter-out config.py, $(wildcard *.py))

nodist_kimchi_PYTHON = config.py

if WITH_SPICE
WITH_SPICE=yes
else
WITH_SPICE=no
endif

wokdir = $(pythondir)/wok
kimchidir = $(pythondir)/wok/plugins/kimchi

confdir = $(sysconfdir)/wok/plugins.d
dist_conf_DATA = kimchi.conf template.conf

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
		ln -sf ../../../po/$$L.gmo $$dir/kimchi.mo ;   \
	done < po/LINGUAS

do_substitution = \
	sed -e 's,[@]prefix[@],$(prefix),g'             \
	-e 's,[@]datadir[@],$(datadir),g'               \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g'         \
	-e 's,[@]localstatedir[@],$(localstatedir),g'   \
	-e 's,[@]pkgdatadir[@],$(pkgdatadir),g'         \
	-e 's,[@]wokdir[@],$(wokdir),g'           \
	-e 's,[@]kimchidir[@],$(kimchidir),g'           \
	-e 's,[@]kimchiversion[@],$(PACKAGE_VERSION),g' \
	-e 's,[@]kimchirelease[@],$(PACKAGE_RELEASE),g' \
	-e 's,[@]withspice[@],$(WITH_SPICE),g'

config.py: config.py.in Makefile
	$(do_substitution) < $(srcdir)/config.py.in > config.py


#
# Packaging helpers
#

install-deb: install
	cp -R $(top_srcdir)/contrib/DEBIAN $(DESTDIR)/
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/
	touch $(DESTDIR)/$(localstatedir)/lib/wok/objectstore
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/plugins/kimchi/vnc-tokens
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/plugins/kimchi/debugreports
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/plugins/kimchi/screenshots
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/plugins/kimchi/isos


deb: contrib/make-deb.sh
	$(top_srcdir)/contrib/make-deb.sh

kimchi.spec: contrib/kimchi.spec.fedora contrib/kimchi.spec.suse
	@if test -e /etc/redhat-release; then                   \
		ln -sf contrib/kimchi.spec.fedora $@ ;              \
	elif test -e /etc/SuSE-release; then                    \
		ln -sf contrib/kimchi.spec.suse $@ ;                \
	else                                                    \
		echo "Unable to select a spec file for RPM build" ; \
		/bin/false ;                                        \
	fi

rpm: dist kimchi.spec
	$(MKDIR_P) rpm/BUILD rpm/RPMS rpm/SOURCES rpm/SPECS rpm/SRPMS
	cp $(top_srcdir)/kimchi.spec rpm/SPECS/kimchi.spec
	cp $(DIST_ARCHIVES) rpm/SOURCES
	rpmbuild -ba --define "_topdir `pwd`/rpm" rpm/SPECS/kimchi.spec

fedora-rpm: contrib/kimchi.spec.fedora
	ln -sf contrib/kimchi.spec.fedora kimchi.spec
	$(MAKE) rpm

suse-rpm: contrib/kimchi.spec.suse
	ln -sf contrib/kimchi.spec.suse kimchi.spec
	$(MAKE) rpm

ChangeLog:
	@if test -d .git; then                                   \
		$(top_srcdir)/build-aux/genChangelog --release > $@; \
	fi

install-data-local:
	$(MKDIR_P) $(DESTDIR)/$(localstatedir)/lib/wok/
	touch $(DESTDIR)/$(localstatedir)/lib/wok/objectstore
	$(MKDIR_P) $(DESTDIR)$(kimchidir)
	$(INSTALL_DATA) API.json $(DESTDIR)$(kimchidir)/API.json
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/plugins/kimchi/vnc-tokens
	mkdir -p $(DESTDIR)/$(localstatedir)/lib/wok/plugins/kimchi/{debugreports,isos,screenshots}

uninstall-local:
	$(RM) $(DESTDIR)$(kimchidir)/API.json
	$(RM) -rf $(DESTDIR)/$(localstatedir)/lib/wok/plugins/kimchi

VERSION:
	@if test -d .git; then                                \
		git describe --abbrev=0 > $@;                     \
	fi

.PHONY: deb install-deb rpm fedora-rpm suse-rpm ChangeLog VERSION


clean-local:
	rm -rf mo rpm

BUILT_SOURCES = config.py
CLEANFILES = config.py kimchi.spec `find "$(top_srcdir)" -type f -name "*.pyc" -print`
