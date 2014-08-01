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

from kimchi.exception import InvalidOperation, NotFoundError
from kimchi.basemodel import BaseModel


class CirclesModel(object):
    def __init__(self):
        self._circles = {}

    def create(self, params):
        name = params['name']
        if name in self._circles:
            raise InvalidOperation("SPCIRCLE0001E", {'name': name})
        self._circles[name] = Circle(params['radius'])
        return name

    def get_list(self):
        return sorted(self._circles)


class CircleModel(object):
    def __init__(self, parent_model):
        # Circel and Circles models are friends, it's OK to share _circles.
        self._circles = parent_model._circles

    def lookup(self, name):
        try:
            circle = self._circles[name]
        except KeyError:
            raise NotFoundError("SPCIRC0002E", {'name': name})
        return {'radius': circle.radius}

    def update(self, name, params):
        if name not in self._circles:
            raise NotFoundError("SPCIRC0002E", {'name': name})
        self._circles[name].radius = params['radius']
        return name

    def delete(self, name):
        try:
            del self._circles[name]
        except KeyError:
            pass


class RectanglesModel(object):
    def __init__(self):
        self._rectangles = {}

    def create(self, params):
        name = params['name']
        if name in self._rectangles:
            raise InvalidOperation("SPRET0001E", {'name': name})
        self._rectangles[name] = Rectangle(params['length'], params['width'])
        return name

    def get_list(self):
        return sorted(self._rectangles)


class RectangleModel(object):
    def __init__(self, parent_model):
        self._rectangles = parent_model._rectangles

    def lookup(self, name):
        try:
            rectangle = self._rectangles[name]
        except KeyError:
            raise NotFoundError("SPRET0002E", {'name': name})
        return {'length': rectangle.length, 'width': rectangle.width}

    def update(self, name, params):
        if name not in self._rectangles:
            raise NotFoundError("SPRET0002E", {'name': name})
        try:
            self._rectangles[name].length = params['length']
        except KeyError:
            pass

        try:
            self._rectangles[name].width = params['width']
        except KeyError:
            pass
        return name

    def delete(self, name):
        try:
            del self._rectangles[name]
        except KeyError:
            pass


class Model(BaseModel):
    def __init__(self):
        circles = CirclesModel()
        circle = CircleModel(circles)

        rectangles = RectanglesModel()
        rectangle = RectangleModel(rectangles)

        return super(Model, self).__init__(
            [circle, circles, rectangle, rectangles])


class Rectangle(object):
    def __init__(self, length, width):
        self.length = length
        self.width = width


class Circle(object):
    def __init__(self, radius):
        self.radius = radius
