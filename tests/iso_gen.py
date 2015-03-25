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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import platform
import struct

from kimchi.isoinfo import IsoImage

iso_des = [
    ('openbsd', lambda v: True,
        lambda v: 'OpenBSD/i386    %s Install CD' % v),
    ('centos', lambda v: True, lambda v: 'CentOS_%s_Final' % v),
    ('windows', '2000', 'W2AFPP'),
    ('windows', 'xp', 'WXPFPP'),
    ('windows', '2003', 'ARMECHK'),
    ('windows', '2003r2', 'CRMEFPP'),
    ('windows', '2008', 'KRTMSVOL'),
    ('windows', '2008r2', 'GRMSXVOL'),
    ('windows', 'vista', 'FB1EVOL'),
    ('windows', '7', 'GRMCULFRER'),
    ('windows', '8', 'HB1_CCPA_X86FRE'),
    ('sles', '10', 'SLES10'),
    ('sles', '11', 'SUSE_SLES-11-0-0'),
    ('opensuse', '11.1', 'SU1110.001'),
    ('opensuse', '11.3', 'openSUSE-DVD-x86_64.0702..001'),
    ('opensuse', '11.4', 'openSUSE-DVD-x86_640024'),
    ('opensuse', '12.1', 'openSUSE-DVD-x86_640039'),
    ('opensuse', '12.2', 'openSUSE-DVD-x86_640167'),
    ('opensuse', lambda v: True, lambda v: 'openSUSE-%s' % v),
    ('rhel', '4.8', 'RHEL/4-U8'),
    ('rhel', lambda v: v.startswith('6.'), lambda v: 'RHEL_%s' % v),
    ('debian', lambda v: True, lambda v: 'Debian %s' % v),
    ('ubuntu',
     lambda v: v in ('7.10', '8.04', '8.10', '9.04', '9.10', '10.04', '10.10',
                     '11.04', '11.10', '12.04', '12.10', '13.04', '13.10',
                     '14.04'),
     lambda v: 'Ubuntu %s' % v),
    ('fedora',
     lambda v: v in ('16', '17', '18', '19'),
     lambda v: 'Fedora %s' % v)
]


class FakeIsoImage(object):
    def _build_iso(self, fd, iso_volid, bootable):
        if platform.machine().startswith('ppc'):
            self._build_powerpc_bootable_iso(fd, iso_volid)
            return
        self._build_intel_iso(fd, iso_volid, bootable)

    def _build_powerpc_bootable_iso(self, fd, iso_volid):
        self._build_prim_vol(fd, iso_volid)
        self._build_bootable_ppc_path_table(fd)

    def _build_intel_iso(self, fd, iso_volid, bootable):
        # Do not change the order of the method calls
        self._build_el_boot(fd, bootable)
        self._build_prim_vol(fd, iso_volid)
        self._build_el_torito(fd)

    def _build_prim_vol(self, fd, iso_volid):
        fd.seek(16 * IsoImage.SECTOR_SIZE)
        fmt = IsoImage.VOL_DESC
        vd_type = 1
        vd_ident = 'CD001'
        vd_ver = 1
        pad0 = 1
        sys_id = 'fake os'
        vol_id = iso_volid
        data = (vd_type, vd_ident, vd_ver, pad0, sys_id, vol_id)
        s = fmt.pack(*data)
        fd.write(s)
        self._add_sector_padding(fd, s)

    def _add_sector_padding(self, fd, s):
        padding_len = IsoImage.SECTOR_SIZE - len(s)
        fmt = struct.Struct('=%ss' % padding_len)
        s = fmt.pack('a' * padding_len)
        fd.write(s)

    def _build_el_torito(self, fd):
        fmt = IsoImage.EL_TORITO_BOOT_RECORD
        vd_type = 0
        vd_ident = 'CD001'
        vd_ver = 1
        et_ident = "EL TORITO SPECIFICATION:"
        pad0 = 'a' * 32
        boot_cat = 0
        data = (vd_type, vd_ident, vd_ver, et_ident, pad0, boot_cat)
        s = fmt.pack(*data)
        fd.write(s)
        self._add_sector_padding(fd, s)

    def _build_el_boot(self, fd, bootable):
        fmt = IsoImage.EL_TORITO_VALIDATION_ENTRY
        hdr_id = 0
        platform_id = 0
        pad0 = 1
        ident = 'c' * 24
        csum = 1
        key55 = 0x55
        keyAA = 0xaa
        data = (hdr_id, platform_id, pad0, ident, csum, key55, keyAA)
        s = fmt.pack(*data)
        fd.write(s)

        fmt = IsoImage.EL_TORITO_BOOT_ENTRY
        if bootable:
            boot = 0x88
        else:
            boot = 0
        media_type = 1
        load_seg = 1
        sys_type = 1
        pad0 = 1
        sectors = 1
        load_rba = 1
        data = (boot, media_type, load_seg, sys_type, pad0, sectors, load_rba)
        s = fmt.pack(*data)
        fd.write(s)

        s = 'a' * IsoImage.SECTOR_SIZE
        fd.write(s)

    def _build_bootable_ppc_path_table(self, fd):
        # write path table locator
        PATH_TABLE_LOC_OFFSET = 16 * IsoImage.SECTOR_SIZE + 132
        PATH_TABLE_SIZE_LOC = struct.Struct("<I 4s I")
        path_table_size = 64
        path_table_loc = 18
        fd.seek(PATH_TABLE_LOC_OFFSET)
        fmt = PATH_TABLE_SIZE_LOC
        data = (path_table_size, 4*'0', path_table_loc)
        s = fmt.pack(*data)
        fd.write(s)
        # write path table entry
        fd.seek(path_table_loc * IsoImage.SECTOR_SIZE)
        DIR_NAMELEN_LOCATION_PARENT = struct.Struct("<B B I H 3s")
        dir_namelen = 3
        dir_loc = 19
        dir_parent = 1
        dir_name = 'ppc'
        data = (dir_namelen, 0, dir_loc, dir_parent, dir_name)
        fmt = DIR_NAMELEN_LOCATION_PARENT
        s = fmt.pack(*data)
        fd.write(s)
        # write 'ppc' dir record
        ppc_dir_offset = dir_loc * IsoImage.SECTOR_SIZE
        fd.seek(ppc_dir_offset)
        STATIC_DIR_RECORD_FMT = struct.Struct("<B 9s I 11s B 6s B 12s")
        dir_rec_len = 1
        unused1 = 9 * '0'
        dir_size = 100
        unused2 = 11 * '0'
        file_flags = 0
        unused3 = 6 * '0'
        file_name_len = 12
        boot_file_name = "bootinfo.txt"
        data = (dir_rec_len, unused1, dir_size, unused2, file_flags,
                unused3, file_name_len, boot_file_name)
        fmt = STATIC_DIR_RECORD_FMT
        s = fmt.pack(*data)
        fd.write(s)


def construct_fake_iso(path, bootable, version, distro):
    iso = FakeIsoImage()

    for d, v, gen_id in iso_des:
        if d != distro:
            continue
        if hasattr(v, '__call__'):
            supported = v(version)
        else:
            supported = version == v

        if not supported:
            continue

        if hasattr(gen_id, '__call__'):
            vol_id = gen_id(version)
        else:
            vol_id = gen_id
        with open(path, 'w') as fd:
            return iso._build_iso(fd, vol_id, bootable)

    raise Exception("%s: %s not supported generation" % (distro, version))


if __name__ == '__main__':
    construct_fake_iso('centos.iso', True, '6.1', 'centos')
    construct_fake_iso('ubuntu12.04.iso', True, '12.04', 'ubuntu')
    construct_fake_iso('fedora17.iso', True, '17', 'fedora')
    construct_fake_iso('sles10.iso', True, '10', 'sles')
    construct_fake_iso('openbsd.iso', True, '5.0', 'openbsd')
