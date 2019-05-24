FEDORA dependencies for Kimchi
================================

* [Build Dependencies](#development-dependencies)
* [Runtime Dependencies](#runtime-dependencies)

Development Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-dev.txt
    $ sudo dnf install -y gcc make autoconf automake git python3-pip python3-requests python3-mock gettext-devel rpm-build libxslt gcc-c++ python3-devel python2-pep8 python3-pyflakes rpmlint python3-pyyaml

Runtime Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-FEDORA.txt
    $ sudo dnf install -y systemd logrotate python3-jsonschema python3-psutil python3-ldap python3-lxml python3-websockify openssl nginx python3-cherrypy python3-cheetah python3-pam python3-m2crypto gettext-devel
