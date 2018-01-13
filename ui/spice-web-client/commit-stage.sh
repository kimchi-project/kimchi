#!/bin/bash
set -e
set -u
set -x

# it would be good to not run the build if:
#
# * there are no changes in the source files used in the concatenator.js file
# * there haven't been any changes in this repo
#
# since the last build done by jenkins. To achieve this you might get the date
# of the last jenkins commit in this repo, and do git log --since 'that date'
# and check if there have been any commit or not.

cd "$(dirname "$0")"

echo "Generating spiceproxy.js"

spiceproxy/concatenator.js spice-web-client
