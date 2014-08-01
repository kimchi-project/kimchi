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

import gettext

_ = gettext.gettext


messages = {
    "SPAPI0001E": _("Unkown parameter specified %(value)s"),
    "SPAPI0002E": _("The specified value %(value)s is not a positive number"),

    "SPCIRC0002E": _("Circle %(name)s does not exist"),
    "SPCIRC0003E": _("Specify name and radius to create a Circle"),
    "SPCIRC0004E": _("Circle name must be a string"),
    "SPCIRC0005E": _("Circle radius must be a positive number"),

    "SPRET0001E": _("Rectangle %(name)s already exists"),
    "SPRET0002E": _("Rectangle %(name)s does not exist"),
    "SPRET0003E": _("Specify name, length and width to create a Rectangle"),
    "SPRET0004E": _("Rectangle name must be a string"),
    "SPRET0005E": _("Rectangle length must be a positive number"),
    "SPRET0006E": _("Rectangle width must be a positive number"),
}
