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
	README.md.tmpl \
	$(NULL)

FEDORA_DEV_DEPS=$(shell grep "^[^\#;]" ../fedora-dev-deps.list)
FEDORA_RUNTIME_DEPS=$(shell grep "^[^\#;]" ../fedora-runtime-deps.list)
UBUNTU_DEV_DEPS=$(shell grep "^[^\#;]" ../ubuntu-dev-deps.list)
UBUNTU_RUNTIME_DEPS=$(shell grep "^[^\#;]" ../ubuntu-runtime-deps.list)
OPENSUSE_DEV_DEPS=$(shell grep "^[^\#;]" ../opensuse-leap-dev-deps.list)
OPENSUSE_RUNTIME_DEPS=$(shell grep "^[^\#;]" ../opensuse-leap-runtime-deps.list)

all:
	sed -e "s|[@]FEDORA_DEV_DEPS[@]|$(FEDORA_DEV_DEPS)|g" \
		-e "s|[@]FEDORA_RUNTIME_DEPS[@]|$(FEDORA_RUNTIME_DEPS)|g" \
		-e "s|[@]UBUNTU_DEV_DEPS[@]|`echo $(UBUNTU_DEV_DEPS)`|g" \
		-e "s|[@]UBUNTU_RUNTIME_DEPS[@]|`echo $(UBUNTU_RUNTIME_DEPS)`|g" \
		-e "s|[@]OPENSUSE_DEV_DEPS[@]|`echo $(OPENSUSE_DEV_DEPS)`|g" \
		-e "s|[@]OPENSUSE_RUNTIME_DEPS[@]|`echo $(OPENSUSE_RUNTIME_DEPS)`|g" README.md.tmpl > README.md ;

dist_doc_DATA = $(wildcard *.md) $(wildcard *.png) $(NULL)
