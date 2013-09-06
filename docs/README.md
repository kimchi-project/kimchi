Kimchi Project
==============

Kimchi is an HTML5 based management tool for KVM.  It is designed to make it
as easy as possible to get started with KVM and create your first guest.

Browser Support
===============
Desktop Browser Support:
-----------------------
* **Internet Explorer:** IE9+ (Partial support for IE8)
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

    $ sudo yum install gcc make python-cherrypy python-cheetah \
                       python-imaging libvirt-python libvirt \
                       gettext-devel automake autoconf

Install Dependecies for RHEL6
----------------------------
    $ sudo yum install python-unittest2 python-ordereddict

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

Connect your browser to localhost:8000.  You should see a screen like:

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
