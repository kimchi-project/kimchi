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

import sys


class RollbackContext(object):
    '''
    A context manager for recording and playing rollback.
    The first exception will be remembered and re-raised after rollback

    Sample usage:
    with RollbackContext() as rollback:
        step1()
        rollback.prependDefer(lambda: undo step1)
        def undoStep2(arg): pass
        step2()
        rollback.prependDefer(undoStep2, arg)
    '''
    def __init__(self, *args):
        self._finally = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        According to Python official doc. This function should only re-raise
        the exception from undo functions. Python automatically re-raises the
        original exception when this function does not return True.
        http://docs.python.org/2/library/stdtypes.html#contextmanager.__exit__
        """
        undoExcInfo = None
        for undo, args, kwargs in self._finally:
            try:
                undo(*args, **kwargs)
            except Exception:
                # keep the earliest exception info
                if undoExcInfo is None:
                    undoExcInfo = sys.exc_info()

        if exc_type is None and undoExcInfo is not None:
            raise undoExcInfo[0], undoExcInfo[1], undoExcInfo[2]

    def defer(self, func, *args, **kwargs):
        self._finally.append((func, args, kwargs))

    def prependDefer(self, func, *args, **kwargs):
        self._finally.insert(0, (func, args, kwargs))

    def commitAll(self):
        self._finally = []
