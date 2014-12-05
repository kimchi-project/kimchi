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

SUBDIRS = DEBIAN

EXTRA_DIST = \
	check_i18n.py \
	kimchid.sysvinit \
	kimchid.service.fedora \
	kimchi.spec.fedora.in \
	kimchid-upstart.conf.debian \
	kimchid-upstart.conf.fedora \
	make-deb.sh.in \
	$(NULL)

make-deb.sh: make-deb.sh.in $(top_builddir)/config.status
	$(AM_V_GEN)sed						\
	    -e 's|[@]PACKAGE_VERSION[@]|$(PACKAGE_VERSION)|g'	\
	    -e 's|[@]PACKAGE_RELEASE[@]|$(PACKAGE_RELEASE)|g'	\
	    < $< > $@-t &&					\
	    chmod a+x $@-t &&					\
	    mv $@-t $@
BUILT_SOURCES = make-deb.sh

CLEANFILES = kimchi.spec.fedora kimchi.spec.suse kimchi.spec make-deb.sh
