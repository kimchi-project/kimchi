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

    $ sudo apt-get install python-configobj websockify novnc python-libvirt \
                            libvirt-bin nfs-common qemu-kvm python-parted \
                            python-ethtool sosreport python-ipaddr \
                            python-lxml open-iscsi python-guestfs \
                            libguestfs-tools spice-html5 python-magic \
                            python-paramiko python-pil

Packages required for UI development
------------------------------------

    $ sudo apt-get install g++ python-dev python-pip
    $ sudo pip install cython libsass

Packages required for tests
---------------------------

    $ sudo apt-get install pep8 pyflakes python-requests python-mock bc
