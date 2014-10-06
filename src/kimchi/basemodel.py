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


class BaseModel(object):
    '''
    This model squashes all sub-model's public callable methods to itself.

    Model methods are not limited to get_list, create, lookup, update, delete.
    Controller can call generate_action_handler to generate new actions, which
    call the related model methods. So all public callable methods of a
    sub-model should be mapped to this model.
    '''
    def __init__(self, model_instances):
        for model_instance in model_instances:
            cls_name = model_instance.__class__.__name__
            if cls_name.endswith('Model'):
                method_prefix = cls_name[:-len('Model')].lower()
            else:
                method_prefix = cls_name.lower()

            callables = [m for m in dir(model_instance)
                         if not m.startswith('_') and
                         callable(getattr(model_instance, m))]

            for member_name in callables:
                m = getattr(model_instance, member_name, None)
                setattr(self, '%s_%s' % (method_prefix, member_name), m)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            inst = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = inst
        return cls._instances[cls]
