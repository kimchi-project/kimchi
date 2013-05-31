#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.
#

import cherrypy
import template
import controller


class Root(controller.Resource):
    def __init__(self, model):
        controller.Resource.__init__(self, model)
        self.vms = controller.VMs(model)
        self.templates = controller.Templates(model)
        self.storagepools = controller.StoragePools(model)

    def get(self):
        return self.default('burnet-ui.html')

    @cherrypy.expose
    def default(self, page, **kwargs):
        if page.endswith('.html'):
            return template.render(page, {'hostname': 'localhost'})
        raise cherrypy.HTTPError(404)
