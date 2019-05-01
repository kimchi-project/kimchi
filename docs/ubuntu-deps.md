Ubuntu dependencies for Kimchi
==============================

* [Build Dependencies](#build-dependencies)
* [Runtime Dependencies](#runtime-dependencies)
* [Packages required for UI development](#packages-required-for-ui-development)
* [Packages required for tests](#packages-required-for-tests)

Build Dependencies
--------------------

    $ sudo apt-get install gcc make autoconf automake gettext git pkgconf \
                           xsltproc

Runtime Dependencies
--------------------

    $ sudo apt-get install python3-configobj novnc python3-libvirt \
                            libvirt-bin nfs-common qemu-kvm python3-parted \
                            python-ethtool sosreport python-ipaddr \
                            python3-lxml open-iscsi python3-guestfs \
                            libguestfs-tools spice-html5 python3-magic \
                            python3-paramiko python3-pil \
                            fonts-font-awesome geoip-database gettext \
                            nginx-light python-cheetah python3-cherrypy3 \
                            python3-ldap python-openssl python3-pam

    sudo apt install python3 python3-setuptools libpython3.6-dev libnl-route-3-dev
    sudo pip3 install ethtool ipaddr

Packages required for UI development
------------------------------------

    $ sudo apt-get install g++ python3-dev python3-pip
    $ sudo pip install cython libsass

Packages required for tests
---------------------------

    $ sudo apt-get install pep8 pyflakes python3-requests python3-mock bc
