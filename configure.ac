#
# Kimchi
#
# Copyright IBM Corp, 2013-2015
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

AC_INIT([wok], [m4_esyscmd([./build-aux/pkg-version --version])])

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

AC_ARG_ENABLE(
    [sample],
    [AS_HELP_STRING(
        [--enable-sample],
        [enable sample plugin @<:@default=no@:>@]
    )],
    ,
    [enable_sample="no"]
)

if test "${enable_sample}" = "yes"; then
AC_SUBST([ENABLE_SAMPLE], [True])
else
AC_SUBST([ENABLE_SAMPLE], [False])
fi

# check for systemd
PKG_PROG_PKG_CONFIG
AC_ARG_WITH([systemdsystemunitdir],
    AS_HELP_STRING([--with-systemdsystemunitdir=DIR], [Directory for systemd service files]),
    [], [with_systemdsystemunitdir=$($PKG_CONFIG --variable=systemdsystemunitdir systemd)])
if test "x$with_systemdsystemunitdir" != xno; then
    AC_SUBST([systemdsystemunitdir], [$with_systemdsystemunitdir])
fi

AC_ARG_WITH(
    [spice-html5],
    [AS_HELP_STRING([--with-spice-html5],
                    [Build Kimchi with spice-html5 @<:@default=no@:>@])],
    ,
    [with_spice_html5="no"]
)
AM_CONDITIONAL([WITH_SPICE], [test "x$with_spice_html5" = xyes])

AC_CONFIG_FILES([
    po/Makefile.in
    po/gen-pot
    Makefile
    docs/Makefile
    docs/wokd.8
    src/Makefile
    src/nginx/Makefile
    src/wok/Makefile
    src/wok/control/Makefile
    src/wok/model/Makefile
    src/wok/xmlutils/Makefile
    src/wok/plugins/Makefile
    src/wok/plugins/sample/Makefile
    src/wok/plugins/sample/po/Makefile.in
    src/wok/plugins/sample/sample.conf
    src/wok/plugins/sample/ui/Makefile
    src/wok/plugins/sample/ui/config/Makefile
    src/wok/plugins/sample/ui/js/Makefile
    src/wok/plugins/sample/ui/pages/Makefile
    ui/Makefile
    ui/base64/Makefile
    ui/css/Makefile
    ui/css/fontawesome/Makefile
    ui/css/opensans/Makefile
    ui/images/Makefile
    ui/images/theme-default/Makefile
    ui/js/Makefile
    ui/libs/Makefile
    ui/libs/bootstrap/Makefile
    ui/libs/bootstrap-select/Makefile
    ui/libs/es5-shim/Makefile
    ui/libs/jquery/Makefile
    ui/libs/jquery-i18n/Makefile
    ui/libs/jquery-ui/Makefile
    ui/libs/jquery-ui/themes/Makefile
    ui/libs/jquery-ui/themes/base/Makefile
    ui/libs/jquery-ui/themes/base/images/Makefile
    ui/pages/Makefile
    ui/pages/websockify/Makefile
    contrib/Makefile
    contrib/DEBIAN/Makefile
    contrib/DEBIAN/control
    contrib/wok.spec.fedora
    contrib/wok.spec.suse
    tests/Makefile
],[
    chmod +x po/gen-pot
])

AC_OUTPUT
