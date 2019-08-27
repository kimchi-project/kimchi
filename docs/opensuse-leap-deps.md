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
    $ sudo zypper install -y python3-configobj python3-lxml python3-magic python3-paramiko python3-ldap spice-html5 novnc qemu-kvm python3-libvirt-python python-parted python3-ethtool python3-Pillow python3-CherryPy python3-python-pam python3-ipaddr python3-libguestfs libvirt libvirt-daemon-config-network open-iscsi guestfs-tools nfs-client
