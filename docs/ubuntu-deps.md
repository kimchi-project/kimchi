UBUNTU dependencies for Kimchi
================================

* [Build Dependencies](#development-dependencies)
* [Runtime Dependencies](#runtime-dependencies)

Development Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-dev.txt
    $ sudo apt install -y gcc make autoconf automake git python3-pip python3-requests python3-mock gettext pkgconf xsltproc python3-dev pep8 pyflakes python3-yaml

Runtime Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-UBUNTU.txt
    $ sudo apt install -y systemd logrotate python3-jsonschema python3-psutil python3-ldap python3-lxml python3-websockify openssl nginx python3-cherrypy3 python-cheetah python3-pam python-m2crypto gettext python3-openssl
