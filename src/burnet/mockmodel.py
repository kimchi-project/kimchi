#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This work is licensed under the terms of the GNU GPLv2.
# See the COPYING file in the top-level directory.

import burnet.model

class MockModel(object):
    def __init__(self):
        self.reset()

    def reset(self):
        pass

def get_mock_environment():
    model = MockModel()
    return model
