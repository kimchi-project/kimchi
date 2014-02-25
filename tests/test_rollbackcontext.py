#
# Project Kimchi
#
# Copyright IBM, Corp. 2014
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import unittest

from kimchi.rollbackcontext import RollbackContext


class FirstError(Exception):
    '''A hypothetical exception to be raise in the test firstly.'''
    pass


class SecondError(Exception):
    '''A hypothetical exception to be raise in the test secondly.'''
    pass


class RollbackContextTests(unittest.TestCase):

    def setUp(self):
        self._counter = 0

    def _inc_counter(self):
        self._counter += 1

    def _raise(self, exception=FirstError):
        raise exception()

    def test_rollback(self):
        with RollbackContext() as rollback:
            rollback.prependDefer(self._inc_counter)
            rollback.prependDefer(self._inc_counter)
        self.assertEquals(self._counter, 2)

    def test_raise(self):
        try:
            with RollbackContext() as rollback:
                rollback.prependDefer(self._inc_counter)
                rollback.prependDefer(self._inc_counter)
                raise FirstError()
                rollback.prependDefer(self._inc_counter)
        except FirstError:
            # All undo before the FirstError should be run
            self.assertEquals(self._counter, 2)
        else:
            self.fail('Should have raised FirstError')

    def test_raise_undo(self):
        try:
            with RollbackContext() as rollback:
                rollback.prependDefer(self._inc_counter)
                rollback.prependDefer(self._raise)
                rollback.prependDefer(self._inc_counter)
        except FirstError:
            # All undo should be run
            self.assertEquals(self._counter, 2)
        else:
            self.fail('Should have raised FirstError')

    def test_raise_prefer_original(self):
        try:
            with RollbackContext() as rollback:
                rollback.prependDefer(self._raise, SecondError)
                raise FirstError()
        except FirstError:
            pass
        except SecondError:
            self.fail('Should have preferred FirstError to SecondError')
        else:
            self.fail('Should have raised FirstError')

    def test_raise_prefer_first_undo(self):
        try:
            with RollbackContext() as rollback:
                rollback.prependDefer(self._raise, SecondError)
                rollback.prependDefer(self._raise, FirstError)
        except FirstError:
            pass
        except SecondError:
            self.fail('Should have preferred FirstError to SecondError')
        else:
            self.fail('Should have raised FirstError')
