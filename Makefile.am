#
# Kimchi
#
# Copyright IBM Corp, 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
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
	src/kimchi/asynctask.py \
	src/kimchi/auth.py \
	src/kimchi/cachebust.py \
	src/kimchi/config.py.in \
	src/kimchi/disks.py \
	src/kimchi/featuretests.py \
	src/kimchi/rollbackcontext.py \
	src/kimchi/root.py \
	src/kimchi/server.py \
	src/kimchi/control/*.py \
	tests/test_mockmodel.py \
	tests/test_model.py \
	tests/test_plugin.py \
	tests/test_rest.py \
	tests/utils.py \
	$(NULL)

check-local:
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
	cp -R $(top_srcdir)/contrib/kimchid-upstart.conf.debian \
		$(DESTDIR)/etc/init/kimchid.conf


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

VERSION:
	@if test -d .git; then                                \
		git describe --abbrev=0 > $@;                     \
	fi

.PHONY: deb install-deb rpm fedora-rpm suse-rpm ChangeLog VERSION

clean-local:
	rm -rf mo rpm

CLEANFILES = kimchi.spec
