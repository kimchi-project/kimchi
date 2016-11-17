* [What is Kimchi?](#what-is-kimchi)
* [Browser Support](https://github.com/kimchi-project/wok/#browser-support)
    * [Desktop Browser Support](https://github.com/kimchi-project/wok/#desktop-browser-support)
    * [Mobile Browser Support](https://github.com/kimchi-project/wok/#mobile-browser-support)
* [Linux Support](https://github.com/kimchi-project/wok/#linux-support)
* [Getting started](#getting-started)
    * [Install Dependencies](#install-dependencies)
    * [Build and Install](#build-and-install)
    * [Starting up Wok](https://github.com/kimchi-project/wok/#starting-up-wok)
    * [Troubleshooting](#troubleshooting)
    * [Testing](#testing)
    * [Usage](#usage)
* [Contributing to Kimchi Project](#contributing-to-kimchi-project)

What is Kimchi?
===============

Kimchi is an HTML5 based management tool for KVM. It is designed to make it as
easy as possible to get started with KVM and create your first guest.

Kimchi runs as a [Wok](https://github.com/kimchi-project/wok/wiki) plugin.

Kimchi manages KVM guests through libvirt. The management interface is accessed
over the web using a browser that supports HTML5.

Getting Started
===============

Install Dependencies
--------------------
First of all, make sure to [Wok](https://github.com/kimchi-project/wok/#getting-started)
and [Ginger Base](https://github.com/kimchi-project/gingerbase/#getting-started) installed in your system.
To add Kimchi plugin, please make sure to have all the dependencies installed
before starting up the wokd service.

* [RHEL/Fedora systems](/docs/fedora-deps.md)
* [Debian/Ubuntu systems](/docs/ubuntu-deps.md)
* [openSUSE systems](/docs/opensuse-deps.md)

Build and Install
-----------------

    For openSUSE:
    $ ./autogen.sh --with-spice-html5

    Otherwise:
    $ ./autogen.sh --system

    $ make

    # Optional if running from the source tree
    $ sudo make install

Testing
-------

    $ make check-local
    $ sudo make check

After all tests are executed, a summary will be displayed containing any
errors/failures which might have occurred.

Usage
-----

Connect your browser to https://localhost:8001.  You should see a screen like:

![Wok Login Screen](/docs/wok-login.png)

By default, wok uses PAM to authenticate users so you can log in with the same username
and password that you would use to log in to the machine itself.  Once logged in
you will see a screen like:

![Kimchi Guest View](/docs/kimchi-guests.png)

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

To create a template, you need an ISO or image file on your host or use a remote one.
If you are willing to use your own ISO, please copy it to out of box storage
pool (default path is: /var/lib/kimchi/isos).

Troubleshooting
---------------

#### Server access
Please, check [Wok configuration](https://github.com/kimchi-project/wok/#troubleshooting)
if you are getting problems to access Wok server.

#### NFS storage pool
Please, check the NFS export path permission is configured like below:

1. Export path need to be squashed as kvm gid and libvirt uid:
    /my_export_path *(all_squash,anongid=<kvm-gid>, anonuid=<libvirt-uid>,rw,sync)

    So that root user can create volume with right user/group.

2. Set libvirt user and kvm group for export path, in order to make sure all
mapped user can get into the mount point.

Contributing to Kimchi Project
==============================

There are many ways to contribute to the Kimchi Project:

* Issues can be reported at [Github](https://github.com/kimchi-project/kimchi/issues)
* Patches are always welcome! Please, follow [these instructions](https://github.com/kimchi-project/kimchi/wiki/How-to-Contribute)
 on how to send patches to the mailing list (kimchi-devel@ovirt.org).

Find more information about Wok Project at https://github.com/kimchi-project/kimchi/wiki
