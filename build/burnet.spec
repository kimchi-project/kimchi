%define release  %{?custom_release}%{!?custom_release: 0}
%define version  %{?custom_version}%{!?custom_version: 0.1}

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%global with_systemd 1
%endif

Name:		%{project_name}
Version:	%{version}
Release:	%{release}%{?dist}
Summary:	Burnet server application
BuildRoot:	%{_topdir}/BUILD/%{name}-%{version}-%{release}
Group:		System Environment/Base
License:	IBM
Source0:	%{name}.tar.gz
Requires:	libvirt
Requires:	libvirt-python

%if %([[ %{_vendor} == "redhat" ]] && echo 1 || echo 0)
Requires:	python-cherrypy
Requires:	python-cheetah
%endif

%if 0%{?rhel} == 6
Requires:	python-ordereddict
Requires:	python-imaging
%endif

%if 0%{?with_systemd}
Requires:	systemd
%endif

%description
Web server application application to manage KVM/Qemu virtual machines

%prep
%setup -c

%build

%install
mkdir -p $RPM_BUILD_ROOT/
cp -vr * $RPM_BUILD_ROOT
%if 0%{?with_systemd}
rm -rf $RPM_BUILD_ROOT/etc/init/
%else
rm -rf $RPM_BUILD_ROOT/lib/systemd/
%endif

find $RPM_BUILD_ROOT -type f -printf "/%%P\n" | grep -v "\.py" > %{_builddir}/files.list
find $RPM_BUILD_ROOT -name "*.py" -printf "/%%P*\n" >> %{_builddir}/files.list

%post
%if 0%{?with_systemd}
systemctl --system daemon-reload
systemctl enable %{project_name}d.service
systemctl start %{project_name}d.service
%endif

%if 0%{?rhel} == 6
start %{project_name}d
%else
service %{project_name}d start
%endif

%preun
%if 0%{?with_systemd}
systemctl stop %{project_name}d.service
%endif

%if 0%{?rhel} == 6
stop %{project_name}d
%else
service %{project_name}d stop
%endif

%postun
rm -rf %{_datadir}/burnet/ /etc/burnet/ /var/log/burnet/ /var/run/burnet.pid

%clean
rm -rf $RPM_BUILD_ROOT

%files -f %{_builddir}/files.list
%attr(-,root,root)
/usr/share/burnet/data

%changelog
* Thu Apr 04 2013 Aline Manera <alinefm@br.ibm.com> 0.0-1
- First build
