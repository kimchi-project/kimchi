#
# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Adam Litke <agl@linux.vnet.ibm.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import glob
import os
import re
import struct
import sys
import urllib2


from kimchi.utils import kimchi_log

iso_dir = [
    ##
    # Portions of this data from libosinfo: http://libosinfo.org/
    #
    # Each tuple has the following three members:
    #  Distro ID: Nickname for the distro or OS family
    #  Distro Version: A function or string that provides a specific version
    #                  given a regular expression match on the volume id string
    #  Regular Expression: A regex to match against the ISO Volume ID
    ##
    ('openbsd', lambda m: m.group(2),
        ('OpenBSD/(i386|amd64)    (\d+\.\d+) Install CD')),
    ('centos', lambda m: m.group(1),
        ('CentOS_(\d+\.\d+)_Final')),
    ('windows', '2000',
        ('W2AFPP|SP1AFPP|SP2AFPP|YRMAFPP|ZRMAFPP|W2AOEM|SP1AOEM|SP2AOEM' +
         '|YRMAOEM|ZRMAOEM|W2ASEL|SP2ASEL|W2SFPP|SP1SFPP|SP2SFPP|YRMSFPP' +
         '|ZRMSFPP|W2SOEM|W2SOEM|SP1SOEM|SP2SOEM|YRMSOEM|ZRMSOEM|W2SSEL' +
         '|SP2SSEL|W2PFPP|SP1PFPP|SP2PFPP|YRMPFPP|ZRMPFPP|W2POEM|SP1POEM' +
         '|SP2POEM|YRMPOEM|ZRMPOEM|W2PSEL|SP2PSEL|W2PCCP|WIN2000|W2K_SP4')),
    ('windows', 'xp',
        ('WXPFPP|WXHFPP|WXPCCP|WXHCCP|WXPOEM|WXHOEM|WXPVOL|WXPEVL|XRMPFPP' +
         '|XRMHFPP|XRMPCCP|XRMHCCP|XRMPOEM|XRMHOEM|XRMPVOL|XRMSD2|X1APFPP' +
         '|X1AHFPP|X1APCCP|X1APCCP|X1AHCCP|X1APOEM|X1AHOEM|X1APVOL|VRMPFPP' +
         '|VRMHFPP|VRMPCCP|VRMHCCP|VRMPOEM|VRMHOEM|VRMPVOL|VRMSD2|VX2PFPP' +
         '|VX2HFPP|VX2PCCP|VX2HCCP|VX2POEM|VX2HOEM|VX2PRMFPP|VX2PVOL|GRTMUPD' +
         '|GRTMPFPP|GRTMPRMFPP|GRTMHFPP|GRTMHKFPP|GRTMHKNFPP|GRTMHRMFPP' +
         '|GRTMPOEM|GRTMHOEM|GRTMPVOL|GRTMPKNVOL|GRTMPKVOL|GRTMPRMVOL' +
         '|MX2PFPP|MRMSD2|ARMPXFPP|ARMPXCCP|ARMPXOEM|ARMPXVOL|AX2PXCFPP' +
         '|AX2PXFPP|NRMPIFPP')),
    ('windows', '2003',
        ('ARMECHK|ARMEVOL|ARMSVOL|ARMWVOL|ARMEEVL|ARMSEVL|ARMWEVL|ARMEOEM' +
         '|ARMDOEM|ARMSOEM|ARMWOEM|ARMEFPP|ARMDFPP|ARMSFPP|ARMWFPP|NRMECHK' +
         '|NRMEVOL|NRMSVOL|NRMWVOL|NRMEEVL|NRMSEVL|NRMWEVL|NRMEOEM|NRMDOEM' +
         '|NRMSOEM|NRMWOEM|NRMEFPP|NRMDFPP|NRMSFPP|NRMSFPP|CRMSVOL|CRMSXVOL' +
         '|BRMEVOL|BX2DVOL|ARMEEVL|BRMEEVL|CR0SP2|ARMEICHK|ARMEIFPP|ARMEIEVL' +
         '|ARMEIOEM|ARMDIOEM|ARMEXFPP|ARMDFPP|ARMSXFPP|CR0SPX2|NRMEICHK' +
         '|NRMEIFPP|NRMDIFPP|NRMEIOEM|NRMDIOEM|NRMEIVOL|NRMEIEVL|BRMEXVOL' +
         '|BX2DXVOL|ARMEIFPP|CR0SPI2')),
    ('windows', '2003r2',
        ('CRMEFPP|CRMSFPP|CR0SCD2|CR0ECD2|BX2SFPP|BX2EFPP|BRMECD2FRE' +
         '|BRMSCD2FRE|CRMEXFPP|CRMSXFPP|CR0SCD2X|CR0ECD2X|BX2SXFPP|BX2EXFPP' +
         '|BRMECD2XFRE|BRMSCD2XFRE|CRMDVOL|CRMDXVOL')),
    ('windows', '2008',
        ('KRTMSVOL|KRTMSCHK|KRMWVOL|KRMSVOL|KRTMSXVOL|KRTMSXCHK|KRMWXVOL' +
         '|KRMSXVOL')),
    ('windows', '2008r2',
        ('GRMSXVOL|GRMSXFRER|GRMSHXVOL|GRMSIAIVOL|SRVHPCR2')),
    ('windows', 'vista',
        ('FB1EVOL|LRMCFRE|FRTMBVOL|FRMBVOL|FRMEVOL|FB1EXVOL|LRMCXFRE' +
         '|FRTMBXVOL|FRMBXVOL|FRMEXVOL|LRMEVOL|LRMEXVOL')),
    ('windows', '7',
        ('GRMCULFRER|GSP1RMCNPRFRER|GSP1RMCNULFRER|GSP1RMCULFRER' +
         '|GSP1RMCPRFRER|GRMCENVOL|GRMCNENVOL|GRMCPRFRER|GSP1RMCPRVOL' +
         '|GRMCULXFRER|GSP1RMCPRXFRER|GSP1RMCNHPXFRER|GRMCHPXFRER|GRMCXCHK' +
         '|GSP1RMCENXVOL|GRMCENXVOL|GRMCNENXVOL|GRMCPRXFRER|GSP1RMCPRXVOL')),
    ('windows', '8',
        ('HB1_CCPA_X86FRE|HRM_CCSA_X86FRE|HRM_CCSA_X86CHK|HRM_CCSNA_X86CHK' +
         '|HRM_CCSNA_X86FRE|HRM_CENA_X86FREV|HRM_CENA_X86CHKV' +
         '|HRM_CENNA_X86FREV|HRM_CENNA_X86CHKV|HRM_CPRA_X86FREV' +
         '|HRM_CPRNA_X86FREV|HB1_CCPA_X64FRE|HRM_CCSA_X64FRE' +
         '|HRM_CCSA_X64CHK|HRM_CCSNA_X64FRE|HRM_CCSNA_X64CHK' +
         '|HRM_CENNA_X64FREV|HRM_CENNA_X64CHKV|HRM_CENA_X64FREV' +
         '|HRM_CENA_X64CHKV|HRM_CPRA_X64FREV|HRM_CPRNA_X64FREV')),
    ('sles', '10', 'SLES10|SUSE-Linux-Enterprise-Server.001'),
    ('sles', '11', 'SUSE_SLES-11-0-0'),
    ('sles', lambda m: "11sp%s" % m.group(1), 'SLES-11-SP(\d+)'),
    ('opensuse', lambda m: m.group(1), 'openSUSE[ -](\d+\.\d+)'),
    ('opensuse', '11.1', 'SU1110.001'),
    ('opensuse', '11.3',
        'openSUSE-DVD-i586-Build0702..001|openSUSE-DVD-x86_64.0702..001'),
    ('opensuse', '11.4',
        'openSUSE-DVD-i586-Build0024|openSUSE-DVD-x86_640024'),
    ('opensuse', '12.1',
        'openSUSE-DVD-i586-Build0039|openSUSE-DVD-x86_640039'),
    ('opensuse', '12.2',
        'openSUSE-DVD-i586-Build0167|openSUSE-DVD-x86_640167'),
    ('rhel', '4.8', 'RHEL/4-U8'),
    ('rhel', lambda m: m.group(1), 'RHEL[_/](\d+\.\d+)'),
    ('debian', lambda m: m.group(1), 'Debian (\d+\.\d+)'),
    ('ubuntu', lambda m: m.group(2), '[Uu]buntu(-Server)? (\d+\.\d+)'),
    ('fedora', lambda m: m.group(1), 'Fedora[ -](\d+)'),
    ('fedora', lambda m: m.group(1), 'Fedora.*-(\d+)-'),
]


class IsoFormatError(Exception):
    pass


class IsoImage(object):
    """
    Scan an iso9660 image to extract the Volume ID and check for boot-ability

    ISO-9660 specification:
    http://www.ecma-international.org/publications/standards/Ecma-119.htm

    El-Torito specification:
    http://download.intel.com/support/motherboards/desktop/sb/specscdrom.pdf
    """
    SECTOR_SIZE = 2048
    VOL_DESC = struct.Struct("=B5sBB32s32s")
    EL_TORITO_BOOT_RECORD = struct.Struct("=B5sB32s32sI")
    EL_TORITO_VALIDATION_ENTRY = struct.Struct("=BBH24sHBB")
    EL_TORITO_BOOT_ENTRY = struct.Struct("=BBHBBHL20x")

    def __init__(self, path, remote = False):
        self.path = path
        self.volume_id = None
        self.bootable = False
        self.remote = remote
        self._scan()

    def _unpack(self, s, data):
        return s.unpack(data[:s.size])

    def _scan_el_torito(self, data):
        """
        Search the Volume Descriptor Table for an El Torito boot record.  If
        found, the boot record will provide a link to a boot catalogue.  The
        first entry in the boot catalogue is a validation entry.  The next entry
        contains the default boot entry.  The default boot entry will indicate
        whether the image is considered bootable.
        """
        vd_type = -1
        for i in xrange(1, 4):
            fmt = IsoImage.EL_TORITO_BOOT_RECORD
            ptr = i * IsoImage.SECTOR_SIZE
            tmp_data = data[ptr:ptr+fmt.size]
            if len(tmp_data) < fmt.size:
                return

            (vd_type, vd_ident, vd_ver,
             et_ident, pad0, boot_cat) = self._unpack(fmt, tmp_data)
            if vd_type == 255:  # Volume record terminator
                return
            if vd_type == 0:  # Found El-Torito Boot Record
                break
        if not et_ident.startswith('EL TORITO SPECIFICATION'):
            raise IsoFormatError("Invalid El Torito boot record")

        offset = IsoImage.SECTOR_SIZE * boot_cat
        size = IsoImage.EL_TORITO_VALIDATION_ENTRY.size + IsoImage.EL_TORITO_BOOT_ENTRY.size
        data = self._get_iso_data(offset, size)

        fmt = IsoImage.EL_TORITO_VALIDATION_ENTRY
        tmp_data = data[0:fmt.size]
        ptr = fmt.size
        (hdr_id, platform_id, pad0,
         ident, csum, key55, keyAA) = self._unpack(fmt, tmp_data)
        if key55 != 0x55 or keyAA != 0xaa:
            raise IsoFormatError("Invalid El Torito validation entry")

        fmt = IsoImage.EL_TORITO_BOOT_ENTRY
        tmp_data = data[ptr:ptr+fmt.size]
        (boot, media_type, load_seg, sys_type,
         pad0, sectors, load_rba) = self._unpack(fmt, tmp_data)
        if boot == 0x88:
            self.bootable = True
        elif boot == 0:
            self.bootable = False
        else:
            raise IsoFormatError("Invalid El Torito boot indicator")

    def _scan_primary_vol(self, data):
        """
        Scan one sector for a Primary Volume Descriptor and extract the
        Volume ID from the table
        """
        primary_vol_data = data[0: -1]
        (vd_type, vd_ident, vd_ver,
         pad0, sys_id, vol_id) = self._unpack(IsoImage.VOL_DESC, primary_vol_data)
        if vd_type != 1:
            raise IsoFormatError("Unexpected volume type for primary volume")
        if vd_ident != 'CD001' or vd_ver != 1:
            raise IsoFormatError("Bad format while reading volume descriptor")
        self.volume_id = vol_id

    def _get_iso_data(self, offset, size):
        if self.remote:
            request = urllib2.Request(self.path)
            request.add_header("range", "bytes=%d-%d" % (offset, offset + size -1))
            response = urllib2.urlopen(request)
            data = response.read()
        else:
            with open(self.path) as fd:
                fd.seek(offset)
                data = fd.read(size)

        return data

    def _scan(self):
        offset = 16 * IsoImage.SECTOR_SIZE
        size = 4 * IsoImage.SECTOR_SIZE
        data = self._get_iso_data(offset, size)
        if len(data) < 2 * IsoImage.SECTOR_SIZE:
            return

        self._scan_primary_vol(data)
        self._scan_el_torito(data)


class Matcher(object):
    """
    Simple utility class to assist with matching a given string against a
    series of regular expressions.
    """
    def __init__(self, matchstring):
        self.matchstring = matchstring

    def search(self, regex):
        self.lastmatch = re.search(regex, self.matchstring)
        return bool(self.lastmatch)

    def group(self, num):
        return self.lastmatch.group(num)


def _probe_iso(fname, remote = False):
    try:
        iso = IsoImage(fname, remote)
    except Exception, e:
        kimchi_log.warning("probe_iso: Error processing ISO image: %s\n%s" %
                           (fname, e))
        raise IsoFormatError(e)

    if not iso.bootable:
        raise IsoFormatError("ISO %s not bootable" % fname)

    matcher = Matcher(iso.volume_id)

    for d, v, regex in iso_dir:
        if matcher.search(regex):
            distro = d
            if hasattr(v, '__call__'):
                version = v(matcher)
            else:
                version = v
            return (distro, version)

    kimchi_log.debug("probe_iso: Unable to identify ISO %s with Volume ID: %s"
                     % (fname, iso.volume_id))
    return ('unknown', 'unknown')


def probe_iso(status_helper, params):
    loc = params['path'].encode("utf-8")
    updater = params['updater']
    ignore = False
    ignore_list = params['ignore_list']

    def update_result(iso, ret):
        if ret != ('unknown', 'unknown'):
            iso = os.path.abspath(iso)
            updater({'path': iso, 'distro': ret[0], 'version': ret[1]})

    if os.path.isdir(loc):
        for root, dirs, files in os.walk(loc):
            for dir_name in ignore_list:
                if root in glob.glob(dir_name):
                    ignore = True
                    break
            if ignore:
                ignore = False
                continue
            for name in files:
                if not name.lower().endswith('.iso'):
                    continue
                iso = os.path.join(root, name)
                try:
                    ret = _probe_iso(iso)
                    update_result(iso, ret)
                except:
                    continue
    elif os.path.isfile(loc):
        ret = _probe_iso(loc, False)
        update_result(loc, ret)
    else:
        ret = _probe_iso(loc, True)
        update_result(loc, ret)

    if status_helper != None:
        status_helper('', True)

def _check_url_path(path):
    try:
        code = urllib2.urlopen(path).getcode()
        if code != 200:
            return False
    except (urllib2.HTTPError, ValueError):
        return False

    return True

def probe_one(iso):
    if os.path.isfile(iso):
        remote = False
    elif _check_url_path(iso):
        remote = True
    else:
        raise IsoFormatError('ISO %s does not exist' % iso)

    return _probe_iso(iso, remote)


if __name__ == '__main__':
    iso_list = []
    def updater(iso_info):
        iso_list.append(iso_info)
    probe_iso(None, dict(path=sys.argv[1], updater=updater))
    print iso_list
