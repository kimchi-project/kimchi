OPENSUSE-LEAP dependencies for Kimchi
================================

* [Build Dependencies](#development-dependencies)
* [Runtime Dependencies](#runtime-dependencies)

Development Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-dev.txt
    $ sudo zypper install -y gcc make autoconf automake git python3-pip python3-requests python3-mock gettext-tools rpm-build libxslt-tools gcc-c++ python3-devel python3-pep8 python3-pyflakes rpmlint python3-PyYAML python3-distro

Runtime Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-OPENSUSE-LEAP.txt
    $ sudo zypper install -y systemd logrotate python3-jsonschema python3-psutil python3-ldap python3-lxml python3-websockify openssl nginx python3-CherryPy python3-Cheetah3 python3-python-pam python3-M2Crypto gettext-tools python3-distro
