#
# Kimchi
#
# Copyright IBM Corp, 2013-2016
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

docdir = $(datadir)/kimchi/doc

EXTRA_DIST = \
	deps.md.tmpl \
	$(NULL)

all:
	@for os_distro in ubuntu fedora opensuse-leap; do \
		case $$os_distro in \
			ubuntu) \
		    	PKG_MGNT_TOOL="apt install -y"; \
		    ;; \
		    fedora) \
		    	PKG_MGNT_TOOL="dnf install -y"; \
		    ;; \
		    opensuse-leap) \
		    	PKG_MGNT_TOOL="zypper install -y"; \
		    ;; \
		    *) \
		    	PKG_MGNT_TOOL="error"; \
		    ;; \
		esac; \
		echo $${PKG_MGNT_TOOL}; \
		DEV_DEPS=`grep "^[^#;]" ../$${os_distro}-dev-deps.list` ;\
		RUNTIME_DEPS=`grep "^[^#;]" ../$${os_distro}-runtime-deps.list` ;\
		sed -e "s|[@]DISTRO[@]|$${os_distro^^}|g" \
			-e "s|[@]PKG_MGNT_TOOL[@]|$${PKG_MGNT_TOOL}|g" \
			-e "s|[@]DEV_DEPS[@]|`echo $${DEV_DEPS}`|g" \
			-e "s|[@]RUNTIME_DEPS[@]|`echo $${RUNTIME_DEPS}`|g" deps.md.tmpl > $${os_distro}-deps.md ;\
	done

dist_doc_DATA = $(wildcard *.md) $(wildcard *.png) $(NULL)
