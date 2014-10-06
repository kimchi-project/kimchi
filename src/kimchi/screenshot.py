#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#

import glob
import os
import signal
import tempfile
import time
import uuid


try:
    from PIL import Image
except ImportError:
    import Image


from kimchi import config
from kimchi.utils import kimchi_log


(fd, pipe) = tempfile.mkstemp()
stream_test_result = None


class VMScreenshot(object):
    OUTDATED_SECS = 5
    THUMBNAIL_SIZE = (256, 256)
    LIVE_WINDOW = 60
    MAX_STREAM_ATTEMPTS = 10

    def __init__(self, args):
        self.vm_uuid = args['uuid']
        args.setdefault('thumbnail',
                        os.path.join(config.get_screenshot_path(),
                                     '%s-%s.png' %
                                     (self.vm_uuid, str(uuid.uuid4()))))
        self.info = args

    @staticmethod
    def get_stream_test_result():
        return stream_test_result

    def lookup(self):
        now = time.time()
        try:
            last_update = os.path.getmtime(self.info['thumbnail'])
        except OSError:
            last_update = 0

        if now - last_update > self.OUTDATED_SECS:
            self._clean_extra(self.LIVE_WINDOW)
            self._generate_thumbnail()
        return '/data/screenshots/%s' %\
               os.path.basename(self.info['thumbnail'])

    def _clean_extra(self, window=-1):
        """
        Clear screenshots before time specified by window,
        Clear all screenshots if window is -1.
        """
        try:
            now = time.time()
            clear_list = glob.glob("%s/%s-*.png" %
                                   (config.get_screenshot_path(),
                                    self.vm_uuid))
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

    def _create_black_image(self, thumbnail):
        image = Image.new("RGB", self.THUMBNAIL_SIZE, 'black')
        image.save(thumbnail)

    def _watch_stream_creation(self, thumbnail):
        """
        This is a verification test for libvirt stream functionality.

        It is necessary to avoid the server hangs while creating the screenshot
        image using libvirt stream API.

        This problem was found in libvirt 0.9.6 for SLES11 SP2.

        This test consists in running the screeshot creation with a timeout.
        If timeout occurs, the libvirt is taking too much time to create the
        screenshot image and the stream must be disabled it if happens
        successively (to avoid blocking server requests).
        """
        pid = os.fork()
        if pid == 0:
            try:
                self._generate_scratch(thumbnail)
                os._exit(0)
            except:
                os._exit(1)
        else:
            counter = 0
            ret = os.waitpid(pid, os.WNOHANG)
            while ret == (0, 0) and counter < 3:
                counter += 1
                time.sleep(1)
                ret = os.waitpid(pid, os.WNOHANG)

            fd = open(pipe, "a")
            if ret != (pid, 0):
                fd.write("-")
                if ret[0] != pid:
                    os.kill(int(pid), signal.SIGKILL)
                    os.waitpid(pid, 0)
            else:
                fd.write("+")
            fd.close()

    def _get_test_result(self):
        if not os.path.exists(pipe):
            return

        fd = open(pipe, "r")
        data = fd.read()
        fd.close()

        if len(data) >= self.MAX_STREAM_ATTEMPTS or bool('+' in data):
            global stream_test_result
            stream_test_result = bool('+' in data)
            os.remove(pipe)

    def _generate_thumbnail(self):
        thumbnail = os.path.join(config.get_screenshot_path(), '%s-%s.png' %
                                 (self.vm_uuid, str(uuid.uuid4())))

        self._get_test_result()
        if stream_test_result is None:
            self._watch_stream_creation(thumbnail)
        elif stream_test_result:
            try:
                self._generate_scratch(thumbnail)
            except:
                kimchi_log.error("screenshot_creation: Unable to create "
                                 "screenshot image %s." % thumbnail)
        else:
            self._create_black_image(thumbnail)

        if os.path.getsize(thumbnail) == 0:
            self._create_black_image(thumbnail)
        else:
            im = Image.open(thumbnail)
            try:
                # Prevent Image lib from lazy load,
                # work around pic truncate validation in thumbnail generation
                im.thumbnail(self.THUMBNAIL_SIZE)
            except Exception as e:
                kimchi_log.warning("Image load with warning: %s." % e)
            im.save(thumbnail, "PNG")

        self.info['thumbnail'] = thumbnail
