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

SUBDIRS = src ui docs contrib tests po config plugins

if FONTS
DEFINE_FONTS = --define "with_fonts 1"
else
DEFINE_FONTS = --define "with_fonts 0"
endif

AUTOMAKE_OPTIONS = foreign

ACLOCAL_AMFLAGS = --install -I m4

EXTRA_DIST = \
	config.rpath \
	autogen.sh \
	COPYING.ASL2 \
	COPYING.LGPL \
	CONTRIBUTE.md \
	VERSION \
	build-aux/pkg-version \
	$(NULL)


# When fixing a file to conform with pep8, add it to the WL here.
# So it will be checked from now on.
PEP8_WHITELIST = \
	plugins/__init__.py \
	plugins/sample/__init__.py \
	plugins/sample/model.py \
	src/kimchid.in \
	src/kimchi/asynctask.py \
	src/kimchi/auth.py \
	src/kimchi/cachebust.py \
	src/kimchi/config.py.in \
	src/kimchi/control/*.py \
	src/kimchi/control/vm/*.py \
	src/kimchi/disks.py \
	src/kimchi/distroloader.py \
	src/kimchi/exception.py \
	src/kimchi/featuretests.py \
	src/kimchi/imageinfo.py \
	src/kimchi/iscsi.py \
	src/kimchi/isoinfo.py \
	src/kimchi/kvmusertests.py \
	src/kimchi/mockmodel.py \
	src/kimchi/model/*.py \
	src/kimchi/objectstore.py \
	src/kimchi/osinfo.py \
	src/kimchi/proxy.py \
	src/kimchi/repositories.py \
	src/kimchi/rollbackcontext.py \
	src/kimchi/root.py \
	src/kimchi/scan.py \
	src/kimchi/server.py \
	src/kimchi/swupdate.py \
	src/kimchi/template.py \
	src/kimchi/utils.py \
	src/kimchi/vmtemplate.py \
	tests/test_config.py.in \
	tests/test_mockmodel.py \
	tests/test_model.py \
	tests/test_osinfo.py \
	tests/test_plugin.py \
	tests/test_rest.py \
	tests/test_rollbackcontext.py \
	tests/test_storagepool.py \
	tests/utils.py \
	$(NULL)

SKIP_PYFLAKES_ERR = "\./src/kimchi/websocket\.py"

I18N_FILES = plugins/*/i18n.py \
	src/kimchi/i18n.py \
	$(NULL)

check-local:
	PYTHONPATH=src contrib/check_i18n.py $(I18N_FILES)
	find . -path './.git' -prune -type f -o \
		-name '*.py' -o -name '*.py.in'  | xargs $(PYFLAKES) | \
		grep -w -v $(SKIP_PYFLAKES_ERR) | \
		while read LINE; do echo "$$LINE"; false; done

	$(PEP8) --version
	$(PEP8) --filename '*.py,*.py.in' $(PEP8_WHITELIST)


# Link built mo files in the source tree to enable use of translations from
# within the source tree
all-local:
	while read L && test -n "$$L"; do                  \
		dir=mo/$$L/LC_MESSAGES ;                       \
		$(MKDIR_P) $$dir ;                             \
		ln -sf ../../../po/$$L.gmo $$dir/kimchi.mo ;   \
	done < po/LINGUAS

#
# Packaging helpers
#

install-deb: install
	cp -R $(top_srcdir)/contrib/DEBIAN $(DESTDIR)/
	$(MKDIR_P) $(DESTDIR)/etc/init
	$(MKDIR_P) $(DESTDIR)/usr/lib/firewalld/services
	cp -R $(top_srcdir)/contrib/kimchid-upstart.conf.debian \
		$(DESTDIR)/etc/init/kimchid.conf
	cp -R $(top_srcdir)/src/firewalld.xml \
		$(DESTDIR)/usr/lib/firewalld/services/kimchid.xml


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
	rpmbuild -ba $(DEFINE_FONTS) --define "_topdir `pwd`/rpm" rpm/SPECS/kimchi.spec

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

VERSION:
	@if test -d .git; then                                \
		git describe --abbrev=0 > $@;                     \
	fi

.PHONY: deb install-deb rpm fedora-rpm suse-rpm ChangeLog VERSION

clean-local:
	rm -rf mo rpm

CLEANFILES = kimchi.spec
