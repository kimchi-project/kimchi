Kimchi Project
==============

Kimchi is an HTML5 based management tool for KVM. It is designed to make it as
easy as possible to get started with KVM and create your first guest.

Kimchi runs as a Wok plugin. Wok runs as a daemon on the hypervisor host.

Kimchi manages KVM guests through libvirt. The management interface is accessed
over the web using a browser that supports HTML5.

Browser Support
===============

Wok and its plugin can run in any web browser that supports HTML5. The
Kimchi community (responsible for Wok project) makes an effort to
test it with the latest versions of Chrome and Firefox browsers, but the
following list can be used as reference to browser support.

Desktop Browser Support:
-----------------------
* **Internet Explorer:** Current version
* **Chrome:** Current version
* **Firefox:** Current version
* **Safari:** Current version
* **Opera:** Current version

Mobile Browser Support:
-----------------------
* **Safari iOS:** Current version
* **Android Browser** Current version


Hypervisor Distro Support
=========================

Kimchi might run on any GNU/Linux distribution that meets the conditions
described on the 'Getting Started' section below.

The Kimchi community makes an effort to test it with the latest versions of
Fedora, RHEL, OpenSuSe, and Ubuntu.

Getting Started
===============

Install Dependencies
--------------------

**For fedora and RHEL:**

     $ sudo yum install wok libvirt-python libvirt \
                        libvirt-daemon-config-network python-imaging \
                        qemu-kvm python-ethtool sos python-ipaddr \
                        nfs-utils iscsi-initiator-utils pyparted \
                        python-libguestfs libguestfs-tools \
                        python-websockify novnc spice-html5 \
                        python-configobj python-magic python-paramiko

     # If using RHEL, install the following additional packages:
     $ sudo yum install python-unittest2 python-ordereddict

     # Restart libvirt to allow configuration changes to take effect
     $ sudo service libvirtd restart

    # These dependencies are only required if you want to run the tests:
    $ sudo yum install pyflakes python-pep8 python-requests
    $ sudo pip install mock


*Note for RHEL users*: Some of the above packages are located in the Red Hat
EPEL repositories.  See
[this FAQ](http://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F)
for more information on how to configure your system to access this repository.

And for RHEL7 systems, you also need to subscribe to the "RHEL Server Optional"
channel at RHN Classic or Red Hat Satellite.

**For Ubuntu (Debian-based):**

    $ sudo apt-get install wok python-imaging python-configobj websockify \
                           novnc python-libvirt libvirt-bin nfs-common \
                           qemu-kvm python-parted python-ethtool sosreport \
                           xsltproc python-ipaddr python-lxml open-iscsi \
                           python-guestfs libguestfs-tools spice-html5 \
                           python-magic python-paramiko \

    # These dependencies are only required if you want to run the tests:
    $ sudo apt-get install pep8 pyflakes python-requests

**For openSUSE:**

    $ sudo zypper install wok libvirt-python libvirt \
                          libvirt-daemon-config-network python-imaging \
                          kvm python-ethtool python-ipaddr nfs-client \
                          open-iscsi python-parted python-libguestfs \
                          python-configobj guestfs-tools python-websockify \
                          novnc python-magic

    # These dependencies are only required if you want to run the tests:
    $ sudo zypper install python-pyflakes python-pep8 python-requests

*Note for openSUSE users*: Some of the above packages are located in different
openSUSE repositories. See
[this FAQ](http://download.opensuse.org/repositories/home:GRNET:synnefo/) for
python-parted, [this FAQ](http://download.opensuse.org/repositories/systemsmanagement:/spacewalk/)
for python-ethtool, and [this FAQ](http://download.opensuse.org/repositories/home:/Simmphonie:/python/) for python-magic to get the correct repository based on your openSUSE version. And
[this FAQ](http://en.opensuse.org/SDB:Add_package_repositories) for more
information on how configure your system to access this repository.

Build and Install
-----------------

    Wok:
    $ ./autogen.sh --system

    $ make
    $ sudo make install   # Optional if running from the source tree


    Kimchi:
    $ cd plugins/kimchi

    For openSUSE 13.1:
    $ ./autogen.sh --with-spice-html5

    Otherwise:
    $ ./autogen.sh --system

    $ make
    $ sudo make install   # Optional if running from the source tree

Run
---

    $ sudo wokd --host=0.0.0.0

If you cannot access Wok, take a look at these 2 points:

1. Firewall
Wok uses by default the ports 8000, 8001 and 64667. To allow incoming connections:

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
Allow httpd_t context for Wok web server:

    semanage permissive -a httpd_t


Test
----

    $ cd plugins/kimchi
    $ make check-local # check for i18n and formatting errors
    $ sudo make check

After all tests are executed, a summary will be displayed containing any
errors/failures which might have occurred.

Usage
-----

Connect your browser to https://localhost:8001.  You should see a screen like:

![Wok Login Screen](/docs/kimchi-login.png)

Wok uses PAM to authenticate users so you can log in with the same username
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
