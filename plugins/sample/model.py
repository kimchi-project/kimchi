#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Mark Wu <wudxw@linux.vnet.ibm.com>
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

from kimchi.exception import InvalidOperation, NotFoundError


class Model(object):

    def __init__(self):
        self.rectangles = {}
        self.circles = {}

    def rectangles_create(self, params):
        name = params['name']
        if name in self.rectangles:
            raise InvalidOperation("Rectangle %s already exists" % name)
        self.rectangles[name] = Rectangle(params['length'], params['width'])
        return name

    def rectangles_get_list(self):
        return sorted(self.rectangles)

    def rectangle_lookup(self, name):
        try:
            rectangle = self.rectangles[name]
        except KeyError:
            raise NotFoundError("Rectangle %s not found" % name)
        return {'length': rectangle.length, 'width': rectangle.width}

    def rectangle_update(self, name, params):
        if name not in self.rectangles:
            raise NotFoundError("Rectangle %s not found" % name)
        try:
            self.rectangles[name].length = params['length']
        except KeyError:
            pass

        try:
            self.rectangles[name].width = params['width']
        except KeyError:
            pass
        return name

    def rectangle_delete(self, name):
        try:
            del self.rectangles[name]
        except KeyError:
            pass

    def circles_create(self, params):
        name = params['name']
        if name in self.circles:
            raise InvalidOperation("Circle %s already exists" % name)
        self.circles[name] = Circle(params['radius'])
        return name

    def circles_get_list(self):
        return sorted(self.circles)

    def circle_lookup(self, name):
        try:
            circle = self.circles[name]
        except KeyError:
            raise NotFoundError("Circle %s not found" % name)
        return {'radius': circle.radius}

    def circle_update(self, name, params):
        if name not in self.circles:
            raise NotFoundError("Circle %s not found" % name)
        self.circles[name].radius = params['radius']
        return name

    def circle_delete(self, name):
        try:
            del self.circles[name]
        except KeyError:
            pass


class Rectangle(object):
    def __init__(self, length, width):
        self.length = length
        self.width = width


class Circle(object):
    def __init__(self, radius):
        self.radius = radius
