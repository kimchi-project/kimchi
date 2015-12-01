#!/bin/bash

#
# Project Kimchi
#
# Copyright IBM, Corp. 2015
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

errors="$(cat ui/pages/i18n.json.tmpl | grep -o 'KCH[0-9A-Z]*'| sort)"
uiErrors="$(grep -Ro 'KCH[0-9A-Z]*' ui/js/ | cut -d: -f2 | sort| uniq)"

# all errors on i18n are present in js/html files: success
if [ "$errors" == "$uiErrors" ]; then
    echo "UI errors codes are correct"
else
    echo "Error while checking UI errors codes."
    diff  <(echo "$errors" ) <(echo "$uiErrors")
fi
