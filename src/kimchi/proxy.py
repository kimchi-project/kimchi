#!/usr/bin/python
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA

# This module contains functions that the manipulate
# and configure the Nginx proxy.

import os
import pwd
import subprocess
from string import Template

from kimchi import sslcert
from kimchi.config import paths


def _create_proxy_config(p_port, k_port, p_ssl_port, cert, key):
    """Create nginx configuration file based on current ports config

    To allow flexibility in which port kimchi runs, we need the same
    flexibility with the nginx proxy. This method creates the config
    file dynamically by using 'nginx.conf.in' as a template, creating
    the file 'nginx_kimchi.config' which will be used to launch the
    proxy.

    Arguments:
    p_port - proxy port
    k_port - kimchid port
    p_ssl_port - proxy SSL port
    cert - cert file specified by user config
    key - key file specified by user config
    """

    # User that will run the worker process of the proxy. Fedora,
    # RHEL and Suse creates an user called 'nginx' when installing
    # the proxy. Ubuntu creates an user 'www-data' for it.
    user_proxy = 'nginx'
    try:
        pwd.getpwnam(user_proxy)
    except KeyError:
        user_proxy = 'www-data'

    config_dir = paths.conf_dir
    # No certificates specified by the user
    if not cert or not key:
        cert = '%s/kimchi-cert.pem' % config_dir
        key = '%s/kimchi-key.pem' % config_dir
        # create cert files if they don't exist
        if not os.path.exists(cert) or not os.path.exists(key):
            ssl_gen = sslcert.SSLCert()
            with open(cert, "w") as f:
                f.write(ssl_gen.cert_pem())
            with open(key, "w") as f:
                f.write(ssl_gen.key_pem())

    # Read template file and create a new config file
    # with the specified parameters.
    with open(os.path.join(config_dir, "nginx.conf.in")) as template:
        data = template.read()
    data = Template(data)
    data = data.safe_substitute(user=user_proxy,
                                proxy_port=p_port,
                                kimchid_port=k_port,
                                proxy_ssl_port=p_ssl_port,
                                cert_pem=cert, cert_key=key)

    # Write file to be used for nginx.
    config_file = open(os.path.join(config_dir, "nginx_kimchi.conf"), "w")
    config_file.write(data)
    config_file.close()


def start_proxy(options):
    """Start nginx reverse proxy."""
    _create_proxy_config(options.proxy_port,
                         options.port,
                         options.proxy_ssl_port,
                         options.ssl_cert,
                         options.ssl_key)
    config_dir = paths.conf_dir
    config_file = "%s/nginx_kimchi.conf" % config_dir
    cmd = ['nginx', '-c', config_file]
    subprocess.call(cmd)


def terminate_proxy():
    """Stop nginx process."""
    term_proxy_cmd = ['nginx', '-s', 'stop']
    subprocess.call(term_proxy_cmd)
