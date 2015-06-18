#
# Kimchi
#
# Copyright IBM Corp, 2013-2015
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

SUBDIRS = kimchi distros.d nginx

EXTRA_DIST = kimchid.in \
	kimchi.conf.in \
	firewalld.xml \
	$(NULL)

bin_SCRIPTS = kimchid

confdir = $(sysconfdir)/kimchi
dist_conf_DATA = kimchi.conf template.conf

BUILT_SOURCES = kimchi.conf

do_substitution = \
	sed -e 's,[@]pythondir[@],$(pythondir),g'     \
	-e 's,[@]localstatedir[@],$(localstatedir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g'             \
	-e 's,[@]VERSION[@],$(VERSION),g'


kimchid: kimchid.in Makefile
	$(do_substitution) < $(srcdir)/kimchid.in > kimchid
	chmod +x kimchid

kimchi.conf: kimchi.conf.in Makefile
	$(do_substitution) < kimchi.conf.in > kimchi.conf

# Generate unique Diffie-Hellman group with 2048-bit
all-local: dhparams.pem

dhparams.pem:
	openssl dhparam -out dhparams.pem 2048

CLEANFILES = $(bin_SCRIPTS) $(BUILT_SOURCES) dhparams.pem
