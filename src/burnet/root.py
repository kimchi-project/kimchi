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

    def get(self):
        return template.render('index', { 'hostname': 'localhost' })
