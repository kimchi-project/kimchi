#!/usr/bin/python
#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import imp
import os
import re
import sys


# Match all conversion specifier with mapping key
PATTERN = re.compile(r'''%\([^)]+\)  # Mapping key
                         [#0\-+]?  # Conversion flags (optional)
                         (\d+|\*)?  # Minimum field width (optional)
                         (\.(\d+|\*))?  # Precision (optional)
                         [lLh]?  # Length modifier (optional)
                         [cdeEfFgGioursxX%]  # Conversion type''',
                     re.VERBOSE)
BAD_PATTERN = re.compile(r"%\([^)]*?\)")


def load_i18n_module(i18nfile):
    path = os.path.dirname(i18nfile)
    mname = i18nfile.replace("/", "_").rstrip(".py")
    mobj = imp.find_module("i18n", [path])
    return imp.load_module(mname, *mobj)


def check_string_formatting(messages):
    for k, v in messages.iteritems():
        if BAD_PATTERN.findall(PATTERN.sub(" ", v)):
            print "bad i18n string formatting:"
            print "  %s: %s" % (k, v)
            exit(1)


def main():
    print "Checking for invalid i18n string..."
    for f in sys.argv[1:]:
        messages = load_i18n_module(f).messages
        check_string_formatting(messages)
    print "Checking for invalid i18n string successfully"


if __name__ == '__main__':
    main()
