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

from distutils.core import setup
from glob import glob

setup(name='burnet',
      version='0.1',
      package_dir={'': 'src'},
      packages=['burnet'],
      scripts=['bin/burnetd'],
      data_files=[('share/burnet/js', glob('js/*.js')),
                  ('share/burnet/css', glob('css/*.css')),
                  ('share/burnet/css/fonts', glob('css/fonts/*')),
                  ('share/burnet/images', glob('images/*')),
                  ('share/burnet/templates', glob('templates/*.tmpl'))])
