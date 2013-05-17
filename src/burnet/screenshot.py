#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Royce Lv <lvroyce@linux.vnet.ibm.com>
#
# All Rights Reserved.
#

import os
import time
import Image
import random
import uuid
import glob

import config


class VMScreenshot(object):
    OUTDATED_SECS = 5
    THUMBNAIL_SIZE = (256, 256)
    LIVE_WINDOW = 60

    def __init__(self, args):
        self.vm_name = args['name']
        args.setdefault('thumbnail',
            os.path.join(config.get_screenshot_path(),
                '%s-%s.png' % (self.vm_name, str(uuid.uuid4()))))
        self.info = args

    def lookup(self):
        now = time.time()
        try:
            last_update = os.path.getmtime(self.info['thumbnail'])
        except OSError:
            last_update = 0

        if now - last_update > self.OUTDATED_SECS:
            self._clean_extra(self.LIVE_WINDOW)
            self._generate_thumbnail()
        return '/data/screenshots/%s' % os.path.basename(self.info['thumbnail'])


    def _clean_extra(self, window=-1):
        """
        Clear screenshots before time specified by window,
        Clear all screenshots if window is -1.
        """
        try:
            now = time.time()
            clear_list = glob.glob("%s/%s-*.png" %
                (config.get_screenshot_path(), self.vm_name))
            for f in clear_list:
                if now - os.path.getmtime(f) > window:
                    os.unlink(f)
        except OSError:
            pass

    def delete(self):
        return self._clean_extra()

    def _generate_scratch(self, thumbnail):
        """
        Generate screenshot of given vm.
        Override me in child class.
        """
        pass

    def _generate_thumbnail(self):
        thumbnail = os.path.join(config.get_screenshot_path(), '%s-%s.png' %
                                 (self.vm_name, str(uuid.uuid4())))
        self._generate_scratch(thumbnail)

        if os.path.getsize(thumbnail) == 0:
            image = Image.new("RGB", self.THUMBNAIL_SIZE, 'black')
            image.save(thumbnail)
        else:
            im = Image.open(thumbnail)
            im.thumbnail(self.THUMBNAIL_SIZE)
            im.save(thumbnail, "PNG")
        self.info['thumbnail'] = thumbnail
