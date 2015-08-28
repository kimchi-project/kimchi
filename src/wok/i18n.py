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
    "WOKAPI0002E": _("Delete is not allowed for %(resource)s"),
    "WOKAPI0003E": _("%(resource)s does not implement update method"),
    "WOKAPI0005E": _("Create is not allowed for %(resource)s"),
    "WOKAPI0006E": _("Unable to parse JSON request"),
    "WOKAPI0007E": _("This API only supports JSON"),
    "WOKAPI0008E": _("Parameters does not match requirement in schema: %(err)s"),
    "WOKAPI0009E": _("You don't have permission to perform this operation."),

    "WOKASYNC0001E": _("Datastore is not initiated in the model object."),
    "WOKASYNC0002E": _("Unable to start task due error: %(err)s"),

    "WOKAUTH0001E": _("Authentication failed for user '%(username)s'. [Error code: %(code)s]"),
    "WOKAUTH0002E": _("You are not authorized to access Kimchi"),
    "WOKAUTH0003E": _("Specify %(item)s to login into Kimchi"),
    "WOKAUTH0005E": _("Invalid LDAP configuration: %(item)s : %(value)s"),

    "WOKOBJST0001E": _("Unable to find %(item)s in datastore"),

    "WOKUTILS0001E": _("Invalid URI %(uri)s"),
    "WOKUTILS0002E": _("Timeout while running command '%(cmd)s' after %(seconds)s seconds"),
    "WOKUTILS0004E": _("Invalid data value '%(value)s'"),
    "WOKUTILS0005E": _("Invalid data unit '%(unit)s'"),
}
