#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.
#

import libxml2

def xpath_get_text(xml, expr):
    doc = libxml2.parseDoc(xml)
    res = doc.xpathEval(expr)
    ret = [ str(x.children) for x in res ]

    doc.freeDoc()
    return ret
