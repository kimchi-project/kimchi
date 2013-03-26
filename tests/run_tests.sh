#!/bin/bash
#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.

PYTHONPATH=../src \
  python -m unittest discover -p '*.py'
