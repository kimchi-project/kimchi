# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM, Corp. 2015
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

import os
import tempfile
import threading
import unittest

from kimchi.exception import NotFoundError
from kimchi import objectstore

tmpfile = None


def setUpModule():
    global tmpfile
    tmpfile = tempfile.mktemp()


def tearDownModule():
    os.unlink(tmpfile)


class ObjectStoreTests(unittest.TestCase):
    def test_objectstore(self):
        store = objectstore.ObjectStore(tmpfile)

        with store as session:
            # Test create
            session.store('fǒǒ', 'těst1', {'α': 1})
            session.store('fǒǒ', 'těst2', {'β': 2})

            # Test list
            items = session.get_list('fǒǒ')
            self.assertTrue(u'těst1' in items)
            self.assertTrue(u'těst2' in items)

            # Test get
            item = session.get('fǒǒ', 'těst1')
            self.assertEquals(1, item[u'α'])

            # Test delete
            session.delete('fǒǒ', 'těst2')
            self.assertEquals(1, len(session.get_list('fǒǒ')))

            # Test get non-existent item

            self.assertRaises(NotFoundError, session.get,
                              'α', 'β')

            # Test delete non-existent item
            self.assertRaises(NotFoundError, session.delete,
                              'fǒǒ', 'těst2')

            # Test refresh existing item
            session.store('fǒǒ', 'těst1', {'α': 2})
            item = session.get('fǒǒ', 'těst1')
            self.assertEquals(2, item[u'α'])

    def test_object_store_threaded(self):
        def worker(ident):
            with store as session:
                session.store('foo', ident, {})

        store = objectstore.ObjectStore(tmpfile)

        threads = []
        for i in xrange(50):
            t = threading.Thread(target=worker, args=(i,))
            t.setDaemon(True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        with store as session:
            self.assertEquals(50, len(session.get_list('foo')))
            self.assertEquals(10, len(store._connections.keys()))
