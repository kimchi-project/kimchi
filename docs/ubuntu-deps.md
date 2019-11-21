UBUNTU dependencies for Kimchi
================================

* [Build Dependencies](#development-dependencies)
* [Runtime Dependencies](#runtime-dependencies)

Development Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-dev.txt
    $ sudo apt install -y gcc make autoconf automake git python3-pip python3-requests python3-mock gettext pkgconf xsltproc python3-dev pep8 pyflakes python3-yaml libnl-route-3-dev

Runtime Dependencies
--------------------

    $ sudo -H pip3 install -r requirements-UBUNTU.txt
    $ sudo apt install -y python3-configobj python3-lxml python3-magic python3-paramiko python3-ldap spice-html5 novnc qemu-kvm python3-libvirt python3-parted python3-guestfs python3-pil python3-cherrypy3 python3-pam libvirt0 libvirt-daemon-system libvirt-clients nfs-common sosreport open-iscsi libguestfs-tools libnl-route-3-dev
