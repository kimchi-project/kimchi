#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
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

from kimchi.control.base import AsyncCollection, Resource
from kimchi.control.utils import internal_redirect
from kimchi.control.utils import UrlSubNode


@UrlSubNode("debugreports", True, ['GET', 'PUT', 'POST'])
class DebugReports(AsyncCollection):
    def __init__(self, model):
        super(DebugReports, self).__init__(model)
        self.resource = DebugReport

    def _get_resources(self, filter_params):
        res_list = super(DebugReports, self)._get_resources(filter_params)
        return sorted(res_list, key=lambda x:x.data['time'], reverse=True)


class DebugReport(Resource):
    def __init__(self, model, ident):
        super(DebugReport, self).__init__(model, ident)
        self.update_params = ["name"]
        self.uri_fmt = '/debugreports/%s'
        self.content = DebugReportContent(model, ident)

    @property
    def data(self):
        return {'name': self.ident,
                'uri': self.info['uri'],
                'time': self.info['ctime']}


class DebugReportContent(Resource):
    def __init__(self, model, ident):
        super(DebugReportContent, self).__init__(model, ident)

    def get(self):
        self.lookup()
        raise internal_redirect(self.info['uri'])
