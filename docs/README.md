Kimchi Project
==============

Kimchi is an HTML5 based management tool for KVM. It is designed to make it as
easy as possible to get started with KVM and create your first guest.

Kimchi runs as a daemon on the hypervisor host. It manages KVM guests through
libvirt. The management interface is accessed over the web using a browser that
supports HTML5.

Browser Support
===============
Desktop Browser Support:
-----------------------
* **Internet Explorer:** IE9+
* **Chrome:** Current-1 version
* **Firefox:** Current-1 version Firefox 24ESR
* **Safari:** Current-1 version
* **Opera:** Current-1 version

Mobile Browser Support:
-----------------------
* **Safari iOS:** Current-1 version
* **Android Browser** Current-1 version

Current-1 version denotes that we support the current stable version of the
browser and the version that preceded it. For example, if the current version of
a browser is 24.x, we support the 24.x and 23.x versions.This does not mean that
kimchi cannot be used in other browsers, however, functionality and appearance
may be diminished and we may not be able to provide support for any problems you
find.

Hypervisor Distro Support
=========================

Kimchi daemon might run on any GNU/Linux distribution that meets the conditions
described on the 'Getting Started' section below.

The Kimchi community makes an effort to test with the latest versions of Fedora,
RHEL, OpenSuSe, and Ubuntu.

Getting Started
===============

Install Dependencies
--------------------

**For fedora and RHEL:**

     $ sudo yum install gcc make autoconf automake gettext-devel git \
                        python-cherrypy python-cheetah libvirt-python \
                        libvirt libvirt-daemon-config-network python-imaging \
                        PyPAM m2crypto python-jsonschema rpm-build \
                        qemu-kvm python-psutil python-ethtool sos \
                        python-ipaddr python-ldap python-lxml nfs-utils \
                        iscsi-initiator-utils libxslt pyparted nginx \
                        python-libguestfs libguestfs-tools python-websockify \
                        novnc spice-html5 python-configobj

     # If using RHEL, install the following additional packages:
     $ sudo yum install python-unittest2 python-ordereddict

     # Restart libvirt to allow configuration changes to take effect
     $ sudo service libvirtd restart

    Packages version requirement:
        python-psutil >= 0.6.0

    # These dependencies are only required if you want to run the tests:
    $ sudo yum install pyflakes python-pep8 python-requests

*Note for RHEL users*: Some of the above packages are located in the Red Hat
EPEL repositories.  See
[this FAQ](http://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F)
for more information on how to configure your system to access this repository.

And for RHEL7 systems, you also need to subscribe to the "RHEL Server Optional"
channel at RHN Classic or Red Hat Satellite.

**For debian:**

    $ sudo apt-get install gcc make autoconf automake gettext git \
                           python-cherrypy3 python-cheetah python-libvirt \
                           libvirt-bin python-imaging python-configobj \
                           python-pam python-m2crypto python-jsonschema \
                           qemu-kvm libtool python-psutil python-ethtool \
                           sosreport python-ipaddr python-ldap \
                           python-lxml nfs-common open-iscsi lvm2 xsltproc \
                           python-parted nginx python-guestfs libguestfs-tools \
                           websockify novnc spice-html5

    Packages version requirement:
        python-jsonschema >= 1.3.0
        python-psutil >= 0.6.0

    # These dependencies are only required if you want to run the tests:
    $ sudo apt-get install pep8 pyflakes python-requests

**For openSUSE:**

    $ sudo zypper install gcc make autoconf automake gettext-tools git \
                          python-CherryPy python-Cheetah libvirt-python \
                          libvirt libvirt-daemon-config-network python-pam \
                          python-imaging python-M2Crypto python-jsonschema \
                          rpm-build kvm python-psutil python-ethtool \
                          python-ipaddr python-ldap python-lxml nfs-client \
                          open-iscsi libxslt-tools python-xml python-parted \
                          nginx python-libguestfs python-configobj \
                          guestfs-tools python-websockify novnc

    Packages version requirement:
        python-psutil >= 0.6.0

    # These dependencies are only required if you want to run the tests:
    $ sudo zypper install python-pyflakes python-pep8 python-requests

*Note for openSUSE users*: Some of the above packages are located in different
openSUSE repositories. See
[this FAQ](http://download.opensuse.org/repositories/home:GRNET:synnefo/) for
python-parted; and
[this FAQ](http://download.opensuse.org/repositories/systemsmanagement:/spacewalk/)
for python-ethtool to get the correct repository based on your openSUSE version. And
[this FAQ](http://en.opensuse.org/SDB:Add_package_repositories) for more
information on how configure your system to access this repository.

Build and Install
-----------------
    For openSUSE 13.1:
    $ ./autogen.sh --with-spice-html5

    Otherwise:
    $ ./autogen.sh --system

    $ make
    $ sudo make install   # Optional if running from the source tree

Run
---

    $ sudo kimchid --host=0.0.0.0

If you cannot access Kimchi, take a look at these 2 points:

1. Firewall
Kimchi uses by default the ports 8000, 8001 and 64667. To allow incoming connections:

    For system using firewalld, do:
    sudo firewall-cmd --add-port=8000/tcp --permanent
    sudo firewall-cmd --add-port=8001/tcp --permanent
    sudo firewall-cmd --add-port=64667/tcp --permanent
    sudo firewall-cmd --reload

    For openSUSE systems, do:
    sudo /sbin/SuSEfirewall2 open EXT TCP 8000
    sudo /sbin/SuSEfirewall2 open EXT TCP 8001
    sudo /sbin/SuSEfirewall2 open EXT TCP 64667

    For system using iptables, do:
    sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 64667 -j ACCEPT

    Don't forget to correctly save the rules.


2. SELinux
Allow httpd_t context for Kimchi web server:

    semanage permissive -a httpd_t


Test
----

    $ make check-local # check for i18n and formatting errors
    $ sudo make check

After all tests are executed, a summary will be displayed containing any
errors/failures which might have occurred.

Usage
-----

Connect your browser to https://localhost:8001.  You should see a screen like:

![Kimchi Login Screen](/docs/kimchi-login.png)

Kimchi uses PAM to authenticate users so you can log in with the same username
and password that you would use to log in to the machine itself.  Once logged in
you will see a screen like:

![Kimchi Guest View](/docs/kimchi-guest.png)

This shows you the list of running guests including a live screenshot of
the guest session.  You can use the action buttons to shutdown the guests
or connect to the display in a new window.

To create a new guest, click on the "+" button in the upper right corner.
In Kimchi, all guest creation is done through templates.

You can view or modify templates by clicking on the Templates link in the
top navigation bar.

The template screen looks like:

![Kimchi Template View](/docs/kimchi-templates.png)

From this view, you can change the parameters of a template or create a
new template using the "+" button in the upper right corner.

To create a template, you need an ISO on your host or using remote one.
If you are willing to use your own ISO, please copy it to out of box storage
pool (default path is: /var/lib/kimchi/isos).

Known Issues
------------

1. When you are using NFS as storage pool, check the nfs export path permission
is configured as:
    (1) export path need to be squashed as kvm gid and libvirt uid:
        /my_export_path *(all_squash,anongid=<kvm-gid>, anonuid=<libvirt-uid>,rw,sync)
        So that root user can create volume with right user/group.
    (2) Chown of export path as libvirt user, group as kvm group,
        In order to make sure all mapped user can get into the mount point.

Participating
-------------

All patches are sent through our mailing list hosted by oVirt.  More
information can be found at:

https://github.com/kimchi-project/kimchi/wiki/Communications

Patches should be sent using git-send-email to kimchi-devel@ovirt.org.
