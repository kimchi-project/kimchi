#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.
#

import errno, cherrypy
import json
from Cheetah.Template import Template
import config

def can_accept(mime):
    if not cherrypy.request.headers.has_key('Accept'):
        accepts = 'text/html'
    else:
        accepts = cherrypy.request.headers['Accept']

    if accepts.find(';') != -1:
        accepts, _ = accepts.split(';', 1)

    if mime in map(lambda x: x.strip(), accepts.split(',')):
        return True

    return False

def render(resource, data):
    if can_accept('application/json'):
        return json.dumps(data, indent=2,
                          separators=(',', ':'),
                          encoding='iso-8859-1')
    elif can_accept('text/html'):
        filename = config.get_template_path(resource)
        try:
            return Template(file=filename, searchList=[data]).respond()
        except OSError, e:
            if e.errno != errno.ENOENT:
                raise
    else:
        raise cherrypy.HTTPError(406)
