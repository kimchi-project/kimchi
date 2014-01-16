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

EXTRA_DIST = \
	Makefile.am \
	run_tests.sh.in \
	iso_gen.py   \
	test_exception.py \
	test_mockmodel.py \
	test_model.py \
	test_networkxml.py \
	test_osinfo.py \
	test_plugin.py \
	test_rest.py \
	test_rollbackcontext.py \
	test_server.py \
	test_storagepool.py \
	test_vmtemplate.py \
	utils.py \
	$(NULL)

noinst_SCRIPTS = run_tests.sh

do_substitution = \
	sed -e 's,[@]HAVE_PYMOD_UNITTEST[@],$(HAVE_PYMOD_UNITTEST),g' \
	-e 's,[@]PYTHON_VERSION[@],$(PYTHON_VERSION),g'


run_tests.sh: run_tests.sh.in Makefile
	$(do_substitution) < $(srcdir)/run_tests.sh.in > run_tests.sh
	chmod +x run_tests.sh


check-local:
	$(MKDIR_P) $(top_srcdir)/data/screenshots
	./run_tests.sh

CLEANFILES = run_tests.sh
