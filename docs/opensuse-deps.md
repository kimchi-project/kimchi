openSUSE dependencies for Kimchi
================================

* [Additional openSUSE Repositories](#additional-rhel-repositories)
* [Build Dependencies](#build-dependencies)
* [Runtime Dependencies](#runtime-dependencies)
* [Packages required for UI development](#packages-required-for-ui-development)
* [Packages required for tests](#packages-required-for-tests)

Additional openSUSE Repositories
--------------------------------
Some of the required packages are located in different openSUSE repositories.
Please, make sure to have them configured in your system to be able to install
all the packages listed in the sections below.

* [python-parted](http://download.opensuse.org/repositories/home:GRNET:synnefo/);
* [python-ethtool](http://download.opensuse.org/repositories/systemsmanagement:/spacewalk/);
* [python-magic](http://download.opensuse.org/repositories/home:/Simmphonie:/python/).

See [this FAQ](http://en.opensuse.org/SDB:Add_package_repositories) for more
information on how configure your system to access those repository.

Build Dependencies
--------------------

    $ sudo zypper install gcc make autoconf automake gettext-tools git \
                          rpm-build libxslt-tools

Runtime Dependencies
--------------------

    $ sudo zypper install libvirt-python libvirt kvm python-ethtool \
                            python-ipaddr libvirt-daemon-config-network \
                            nfs-client open-iscsi python-parted \
                            python-libguestfs python-configobj guestfs-tools \
                            python-websockify novnc python-magic \
                            python-paramiko python-Pillow

Packages required for UI development
------------------------------------

    $ sudo zypper install gcc-c++ python-devel python-pip
    $ sudo pip install cython libsass

Packages required for tests
---------------------------

    $ sudo zypper install python-pyflakes python-pep8 python-requests python-mock rpmlint
