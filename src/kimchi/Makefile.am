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

SUBDIRS = control model xmlutils

kimchi_PYTHON = $(filter-out config.py, $(wildcard *.py))

nodist_kimchi_PYTHON = config.py

EXTRA_DIST = \
	API.json \
	config.py.in

if WITH_SPICE
WITH_SPICE=yes
else
WITH_SPICE=no
endif

kimchidir = $(pythondir)/kimchi

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(kimchidir)
	$(INSTALL_DATA) API.json $(DESTDIR)$(kimchidir)/API.json

uninstall-local:
	$(RM) $(DESTDIR)$(kimchidir)/API.json

do_substitution = \
	sed -e 's,[@]prefix[@],$(prefix),g'             \
	-e 's,[@]datadir[@],$(datadir),g'               \
	-e 's,[@]sysconfdir[@],$(sysconfdir),g'         \
	-e 's,[@]localstatedir[@],$(localstatedir),g'   \
	-e 's,[@]pkgdatadir[@],$(pkgdatadir),g'         \
	-e 's,[@]kimchidir[@],$(kimchidir),g'           \
	-e 's,[@]kimchiversion[@],$(PACKAGE_VERSION),g' \
	-e 's,[@]kimchirelease[@],$(PACKAGE_RELEASE),g' \
	-e 's,[@]withspice[@],$(WITH_SPICE),g'


config.py: config.py.in Makefile
	$(do_substitution) < $(srcdir)/config.py.in > config.py

BUILT_SOURCES = config.py
CLEANFILES = config.py
