#
# Kimchi
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

import json
import os
import sys
import guestfs

from kimchi.exception import ImageFormatError, InvalidParameter, TimeoutExpired
from kimchi.utils import run_command, kimchi_log


def probe_img_info(path):
    cmd = ["qemu-img", "info", "--output=json", path]
    info = dict()
    try:
        out = run_command(cmd, 10)[0]
    except TimeoutExpired:
        kimchi_log.warning("Cannot decide format of base img %s", path)
        return None

    info = json.loads(out)
    info['virtual-size'] = info['virtual-size'] >> 30
    info['actual-size'] = info['actual-size'] >> 30
    return info


def probe_image(image_path):
    if not os.path.isfile(image_path):
        raise InvalidParameter("KCHIMG0004E", {'filename': image_path})

    if not os.access(image_path, os.R_OK):
        raise ImageFormatError("KCHIMG0003E", {'filename': image_path})

    g = guestfs.GuestFS(python_return_dict=True)
    g.add_drive_opts(image_path, readonly=1)
    g.launch()

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
