Kimchi Project - Federation Feature
===================================

Federation feature is a Kimchi mechanism to discover Wok peers in the same
network. It uses openSLP tool (http://www.openslp.org/) to register and find Wok
servers.

By default this feature is disabled on Wok as it is not critical for KVM
virtualization and requires additional software installation.

To enable it, do the following:

1. Install openslp and openslp-server rpm packages,
   or install slpd and slptool deb packages.

2. openSLP uses port 427 (UDP) and port 427 (TCP) so make sure to open those
   ports in your firewall configuration

   For system using firewalld, do:
   sudo firewall-cmd --permanent --add-port=427/udp
   sudo firewall-cmd --permanent --add-port=427/tcp
   sudo firewall-cmd --reload

   For openSUSE systems, do:
   sudo /sbin/SuSEfirewall2 open EXT TCP 427
   sudo /sbin/SuSEfirewall2 open EXT UDP 427

   For system using iptables, do:
   sudo iptables -A INPUT -p tcp --dport 427 -j ACCEPT
   sudo iptables -A INPUT -p udp --dport 427 -j ACCEPT

3. In addition to the openSLP ports, you also need to allow multicast in the
   firewall configuration

   For system using firewalld, do:
   sudo firewall-cmd --direct --add-rule ipv4 filter INPUT 0 -s <subnet> -j ACCEPT

   For openSUSE systems, do:
   Add the subnet to the trusted networks listed on FW_TRUSTED_NETS in
   /etc/sysconfig/SuSEfirewall2 file.
   Make sure to restart /sbin/SuSEfirewall2 after modifying /etc/sysconfig/SuSEfirewall2

   For system using iptables, do:
   sudo iptables -A INPUT -s <subnet> -j ACCEPT

4. Start slpd service and make sure it is up while running Wok
   sudo service slpd start

5. Enable federation on Wok by editing the /etc/wok/wok.conf file:

   federation = on

6. Then start Wok service
   sudo service wokd start

The Wok server will be registered on openSLP on server starting up and will
be found by other Wok peers (with federation feature enabled) in the same
network.

Enjoy!
