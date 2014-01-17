Kimchi Project
==============

Kimchi is an HTML5 based management tool for KVM.  It is designed to make it
as easy as possible to get started with KVM and create your first guest.

Browser Support
===============
Desktop Browser Support:
-----------------------
* **Internet Explorer:** IE9+
* **Chrome:** Current-1 version
* **Firefox:** Current-1 version Firefox 17ESR
* **Safari:** Current-1 version
* **Opera:** Current-1 version

Mobile Browser Support:
-----------------------
* **Safari iOS:** Current-1 version
* **Android Browser** Current-1 version

Current-1 version denotes that we support the current stable version of the browser and the version
that preceded it. For example, if the current version of a browser is 24.x, we support the 24.x and
23.x versions.This does not mean that kimchi cannot be used in other browsers, however, functionality
and appearance may be diminished and we may not be able to provide support for any problems you find.

Getting Started
===============

Install Dependencies
--------------------

**For fedora and RHEL:**

     $ sudo yum install gcc make autoconf automake gettext-devel git \
                        python-cherrypy python-cheetah libvirt-python \
                        libvirt libxml2-python python-imaging \
                        PyPAM m2crypto python-jsonschema rpm-build \
                        qemu-kvm python-psutil python-ethtool sos \
                        python-ipaddr python-lxml nfs-utils \
                        iscsi-initiator-utils
     # If using RHEL6, install the following additional packages:
     $ sudo yum install python-unittest2 python-ordereddict
     # Restart libvirt to allow configuration changes to take effect
     $ sudo service libvirtd restart

    Packages version requirement:
        python-psutil >= 0.6.0

*Note for RHEL users*: Some of the above packages are located in the Red Hat
EPEL repositories.  See
[this FAQ](http://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F)
for more information on how to configure your system to access this repository.

**For debian:**

    $ sudo apt-get install gcc make autoconf automake gettext git \
                           python-cherrypy3 python-cheetah python-libvirt \
                           libvirt-bin python-libxml2 python-imaging \
                           python-pam python-m2crypto python-jsonschema \
                           qemu-kvm libtool python-psutil python-ethtool \
                           sosreport python-ipaddr python-lxml nfs-common \
                           open-iscsi

    Packages version requirement:
        python-jsonschema >= 1.3.0
        python-psutil >= 0.6.0

**For openSUSE:**

    $ sudo zypper install gcc make autoconf automake gettext-tools git \
                          python-CherryPy python-Cheetah libvirt-python \
                          libvirt python-libxml2 python-imaging \
                          python-pam python-M2Crypto python-jsonschema \
                          rpm-build kvm python-psutil python-ethtool \
                          python-ipaddr python-lxml nfs-client open-iscsi

    Packages version requirement:
        python-psutil >= 0.6.0

*Note for openSUSE users*: Some of the above packages are located in the openSUSE
Systems Management repository. See
[this FAQ](http://download.opensuse.org/repositories/systemsmanagement:/spacewalk/)
to get the correct repository based on your openSUSE version. And
[this FAQ](http://en.opensuse.org/SDB:Add_package_repositories) for more
information on how configure your system to access this repository.

Build and Install
-----------------

    $ ./autogen.sh --system
    $ make
    $ sudo make install   # Optional if running from the source tree

Run
---

    $ sudo kimchid --host=0.0.0.0

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

Known Issues
------------

Kimchi is still experimental and should not be used in a production
environment.

Participating
-------------

All patches are sent through our mailing list hosted at Google Groups.  More
information can be found at:

https://groups.google.com/forum/#!forum/project-kimchi

Patches should be sent using git-send-email.
