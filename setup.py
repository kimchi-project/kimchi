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

from distutils.command.build import build
from distutils.cmd import Command
from distutils.core import setup
from glob import glob, iglob
import polib
import os


PROJECT = 'burnet'


def make_mo():
    print "compile mo files"
    for path in iglob("i18n/po/*"):
        pofile = os.path.join(path, 'LC_MESSAGES', PROJECT + '.po')
        lang = path.rsplit('/', 1)[1]
        mopath = os.path.join("i18n/mo", lang, 'LC_MESSAGES')
        mofile = os.path.join(mopath, PROJECT + '.mo')
        if (os.path.isfile(pofile) and
            (not os.path.isfile(mofile) or
             os.path.getmtime(mofile) < os.path.getmtime(pofile))):
            po = polib.pofile(pofile)
            if not os.path.isdir(mopath):
                os.makedirs(mopath)
            po.save_as_mofile(mofile)
            print "compile: %s" % mofile


class cmd_make_mo(Command):
    description = "compile po files to mo files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        make_mo()


class burnet_build(build):
    def run(self):
        make_mo()
        build.run(self)


setup(name='burnet',
      version='0.1',
      package_dir={'': 'src'},
      packages=['burnet'],
      scripts=['bin/burnetd'],
      cmdclass={'make_mo': cmd_make_mo,
                'build': burnet_build},
      data_files=[('share/burnet/js', glob('js/*.js')),
                  ('share/burnet/css', glob('css/*.css')),
                  ('share/burnet/css/fonts', glob('css/fonts/*')),
                  ('share/burnet/data', []),
                  ('share/burnet/static', glob('static/*.html')),
                  ('share/burnet/static/include', glob('static/include/*.*')),
                  ('share/burnet/static/include/web-socket-js',
                   glob('static/include/web-socket-js/*')),
                  ('share/burnet/data/screenshots', []),
                  ('share/burnet/images', glob('images/*')),
                  ('share/burnet/templates', glob('templates/*.tmpl')),
                  ('share/burnet/i18n', glob('i18n/*'))])
