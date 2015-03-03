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

import unittest

from kimchi.exception import InvalidParameter
from kimchi.utils import convert_data_size


class UtilsTests(unittest.TestCase):
    def test_convert_data_size(self):
        failure_data = [{'val': None, 'from': 'MiB'},
                        {'val': self, 'from': 'MiB'},
                        {'val': 1,    'from': None},
                        {'val': 1,    'from': ''},
                        {'val': 1,    'from': 'foo'},
                        {'val': 1,    'from': 'kib'},
                        {'val': 1,    'from': 'MiB', 'to': None},
                        {'val': 1,    'from': 'MiB', 'to': ''},
                        {'val': 1,    'from': 'MiB', 'to': 'foo'},
                        {'val': 1,    'from': 'MiB', 'to': 'kib'}]

        for d in failure_data:
            if 'to' in d:
                self.assertRaises(InvalidParameter, convert_data_size,
                                  d['val'], d['from'], d['to'])
            else:
                self.assertRaises(InvalidParameter, convert_data_size,
                                  d['val'], d['from'])

        success_data = [{'got': convert_data_size(5, 'MiB', 'MiB'),
                         'want': 5},
                        {'got': convert_data_size(5, 'MiB', 'KiB'),
                         'want': 5120},
                        {'got': convert_data_size(5, 'MiB', 'M'),
                         'want': 5.24288},
                        {'got': convert_data_size(5, 'MiB', 'GiB'),
                         'want': 0.0048828125},
                        {'got': convert_data_size(5, 'MiB', 'Tb'),
                         'want': 4.194304e-05},
                        {'got': convert_data_size(5, 'KiB', 'MiB'),
                         'want': 0.0048828125},
                        {'got': convert_data_size(5, 'M', 'MiB'),
                         'want': 4.76837158203125},
                        {'got': convert_data_size(5, 'GiB', 'MiB'),
                         'want': 5120},
                        {'got': convert_data_size(5, 'Tb', 'MiB'),
                         'want': 596046.4477539062},
                        {'got': convert_data_size(5, 'MiB'),
                         'want': convert_data_size(5, 'MiB', 'B')}]

        for d in success_data:
            self.assertEquals(d['got'], d['want'])
