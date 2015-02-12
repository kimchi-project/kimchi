#!/usr/bin/env python2
#
# Project Kimchi
#
# Copyright IBM, Corp. 2014-2015
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

import lxml.etree as ET
import sys


HTML_HEAD = """
<html>
<head>
  <title>Kimchi Help</title>
</head>
<body>
<h1>Kimchi Help</h1>
"""

HTML_TAIL = """
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        sys.exit("Missing input files")

    input_files = sys.argv[1:]

    pages = {}

    for f in sorted(input_files):
        with open(f) as fd:
            xml = fd.read()
            doc = ET.fromstring(xml)
            name = doc.xpath('./title')[0].text
            pages[f.replace('.dita', '.html')] = name.encode('utf-8')

    print HTML_HEAD
    for page, name in pages.iteritems():
        html = '  <a href="/help/%s">%s</a><br />\n'
        print html % (page, name)
    print HTML_TAIL


if __name__ == '__main__':
    main()
