Kimchi Project - Federation Feature
===================================

Federation feature is a mechanism to discover Kimchi peers in the same network.
It uses openSLP tool (http://www.openslp.org/) to register and find the Kimchi
servers.

By default this feature is disabled on Kimchi as it is not critical for KVM
virtualization and requires additional software installation.

To enable it, do the following:

1) Install openslp and openslp-server packages
2) openSLP uses port 427 (UDP) and port 427 (TCP) so make sure to open those
   ports in your firewall configuration
3) Start slpd service and make sure it is up while running Kimchi
4) Enable federation on Kimchi by editing the /etc/kimchi/kimchi.conf file:

   federation = on

5) Then restart Kimchi service

The Kimchi server will be registered on openSLP on server starting up and will
be found by other Kimchi peers (with federation feature enabled) in the same
network.

Enjoy!
