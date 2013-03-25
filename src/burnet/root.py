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

import cherrypy
import template
import controller

class Root(controller.Resource):
    def __init__(self, model):
        controller.Resource.__init__(self, model)
        self.vms = controller.VMs(model)

    def get(self):
        return template.render('index', { 'hostname': 'localhost' })
