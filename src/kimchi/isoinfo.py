#
# Project Kimchi
#
# Copyright IBM, Corp. 2013-2015
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

import contextlib
import glob
import platform
import os
import re
import stat
import struct
import sys
import urllib2


from kimchi.exception import IsoFormatError
from kimchi.utils import check_url_path, kimchi_log


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
    ('sles', '12', 'SLE-12'),
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
    ('rhel', lambda m: m.group(2), 'RHEL(-LE)?[_/-](\d+\.\d+)'),
    ('debian', lambda m: m.group(1), 'Debian (\d+\.\d+)'),
    ('ubuntu', lambda m: m.group(2), '[Uu]buntu(-Server)? (\d+\.\d+)'),
    ('fedora', lambda m: m.group(1), 'Fedora[ -](\d+)'),
    ('fedora', lambda m: m.group(1), 'Fedora.*-(\d+)-'),
    ('gentoo', lambda m: m.group(1), 'Gentoo Linux \w+ (\d+)'),
    ('powerkvm', 'live_cd', 'POWERKVM_LIVECD'),
    ('arch', lambda m: m.group(1), 'ARCH_(\d+)'),
]


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
    # Path table info starting in ISO9660 offset 132. We force little
    # endian byte order (the '<' sign) because Power systems can run on
    # both.
    # First int is path table size, next 4 bytes are discarded (it is
    # the same info but in big endian) and next int is the location.
    PATH_TABLE_SIZE_LOC = struct.Struct("<I 4s I")

    def __init__(self, path):
        self.path = path
        self.remote = self._is_iso_remote()
        self.volume_id = None
        self.bootable = False
        self._scan()

    def _is_iso_remote(self):
        if os.path.exists(self.path):
            st_mode = os.stat(self.path).st_mode
            if stat.S_ISREG(st_mode) or stat.S_ISBLK(st_mode):
                return False

        if check_url_path(self.path):
            return True

        raise IsoFormatError("KCHISO0001E", {'filename': self.path})

    def probe(self):
        if not self.bootable:
            raise IsoFormatError("KCHISO0002E", {'filename': self.path})

        matcher = Matcher(self.volume_id)

        for d, v, regex in iso_dir:
            if matcher.search(regex):
                distro = d
                if hasattr(v, '__call__'):
                    version = v(matcher)
                else:
                    version = v
                return (distro, version)

        msg = "probe_iso: Unable to identify ISO %s with Volume ID: %s"
        kimchi_log.debug(msg, self.path, self.volume_id)

        return ('unknown', 'unknown')

    def _unpack(self, s, data):
        return s.unpack(data[:s.size])

    def _scan_el_torito(self, data):
        """
        Search the Volume Descriptor Table for an El Torito boot record.  If
        found, the boot record will provide a link to a boot catalogue.  The
        first entry in the boot catalogue is a validation entry.  The next
        entry contains the default boot entry. The default boot entry will
        indicate whether the image is considered bootable.
        """
        vd_type = -1
        for i in xrange(1, 4):
            fmt = IsoImage.EL_TORITO_BOOT_RECORD
            ptr = i * IsoImage.SECTOR_SIZE
            tmp_data = data[ptr:ptr + fmt.size]
            if len(tmp_data) < fmt.size:
                return

            (vd_type, vd_ident, vd_ver,
             et_ident, pad0, boot_cat) = self._unpack(fmt, tmp_data)
            if vd_type == 255:  # Volume record terminator
                return
            if vd_type == 0:  # Found El-Torito Boot Record
                break
        if not et_ident.startswith('EL TORITO SPECIFICATION'):
            raise IsoFormatError("KCHISO0003E",
                                 {'filename': self.path})

        offset = IsoImage.SECTOR_SIZE * boot_cat
        size = IsoImage.EL_TORITO_VALIDATION_ENTRY.size + \
            IsoImage.EL_TORITO_BOOT_ENTRY.size
        data = self._get_iso_data(offset, size)

        fmt = IsoImage.EL_TORITO_VALIDATION_ENTRY
        tmp_data = data[0:fmt.size]
        ptr = fmt.size
        (hdr_id, platform_id, pad0,
         ident, csum, key55, keyAA) = self._unpack(fmt, tmp_data)
        if key55 != 0x55 or keyAA != 0xaa:
            raise IsoFormatError("KCHISO0004E",
                                 {'filename': self.path})

        fmt = IsoImage.EL_TORITO_BOOT_ENTRY
        tmp_data = data[ptr:ptr + fmt.size]
        (boot, media_type, load_seg, sys_type,
         pad0, sectors, load_rba) = self._unpack(fmt, tmp_data)
        if boot == 0x88:
            self.bootable = True
        elif boot == 0:
            self.bootable = False
        else:
            raise IsoFormatError("KCHISO0005E",
                                 {'filename': self.path})

    def _scan_ppc(self):
        """
        PowerPC firmware does not use the conventional El Torito boot
        specification. Instead, it looks for a file '/ppc/bootinfo.txt'
        which contains boot information. A PPC image is bootable if
        this file exists in the filesystem [1].

        To detect if a PPC ISO is bootable, we could simply mount the
        ISO and search for the boot file as we would with any other
        file in the filesystem. We can also look for the boot file
        searching byte by byte the ISO image. This is possible because
        the PPC ISO image follows the ISO9660 standard [2]. Mounting
        the ISO requires extra resources and it takes longer than
        searching the image data, thus we chose the latter approach
        in this code.

        To locate a file we must access the Path Table, which contains
        the records of all the directories in the ISO. After locating
        the directory/subdirectory that contains the file, we access
        the Directory Record to find it.


        .. [1] https://www.ibm.com/developerworks/community/wikis/home?\
lang=en#!/wiki/W51a7ffcf4dfd_4b40_9d82_446ebc23c550/page/PowerLinux\
%20Boot%20howto
        .. [2] http://wiki.osdev.org/ISO_9660
        """

        # To locate any file we must access the Path Table, which
        # contains the records of all the directories in the ISO.
        # ISO9660 dictates that the Path Table location information
        # is at offset 132, inside the Primary Volume Descriptor,
        # after the SystemArea (16*SECTOR_SIZE).
        #
        # In the Path table info we're forcing little endian byte
        # order (the '<' sign) because Power systems can run on
        # both.
        #
        # First int is path table size, next 4 bytes are discarded (it is
        # the same info but in big endian) and next int is the location.
        PATH_TABLE_LOC_OFFSET = 16 * IsoImage.SECTOR_SIZE + 132
        PATH_TABLE_SIZE_LOC = struct.Struct("<I 4s I")

        path_table_loc_data = self._get_iso_data(PATH_TABLE_LOC_OFFSET,
                                                 PATH_TABLE_SIZE_LOC.size)
        path_size, unused, path_loc = self._unpack(PATH_TABLE_SIZE_LOC,
                                                   path_table_loc_data)
        # Fetch the Path Table using location and size found above
        path_table_offset = path_loc * IsoImage.SECTOR_SIZE
        path_table_data = self._get_iso_data(path_table_offset, path_size)

        # Loop inside the path table to find the directory 'ppc'.
        # The contents of the registers are:
        # - length of the directory identifier (1 byte)
        # - extended attribute record length (1 byte)
        # - location of directory register (4 bytes)
        # - directory number of parent dir (2 bytes)
        # - directory name (size varies according to length)
        # - padding field - 1 byte if the length is odd, not present if even
        DIR_NAMELEN_LOCATION_PARENT = struct.Struct("<B B I H")
        dir_struct_size = DIR_NAMELEN_LOCATION_PARENT.size
        i = 0
        while i < path_size:
            dir_data = path_table_data[i: i+dir_struct_size]
            i += dir_struct_size
            # We won't use the Extended Attribute Record
            dir_namelen, unused, dir_loc, dir_parent = \
                self._unpack(DIR_NAMELEN_LOCATION_PARENT, dir_data)
            if dir_parent == 1:
                # read the dir name using the namelen
                dir_name = path_table_data[i: i+dir_namelen].rstrip()
                if dir_name.lower() == 'ppc':
                    # stop searching, dir was found
                    break
            # Need to consider the optional padding field as well
            i += dir_namelen + dir_namelen % 2

        if i > path_size:
            # Didn't find the '/ppc' directory. ISO is not bootable.
            self.bootable = False
            return

        # Get the 'ppc' directory record using 'dir_loc'.
        ppc_dir_offset = dir_loc * IsoImage.SECTOR_SIZE

        # We need to find the sector size of this dir entry. The
        # size of the File Section is located 10 bytes after
        # the dir location.
        DIR_SIZE_FMT = struct.Struct("<10sI")
        data = self._get_iso_data(ppc_dir_offset, DIR_SIZE_FMT.size)
        unused, dir_size = self._unpack(DIR_SIZE_FMT, data)
        # If the dir is in the middle of a sector, the sector is
        # padded zero and won't be utilized. We need to round up
        # the result
        dir_sectorsize = dir_size / IsoImage.SECTOR_SIZE
        if dir_size % IsoImage.SECTOR_SIZE:
            dir_sectorsize += 1

        # Fixed-size directory record fields:
        # - length of directory record (1 byte)
        # - extended attr. record length (1 byte)
        # - location of extend in both-endian format (8 bytes)
        # - data length (size of extend) in both-endian (8 bytes)
        # - recording date and time (7 bytes)
        # - file flags (1 byte)
        # - file unit size interleaved (1 byte)
        # - interleave gap size (1 byte)
        # - volume sequence number (4 bytes)
        # - length of file identifier (1 byte)
        #
        #  Of all these fields, we will use only 3 of them, 'ignoring'
        #  30 bytes total.
        STATIC_DIR_RECORD_FMT = struct.Struct("<B 24s B 6s B")
        static_rec_size = STATIC_DIR_RECORD_FMT.size

        # Maximum offset possible of all the records of this directory
        DIR_REC_MAX = ppc_dir_offset + dir_sectorsize*IsoImage.SECTOR_SIZE
        # Max size of a given directory record
        MAX_DIR_SIZE = 255
        # Name of the boot file
        BOOT_FILE_NAME = "bootinfo.txt"

        # Loop until one of the following happens:
        # - boot file is found
        # - end of directory record listing for the 'ppc' dir
        while ppc_dir_offset < DIR_REC_MAX:
            record_data = self._get_iso_data(ppc_dir_offset, MAX_DIR_SIZE)
            dir_rec_len, unused, file_flags, unused2, file_name_len = \
                self._unpack(STATIC_DIR_RECORD_FMT, record_data)

            # if dir_rec_len = 0, increment offset (skip the
            # dir_rec_len byte) and continue the loop
            if dir_rec_len == 0:
                ppc_dir_offset += 1
                continue

            # Get filename of the file/dir we're at.
            filename = record_data[static_rec_size:
                                   static_rec_size + file_name_len].rstrip()
            # The second bit of the file_flags indicate if this record
            # is a directory.
            if BOOT_FILE_NAME in filename.lower() and (file_flags & 2) != 1:
                self.bootable = True
                return

            # Update offset and keep looking. There is a padding here
            # if the length of the file identifier is EVEN.
            padding = 0
            if not file_name_len % 2:
                padding = 1
            ppc_dir_offset += dir_rec_len + padding
        # If reached this point the file wasn't found = not bootable
        self.bootable = False

    def _scan_primary_vol(self, data):
        """
        Scan one sector for a Primary Volume Descriptor and extract the
        Volume ID from the table
        """
        primary_vol_data = data[0: -1]
        info = self._unpack(IsoImage.VOL_DESC, primary_vol_data)
        (vd_type, vd_ident, vd_ver, pad0, sys_id, vol_id) = info
        if vd_type != 1:
            raise IsoFormatError("KCHISO0006E", {'filename': self.path})
        if vd_ident != 'CD001' or vd_ver != 1:
            raise IsoFormatError("KCHISO0007E", {'filename': self.path})
        if vol_id.strip() == 'RED_HAT':
            # Some RHEL ISO images store the infomation of volume id in the
            # location of volume set id mistakenly.
            self.volume_id = self._get_volume_set_id(data)
        else:
            self.volume_id = vol_id

    def _get_volume_set_id(self, data):
        # The index is picked from ISO-9660 specification.
        return data[190: 318]

    def _get_iso_data(self, offset, size):
        if self.remote:
            request = urllib2.Request(self.path)
            range_header = "bytes=%d-%d" % (offset, offset + size - 1)
            request.add_header("range", range_header)
            with contextlib.closing(urllib2.urlopen(request)) as response:
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
        if platform.machine().startswith('ppc'):
            self._scan_ppc()
        else:
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


def probe_iso(status_helper, params):
    loc = params['path'].encode("utf-8")
    updater = params['updater']
    ignore = False
    ignore_list = params.get('ignore_list', [])

    def update_result(iso, ret):
        path = os.path.abspath(iso) if os.path.isfile(iso) else iso
        updater({'path': path, 'distro': ret[0], 'version': ret[1]})

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
                    iso_img = IsoImage(iso)
                    ret = iso_img.probe()
                    update_result(iso, ret)
                except:
                    continue
    else:
        iso_img = IsoImage(loc)
        ret = iso_img.probe()
        update_result(loc, ret)

    if status_helper is not None:
        status_helper('', True)


if __name__ == '__main__':
    iso_list = []

    def updater(iso_info):
        iso_list.append(iso_info)

    probe_iso(None, dict(path=sys.argv[1], updater=updater))
    print iso_list
