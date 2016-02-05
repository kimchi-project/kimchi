RHEL/Fedora dependencies for Kimchi
===================================

* [Additional RHEL Repositories](#additional-rhel-repositories)
* [Build Dependencies](#build-dependencies)
* [Runtime Dependencies](#runtime-dependencies)
* [Packages required for UI development](#packages-required-for-ui-development)
* [Packages required for tests](#packages-required-for-tests)

Additional RHEL Repositories
----------------------------
Some of the above packages are located in the Red Hat EPEL repositories, for RHEL
system.  See [this FAQ](http://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F)
for more information on how to configure your system to access this repository.

For RHEL7 systems, you also need to subscribe to the "RHEL Server Optional"
channel at RHN Classic or Red Hat Satellite.

Build Dependencies
--------------------

    $ sudo yum install gcc make autoconf automake gettext-devel git rpm-build \
                        libxslt

Runtime Dependencies
--------------------

    $ sudo yum install libvirt-python libvirt libvirt-daemon-config-network \
                        qemu-kvm python-ethtool sos python-ipaddr nfs-utils \
                        iscsi-initiator-utils pyparted python-libguestfs \
                        libguestfs-tools python-websockify novnc spice-html5 \
                        python-configobj python-magic python-paramiko \
                        python-pillow

    # For RHEL systems, install the additional packages:
    $ sudo yum install python-ordereddict

    # Restart libvirt to allow configuration changes to take effect
    $ sudo service libvirtd restart

Packages required for UI development
------------------------------------

    $ sudo yum install gcc-c++ python-devel python-pip
    $ sudo pip install cython libsass

Packages required for tests
---------------------------

    $ sudo yum install pyflakes python-pep8 python-requests python-mock

    # For RHEL systems, install the additional packages:
    $ sudo yum install python-unittest2
