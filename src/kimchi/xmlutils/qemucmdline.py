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

import lxml.etree as ET
from lxml.builder import ElementMaker

QEMU_NAMESPACE = "http://libvirt.org/schemas/domain/qemu/1.0"


def get_qemucmdline_xml(args):
    """
    <qemu:commandline xmlns:qemu="http://libvirt.org/schemas/domain/qemu/1.0">
      <qemu:arg value='-drive'/>
      <qemu:arg value='file=%(path)s,if=none,id=drive-%(bus)s0-1-0,
                readonly=on,format=%(format)s'/>
      <qemu:arg value='-device'/>
      <qemu:arg value='%(bus)s-cd,bus=%(bus)s.1,unit=0,
                drive=drive-%(bus)s0-1-0,id=%(bus)s0-1-0'/>
    </qemu:commandline>
    """
    EM = ElementMaker(namespace=QEMU_NAMESPACE,
                      nsmap={'qemu': QEMU_NAMESPACE})

    root = EM.commandline()
    for opt, value in args.iteritems():
        root.append(EM.arg(value=opt))
        root.append(EM.arg(value=value))

    return ET.tostring(root, encoding='utf-8', pretty_print=True)
