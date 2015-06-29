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

man_MANS = docs/kimchid.8

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


PEP8_BLACKLIST = *src/kimchi/config.py,*src/kimchi/i18n.py,*tests/test_config.py

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
	$(PEP8) --filename '*.py,*.py.in' --exclude="$(PEP8_BLACKLIST)" .


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
	mkdir -p $(DESTDIR)/var/lib/kimchi/debugreports
	mkdir -p $(DESTDIR)/var/lib/kimchi/screenshots
	mkdir -p $(DESTDIR)/var/lib/kimchi/vnc-tokens
	mkdir -p $(DESTDIR)/var/lib/kimchi/isos
	touch $(DESTDIR)/var/lib/kimchi/objectstore
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
	@if test -d "$(systemdsystemunitdir)" ; then \
		mkdir -p $(DESTDIR)/$(systemdsystemunitdir); \
		$(INSTALL_DATA) contrib/kimchid.service.fedora $(DESTDIR)/$(systemdsystemunitdir)/kimchid.service; \
	else \
		mkdir -p $(DESTDIR)/etc/init.d/; \
		$(INSTALL_DATA) contrib/kimchid.sysvinit $(DESTDIR)/etc/init.d/kimchid; \
		chmod +x $(DESTDIR)/etc/init.d/kimchid; \
    fi; \
	if test -d /usr/lib/firewalld/services/; then \
		mkdir -p $(DESTDIR)/usr/lib/firewalld/services/; \
		$(INSTALL_DATA) src/firewalld.xml $(DESTDIR)/usr/lib/firewalld/services/kimchid.xml; \
	fi; \
	mkdir -p $(DESTDIR)/var/lib/kimchi/{debugreports,screenshots,vnc-tokens,isos}
	touch $(DESTDIR)/var/lib/kimchi/objectstore
	mkdir -p $(DESTDIR)/var/log/kimchi/
	touch $(DESTDIR)/var/log/kimchi/kimchi-access.log
	touch $(DESTDIR)/var/log/kimchi/kimchi-error.log
	mkdir -p $(DESTDIR)/etc/kimchi/
	$(INSTALL_DATA) src/dhparams.pem $(DESTDIR)/etc/kimchi/dhparams.pem
	touch $(DESTDIR)/etc/nginx/conf.d/kimchi.conf

uninstall-local:
	@if test -f $(systemdsystemunitdir)/kimchid.service; then \
		$(RM) $(DESTDIR)/$(systemdsystemunitdir)/kimchid.service; \
	elif test -f /etc/init.d/kimchid; then \
		$(RM) $(DESTDIR)/etc/init.d/kimchid; \
		$(RM) $(DESTDIR)/etc/init/kimchi.conf; \
	fi; \
	if test -d /usr/lib/firewalld/services/; then \
		$(RM) $(DESTDIR)/usr/lib/firewalld/services/kimchid.xml; \
	fi; \
	$(RM) -rf $(DESTDIR)/var/lib/kimchi
	$(RM) -rf $(DESTDIR)/var/log/kimchi
	$(RM) -rf $(DESTDIR)/etc/kimchi
	$(RM) $(DESTDIR)/etc/nginx/conf.d/kimchi.conf

VERSION:
	@if test -d .git; then                                \
		git describe --abbrev=0 > $@;                     \
	fi

.PHONY: deb install-deb rpm fedora-rpm suse-rpm ChangeLog VERSION


clean-local:
	rm -rf mo rpm

CLEANFILES = kimchi.spec `find "$(top_srcdir)" -type f -name "*.pyc" -print`
