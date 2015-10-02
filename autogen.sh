#!/bin/bash
#
# Project Wok
#
# Copyright IBM Corp, 2013-2015
#
# Code derived from Project Kimchi
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

aclocal
automake --add-missing
autoreconf

if [ ! -f "configure" ]; then
    echo "Failed to generate configure script.  Check to make sure autoconf, "
    echo "automake, and other build dependencies are properly installed."
    exit 1
fi

if [ "x$1" == "x--system" ]; then
    ./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var
else
   if [ $# -gt 0 ]; then
        ./configure $@
   else
        ./configure --prefix=/usr/local
   fi
fi
