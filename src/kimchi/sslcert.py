#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2014
# Copyright (C) 2004-2005 OSAF. All Rights Reserved.
#
# Portions of this file were derived from the python-m2crypto unit tests:
#     http://svn.osafoundation.org/m2crypto/trunk/tests/test_x509.py
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import time


from M2Crypto import ASN1, EVP, RSA, X509


class SSLCert(object):
    def __init__(self):
        self._gen()

    def _gen(self):
        def keygen_cb(*args):
            pass

        def passphrase_cb(*args):
            return ''

        self.cert = X509.X509()
        pubkey = EVP.PKey()
        rsa = RSA.gen_key(2048, 65537, keygen_cb)
        pubkey.assign_rsa(rsa)
        self._key = rsa.as_pem(None, callback=passphrase_cb)
        rsa = None

        # Set a serial number that is unlikely to repeat
        sn = int(time.time()) % (2 ** 32 - 1)
        self.cert.set_serial_number(sn)
        self.cert.set_version(2)

        subject = self.cert.get_subject()
        subject.C = 'US'
        subject.CN = 'kimchi'
        subject.O = 'kimchi-project.org'

        t = long(time.time()) + time.timezone
        now = ASN1.ASN1_UTCTIME()
        now.set_time(t)
        nowPlusYear = ASN1.ASN1_UTCTIME()
        nowPlusYear.set_time(t + 60 * 60 * 24 * 365)
        self.cert.set_not_before(now)
        self.cert.set_not_after(nowPlusYear)

        issuer = X509.X509_Name()
        issuer.CN = 'kimchi'
        issuer.O = 'kimchi-project.org'
        self.cert.set_issuer(issuer)

        self.cert.set_pubkey(pubkey)
        self.cert.sign(pubkey, 'sha1')

    def cert_text(self):
        return self.cert.as_text()

    def cert_pem(self):
        return self.cert.as_pem()

    def key_pem(self):
        return self._key


def main():
    c = SSLCert()
    print c.cert_text()
    print c.cert_pem()
    print c.key_pem()

if __name__ == '__main__':
    main()
