#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# All Rights Reserved.
#

import errno, cherrypy
import os
import json
from Cheetah.Template import Template
import config


def get_lang():
    cookie = cherrypy.request.cookie
    if "burnetLang" in cookie.keys():
        return [cookie["burnetLang"].value]

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


def validate_language(langs):
    supportLangs = config.get_support_language()
    for lang in langs:
        if lang in supportLangs:
            return lang
    return "en_US"


def can_accept(mime):
    if not cherrypy.request.headers.has_key('Accept'):
        accepts = 'text/html'
    else:
        accepts = cherrypy.request.headers['Accept']

    if accepts.find(';') != -1:
        accepts, _ = accepts.split(';', 1)

    if mime in map(lambda x: x.strip(), accepts.split(',')):
        return True

    return False

def render(resource, data):
    if can_accept('application/json'):
        return json.dumps(data, indent=2,
                          separators=(',', ':'),
                          encoding='iso-8859-1')
    elif can_accept('text/html'):
        filename = config.get_template_path(resource)
        try:
            params = {'data': data}
            lang = validate_language(get_lang())
            gettext_conf = {'domain': 'burnet',
                            'localedir': config.get_mo_path(),
                            'lang': [lang]}
            params['lang'] = gettext_conf
            return Template(file=filename, searchList=params).respond()
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise cherrypy.HTTPError(404)
            else:
                raise
    else:
        raise cherrypy.HTTPError(406)
