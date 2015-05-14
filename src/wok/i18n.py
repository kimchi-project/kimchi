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

import gettext

_ = gettext.gettext


messages = {
    "KCHAPI0002E": _("Delete is not allowed for %(resource)s"),
    "KCHAPI0003E": _("%(resource)s does not implement update method"),
    "KCHAPI0005E": _("Create is not allowed for %(resource)s"),
    "KCHAPI0006E": _("Unable to parse JSON request"),
    "KCHAPI0007E": _("This API only supports JSON"),
    "KCHAPI0008E": _("Parameters does not match requirement in schema: %(err)s"),
    "KCHAPI0009E": _("You don't have permission to perform this operation."),

    "KCHASYNC0001E": _("Datastore is not initiated in the model object."),
    "KCHASYNC0002E": _("Unable to start task due error: %(err)s"),

    "KCHAUTH0001E": _("Authentication failed for user '%(username)s'. [Error code: %(code)s]"),
    "KCHAUTH0002E": _("You are not authorized to access Kimchi"),
    "KCHAUTH0003E": _("Specify %(item)s to login into Kimchi"),
    "KCHAUTH0005E": _("Invalid LDAP configuration: %(item)s : %(value)s"),

    "KCHOBJST0001E": _("Unable to find %(item)s in datastore"),

    "KCHUTILS0002E": _("Timeout while running command '%(cmd)s' after %(seconds)s seconds"),
    "KCHUTILS0004E": _("Invalid data value '%(value)s'"),
    "KCHUTILS0005E": _("Invalid data unit '%(unit)s'"),
}
