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

import cherrypy
import errno
import json


from kimchi.config import paths
from Cheetah.Template import Template
from glob import iglob


def get_lang():
    cookie = cherrypy.request.cookie
    if "kimchiLang" in cookie.keys():
        return [cookie["kimchiLang"].value]

    lang = cherrypy.request.headers.get("Accept-Language", "en_US")

    if lang and lang.find(';') != -1:
        lang, _ = lang.split(';', 1)
    # the language from Accept-Language is the format as en-us
    # convert it into en_US
    langs = lang.split(',')
    for idx, val in enumerate(langs):
        if "-" in val:
            langCountry = val.split('-')
            langCountry[1] = langCountry[1].upper()
            langs[idx] = "_".join(langCountry)

    return langs


def get_support_languages():
    mopath = "%s/*" % paths.mo_dir
    return [path.rsplit('/', 1)[1] for path in iglob(mopath)]


def validate_language(langs):
    supportLangs = get_support_languages()
    for lang in langs:
        if lang in supportLangs:
            return lang
    return "en_US"


def can_accept(mime):
    if 'Accept' not in cherrypy.request.headers:
        accepts = 'text/html'
    else:
        accepts = cherrypy.request.headers['Accept']

    if accepts.find(';') != -1:
        accepts, _ = accepts.split(';', 1)

    if mime in map(lambda x: x.strip(), accepts.split(',')):
        return True

    return False


def can_accept_html():
    return can_accept('text/html') or \
        can_accept('application/xaml+xml') or \
        can_accept('*/*')


def render_cheetah_file(resource, data):
    paths = cherrypy.request.app.root.paths
    filename = paths.get_template_path(resource)
    try:
        params = {'data': data}
        lang = validate_language(get_lang())
        gettext_conf = {'domain': cherrypy.request.app.root.domain,
                        'localedir': paths.mo_dir,
                        'lang': [lang]}
        params['lang'] = gettext_conf
        return Template(file=filename, searchList=params).respond()
    except OSError, e:
        if e.errno == errno.ENOENT:
            raise cherrypy.HTTPError(404)
        else:
            raise


def render(resource, data):
    if can_accept('application/json'):
        cherrypy.response.headers['Content-Type'] = \
            'application/json;charset=utf-8'
        return json.dumps(data, indent=2, separators=(',', ':'))
    elif can_accept_html():
        return render_cheetah_file(resource, data)
    else:
        raise cherrypy.HTTPError(406)
