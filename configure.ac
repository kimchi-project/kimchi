#
# Kimchi
#
# Copyright IBM Corp, 2013
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

AC_INIT([kimchi], [m4_esyscmd([./build-aux/pkg-version --version])])

AC_SUBST([PACKAGE_VERSION],
         [m4_esyscmd([./build-aux/pkg-version --version])])

AC_SUBST([PACKAGE_RELEASE],
         [m4_esyscmd([./build-aux/pkg-version --release])])

# Testing for version and release
AS_IF([test "x$PACKAGE_VERSION" = x],
      AC_MSG_ERROR([package version not defined]))
AS_IF([test "x$PACKAGE_RELEASE" = x],
      AC_MSG_ERROR([package release not defined]))

AC_CONFIG_AUX_DIR([build-aux])
AM_INIT_AUTOMAKE([-Wno-portability])
AM_PATH_PYTHON([2.6])
AC_PATH_PROG([PEP8], [pep8], [/usr/bin/pep8])
AC_PYTHON_MODULE([unittest])
AC_SUBST([HAVE_PYMOD_UNITTEST])
AC_SUBST([PYTHON_VERSION])
AM_GNU_GETTEXT([external])
AM_GNU_GETTEXT_VERSION([0.10])
AC_PATH_PROG([CHEETAH], [cheetah], [/usr/bin/cheetah])

# Checking for pyflakes
AC_PATH_PROG([PYFLAKES], [pyflakes])
if test "x$PYFLAKES" = "x"; then
  AC_MSG_WARN([pyflakes not found])
fi


AC_CONFIG_FILES([
    po/Makefile.in
    po/gen-pot
    Makefile
    docs/Makefile
    src/Makefile
    src/distros.d/Makefile
    src/kimchi/Makefile
    src/kimchi/control/Makefile
    src/kimchi/control/vm/Makefile
    src/kimchi/model/Makefile
    plugins/Makefile
    plugins/sample/Makefile
    plugins/sample/ui/Makefile
    plugins/sample/ui/config/Makefile
    ui/Makefile
    ui/css/Makefile
    ui/css/fonts/Makefile
    ui/images/Makefile
    ui/images/theme-default/Makefile
    ui/js/Makefile
    ui/js/spice/Makefile
    ui/libs/Makefile
    ui/libs/themes/Makefile
    ui/libs/themes/base/Makefile
    ui/libs/themes/base/images/Makefile
    ui/novnc/Makefile
    ui/novnc/css/Makefile
    ui/novnc/js/Makefile
    ui/novnc/js/web-socket-js/Makefile
    ui/pages/Makefile
    ui/pages/help/Makefile
    ui/pages/help/en_US/Makefile
    ui/pages/help/pt_BR/Makefile
    ui/pages/help/zh_CN/Makefile
    ui/pages/tabs/Makefile
    contrib/Makefile
    contrib/DEBIAN/Makefile
    contrib/DEBIAN/control
    contrib/kimchi.spec.fedora
    contrib/kimchi.spec.suse
    tests/Makefile
    config/Makefile
    config/ui/Makefile
],[
    chmod +x po/gen-pot
])

AC_OUTPUT
