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

EXTRA_DIST = \
	Makefile.am \
	run_tests.sh.in \
	test_config.py.in \
	$(filter-out test_config.py, $(wildcard *.py)) \
	$(NULL)

noinst_SCRIPTS = run_tests.sh

do_substitution = \
	sed -e 's,[@]HAVE_PYMOD_UNITTEST[@],$(HAVE_PYMOD_UNITTEST),g' \
	-e 's,[@]prefix[@],$(prefix),g' \
	-e 's,[@]datadir[@],$(datadir),g' \
	-e 's,[@]PYTHON_VERSION[@],$(PYTHON_VERSION),g' \
	-e 's,[@]kimchidir[@],$(pythondir)/kimchi,g' \
	-e 's,[@]pkgdatadir[@],$(pkgdatadir),g'


run_tests.sh: run_tests.sh.in Makefile
	$(do_substitution) < $(srcdir)/run_tests.sh.in > run_tests.sh
	chmod +x run_tests.sh

test_config.py: test_config.py.in Makefile
	$(do_substitution) < $(srcdir)/test_config.py.in > test_config.py

check-local:
	$(MKDIR_P) $(top_srcdir)/data/screenshots
	./run_tests.sh

BUILT_SOURCES = test_config.py
CLEANFILES = run_tests.sh test_config.py
