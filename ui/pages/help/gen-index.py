#!/usr/bin/python
#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
#
# Authors:
#  Aline Manera <alinefm@linux.vnet.ibm.com>
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

import glob
import libxml2


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
    pages = {}
    files = sorted(glob.glob('*.dita'))
    for f in files:
        with open(f) as fd:
            xml = fd.read()
            doc = libxml2.parseDoc(xml)
            node = doc.xpathEval('/cshelp/title')[0]
            name = node.children.content
            pages[f.replace('.dita', '.html')] = name
            doc.freeDoc()

    with open('index.html', 'w') as fd:
        fd.write(HTML_HEAD)
        for page, name in pages.iteritems():
            html = '  <a href="/help/%s">%s</a><br />\n'
            fd.write(html % (page, name))
        fd.write(HTML_TAIL)


if __name__ == '__main__':
    main()
