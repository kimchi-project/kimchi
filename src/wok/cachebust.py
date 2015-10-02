#
# Project Wok
#
# Copyright IBM, Corp. 2013-2015
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import os


from wok.config import paths, PluginPaths


def href(url, plugin=None):
    if plugin is None:
        basePath = paths.ui_dir
    else:
        basePath = PluginPaths(plugin).ui_dir

    # for error.html, url is absolute path
    f = os.path.join(basePath, url.lstrip("/"))
    mtime = os.path.getmtime(f)
    return "%s?cacheBust=%s" % (url, mtime)
