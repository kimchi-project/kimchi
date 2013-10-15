#!/bin/bash

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
