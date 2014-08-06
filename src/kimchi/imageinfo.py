#
# Kimchi
#
# Copyright IBM Corp, 2014
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
import sys
import guestfs

from kimchi.exception import ImageFormatError


def probe_image(image_path):
    g = guestfs.GuestFS(python_return_dict=True)
    g.add_drive_opts(image_path, readonly=1)
    g.launch()
    if not os.access(image_path, os.R_OK):
        raise ImageFormatError("KCHIMG0003E", {'filename': image_path})
    try:
        roots = g.inspect_os()
    except:
        raise ImageFormatError("KCHIMG0001E")
    if len(roots) == 0:
        raise ImageFormatError("KCHIMG0002E")

    for root in roots:
        version = "%d.%d" % (g.inspect_get_major_version(root),
                             g.inspect_get_minor_version(root))
        distro = "%s" % (g.inspect_get_distro(root))

    return (distro, version)


if __name__ == '__main__':
    print probe_image(sys.argv[1])
