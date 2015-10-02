Wok (Webserver Originated from Kimchi)
======================================

Wok is a cherrypy-based web framework with HTML5 support that is extended by
plugins which expose functionality through REST APIs.

Examples of such plugins are Kimchi (Virtualization Management) and Ginger
(System Administration). Wok comes with a sample plugin for education purposes.

Wok runs through wokd daemon.


Browser Support
===============

Wok and its plugins can run in any web browser that supports HTML5. The
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

Wok might run on any GNU/Linux distribution that meets the conditions
described on the 'Getting Started' section below.

The Kimchi community (responsible for Wok project) makes an effort to
test it with the latest versions of Fedora, RHEL, OpenSUSE, and Ubuntu.

Getting Started
===============

Install Dependencies
--------------------

**For Fedora and RHEL:**

     $ sudo yum install gcc make autoconf automake gettext git \
                        python-cherrypy python-cheetah python-imaging\
                        PyPAM m2crypto python-jsonschema rpm-build \
                        python-psutil python-ldap python-lxml \
                        libxslt nginx openssl


     # If using RHEL, install the following additional packages:
     $ sudo yum install python-unittest2 python-ordereddict

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

**For Ubuntu (Debian-based):**

    $ sudo apt-get install gcc make autoconf automake gettext git \
                           python-cherrypy3 python-cheetah python-imaging \
                           python-pam python-m2crypto python-jsonschema \
                           python-psutil python-ldap python-lxml nginx \
                           libxslt openssl

    Packages version requirement:
        python-jsonschema >= 1.3.0
        python-psutil >= 0.6.0

    # These dependencies are only required if you want to run the tests:
    $ sudo apt-get install pep8 pyflakes python-requests

**For openSUSE:**

    $ sudo zypper install gcc make autoconf automake gettext-tools git \
                          python-CherryPy python-Cheetah python-pam \
                          python-imaging python-M2Crypto python-jsonschema \
                          rpm-build python-psutil python-ldap python-lxml \
                          libxslt-tools python-xml nginx openssl

    Packages version requirement:
        python-psutil >= 0.6.0

    # These dependencies are only required if you want to run the tests:
    $ sudo zypper install python-pyflakes python-pep8 python-requests


Build and Install
-----------------

    $ ./autogen.sh --system
    $ make
    $ sudo make install   # Optional if running from the source tree


Run
---

    $ sudo wokd --host=0.0.0.0

If you cannot access Wok, take a look at these 2 points:

1. Firewall:
Wok uses by default the ports 8000, 8001 and 64667. To allow incoming connections:

    For system using firewalld, do:

        $ sudo firewall-cmd --add-port=8000/tcp --permanent
        $ sudo firewall-cmd --add-port=8001/tcp --permanent
        $ sudo firewall-cmd --add-port=64667/tcp --permanent
        $ sudo firewall-cmd --reload

    For openSUSE systems, do:

        $ sudo /sbin/SuSEfirewall2 open EXT TCP 8000
        $ sudo /sbin/SuSEfirewall2 open EXT TCP 8001
        $ sudo /sbin/SuSEfirewall2 open EXT TCP 64667

    For system using iptables, do:

        $ sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
        $ sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
        $ sudo iptables -A INPUT -p tcp --dport 64667 -j ACCEPT

    Don't forget to correctly save the rules.

2. SELinux:
Allow httpd_t context for Wok web server:

        $ sudo semanage permissive -a httpd_t


Participating
-------------

All patches are sent through our mailing list hosted by oVirt.  More
information can be found at:

https://github.com/kimchi-project/kimchi/wiki/Communications

Patches should be sent using git-send-email to kimchi-devel@ovirt.org.
