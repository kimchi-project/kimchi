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
    $ sudo dnf install -y python3-configobj python3-lxml python3-magic python3-paramiko python3-ldap spice-html5 novnc qemu-kvm python3-libvirt python3-pyparted python3-ethtool python3-pillow python3-cherrypy python3-pam python3-libguestfs libvirt libvirt-daemon-config-network iscsi-initiator-utils libguestfs-tools sos nfs-utils
