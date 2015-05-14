Wok (Webserver Originated from Kimchi)
======================================

Wok is a cherrypy-based web framework with HTML5 support that is extended by
plugins which expose functionality through REST APIs.

Examples of such plugins are Kimchi (Virtualization Management) and Ginger
(System Administration). Wok comes with a sample plugin for education purposes.

Wok runs through wokd daemon.


Build and Install
-----------------

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


Participating
-------------

All patches are sent through our mailing list hosted by oVirt.  More
information can be found at:

https://github.com/kimchi-project/kimchi/wiki/Communications

Patches should be sent using git-send-email to kimchi-devel@ovirt.org.
