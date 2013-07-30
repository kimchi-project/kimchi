Kimchi Project
==============

Kimchi is an HTML5 based management tool for KVM.  It is designed to make it
as easy as possible to get started with KVM and create your first guest.

Getting Started
===============

Install Dependencies
--------------------

    $ sudo yum install python-cherrypy python-cheetah \
                       python-imaging libvirt-python libvirt \
                       gettext-devel

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
