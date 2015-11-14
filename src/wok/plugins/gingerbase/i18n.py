#
# Project Ginger Base
#
# Copyright IBM, Corp. 2015
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

import gettext

_ = gettext.gettext


messages = {
    "GGBAPI0001E": _("Unknown parameter %(value)s"),

    "GGBDR0001E": _("Debug report %(name)s does not exist"),
    "GGBDR0002E": _("Debug report tool not found in system"),
    "GGBDR0003E": _("Unable to create debug report %(name)s. Details: %(err)s."),
    "GGBDR0004E": _("Can not find any debug report with the given name %(name)s"),
    "GGBDR0005E": _("Unable to generate debug report %(name)s. Details: %(err)s"),
    "GGBDR0006E": _("You should give a name for the debug report file."),
    "GGBDR0007E": _("Debug report name must be a string. Only letters, digits, underscore ('_') and "
                    "hyphen ('-') are allowed."),
    "GGBDR0008E": _("The debug report with specified name \"%(name)s\" already exists. Please use another one."),

    "GGBHOST0001E": _("Unable to shutdown host machine as there are running virtual machines"),
    "GGBHOST0002E": _("Unable to reboot host machine as there are running virtual machines"),
    "GGBHOST0003E": _("There may be virtual machines running on the host"),
    "GGBHOST0005E": _("When specifying CPU topology, each element must be an integer greater than zero."),

    "GGBPKGUPD0001E": _("No packages marked for update"),
    "GGBPKGUPD0002E": _("Package %(name)s is not marked to be updated."),
    "GGBPKGUPD0003E": _("Error while getting packages marked to be updated. Details: %(err)s"),
    "GGBPKGUPD0004E": _("There is no compatible package manager for this system."),
    "GGBPKGUPD0005E": _("There is a package manager instance running in the system."),

    "GGBREPOS0001E": _("YUM Repository ID must be one word only string."),
    "GGBREPOS0002E": _("Repository URL must be an http://, ftp:// or file:// URL."),
    "GGBREPOS0003E": _("Repository configuration is a dictionary with specific values according to repository type."),
    "GGBREPOS0004E": _("Distribution to DEB repository must be a string"),
    "GGBREPOS0005E": _("Components to DEB repository must be listed in a array"),
    "GGBREPOS0006E": _("Components to DEB repository must be a string"),
    "GGBREPOS0007E": _("Mirror list to repository must be a string"),
    "GGBREPOS0008E": _("YUM Repository name must be string."),
    "GGBREPOS0009E": _("GPG check must be a boolean value."),
    "GGBREPOS0010E": _("GPG key must be a URL pointing to the ASCII-armored file."),
    "GGBREPOS0011E": _("Could not update repository %(repo_id)s."),
    "GGBREPOS0012E": _("Repository %(repo_id)s does not exist."),
    "GGBREPOS0013E": _("Specify repository base URL,  mirror list or metalink in order to create or "
                       "update a YUM repository."),
    "GGBREPOS0014E": _("Repository management tool was not recognized for your system."),
    "GGBREPOS0015E": _("Repository %(repo_id)s is already enabled."),
    "GGBREPOS0016E": _("Repository %(repo_id)s is already disabled."),
    "GGBREPOS0017E": _("Could not remove repository %(repo_id)s."),
    "GGBREPOS0018E": _("Could not write repository configuration file %(repo_file)s"),
    "GGBREPOS0019E": _("Specify repository distribution in order to create a DEB repository."),
    "GGBREPOS0020E": _("Could not enable repository %(repo_id)s."),
    "GGBREPOS0021E": _("Could not disable repository %(repo_id)s."),
    "GGBREPOS0022E": _("YUM Repository ID already exists"),
    "GGBREPOS0023E": _("YUM Repository name must be a string"),
    "GGBREPOS0024E": _("Unable to list repositories. Details: '%(err)s'"),
    "GGBREPOS0025E": _("Unable to retrieve repository information. Details: '%(err)s'"),
    "GGBREPOS0026E": _("Unable to add repository. Details: '%(err)s'"),
    "GGBREPOS0027E": _("Unable to remove repository. Details: '%(err)s'"),
    "GGBREPOS0028E": _("Configuration items: '%(items)s' are not supported by repository manager"),
    "GGBREPOS0029E": _("Repository metalink must be an http://, ftp:// or file:// URL."),
    "GGBREPOS0030E": _("Cannot specify mirrorlist and metalink at the same time."),


    "GGBCPUINF0001E": _("The number of vCPUs is too large for this system."),
    "GGBCPUINF0002E": _("Invalid vCPU/topology combination."),
    "GGBCPUINF0003E": _("This host (or current configuration) does not allow CPU topology."),
    "GGBCPUINF0004E": _("This host (or current configuration) does not allow to fetch lscpu details."),
    "GGBCPUINF0005E": _("This host (or current configuration) does not provide Socket(s) information."),
    "GGBCPUINF0006E": _("This host (or current configuration) does not provide Core(s) per socket information."),
    "GGBCPUINF0007E": _("This host (or current configuration) does not provide Thread(s) per core information."),

}
