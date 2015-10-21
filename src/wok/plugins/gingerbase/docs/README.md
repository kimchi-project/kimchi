Ginger Base Plugin
==============

Ginger Base is an open source base host management plugin for Wok
(Webserver Originated from Kimchi), that provides an intuitive web panel with
common tools for configuring and managing the Linux systems.

Wok is a cherrypy-based web framework with HTML5 support that is extended by
plugins which expose functionality through REST APIs.

The current features of Base Host Management of Linux system include:
    + Shutdown, Restart, Connect
    + Basic Information
    + System Statistics
    + Software Updates
    + Repository Management
    + Debug Reports (SoS Reports)

Browser Support
===============

Desktop Browser Support:
-----------------------
* **Internet Explorer:** Current version
* **Chrome:** Current version
* **Firefox:** Current version
* **Safari:** Current version
* **Opera:** Current version

Mobile Browser Support:
-----------------------
* **Safari iOS:** Current-1 version
* **Android Browser** Current-1 version

Hypervisor Distro Support
=========================

Ginger Base and Wok might run on any GNU/Linux distribution that meets the conditions
described on the 'Getting Started' section below.

The Ginger community makes an effort to test it with the latest versions of
Fedora, RHEL, OpenSuSe, and Ubuntu.

Getting Started
===============

Install Dependencies
--------------------

**For fedora and RHEL:**

     $ sudo yum install wok gettext-devel git \
                        python-psutil sos python-lxml \
                        libxslt pyparted \
                        python-websockify python-configobj

     # If using RHEL, install the following additional packages:
     $ sudo yum install python-unittest2 python-ordereddict

    # These dependencies are only required if you want to run the tests:
    $ sudo yum install pyflakes python-pep8 python-requests

*Note for RHEL users*: Some of the above packages are located in the Red Hat
EPEL repositories.  See
[this FAQ](http://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F)
for more information on how to configure your system to access this repository.

And for RHEL7 systems, you also need to subscribe to the "RHEL Server Optional"
channel at RHN Classic or Red Hat Satellite.

**For debian:**

    $ sudo apt-get install wok gettext \
                           python-configobj \
                           python-psutil sosreport \
                           python-lxml xsltproc \
                           python-parted websockify

    Packages version requirement:
        python-jsonschema >= 1.3.0
        python-psutil >= 0.6.0

    # These dependencies are only required if you want to run the tests:
    $ sudo apt-get install pep8 pyflakes python-requests

**For openSUSE:**

    $ sudo zypper install wok gettext-tools \
                          python-psutil python-lxml \
                          libxslt-tools python-xml python-parted \
                          python-configobj python-websockify

    Packages version requirement:
        python-psutil >= 0.6.0

    # These dependencies are only required if you want to run the tests:
    $ sudo zypper install python-pyflakes python-pep8 python-requests

*Note for openSUSE users*: Some of the above packages are located in different
openSUSE repositories. See
[this FAQ](http://download.opensuse.org/repositories/home:GRNET:synnefo/) for
python-parted; And
[this FAQ](http://en.opensuse.org/SDB:Add_package_repositories) for more
information on how configure your system to access this repository.

Build and Install
-----------------

    Wok:
    $ ./autogen.sh --system

    $ make
    $ sudo make install   # Optional if running from the source tree

    Ginger Base:
    $ cd plugins/gingerbasae

    $ ./autogen.sh --system

    $ make
    $ sudo make install   # Optional if running from the source tree

Run
---

    $ systemctl start wokd

Test
----

    $ cd plugins/gingerbase
    $ make check-local # check for i18n and formatting errors
    $ sudo make check

After all tests are executed, a summary will be displayed containing any
 errors/failures which might have occurred.

Usage
-----

Connect your browser to https://localhost:8001.
Once logged in you could see host tab which provides the gingerbase functionality.

Wok uses PAM to authenticate users so you can log in with the same username
and password that you would use to log in to the machine itself.

![Ginger Base Host Screen](docs/gingerbase-host-tab.png)

Ginger Base Host tab provides the base host functionality like system information,
 system statistics, software updates, repositories and debug reports functionality.

Also Ginger Base provides shutdown, re-start and connect options.

Participating
-------------

All patches are sent through our mailing list.  More information can be found at:

https://github.com/kimchi-project/ginger/wiki/Communications

Patches should be sent using git-send-email to ginger-dev-list@googlegroups.com