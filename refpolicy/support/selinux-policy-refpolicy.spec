%define polname refpolicy
%define type targeted-mcs
%define distro redhat
%define direct_initrc y
%define monolithic n
Summary: SELinux %{polname} policy configuration
Name: selinux-policy-%{polname}
Version: 20051019
Release: 1
License: GPL
Group: System Environment/Base
Source: refpolicy-%{version}.tar.bz2
Url: http://serefpolicy.sourceforge.net
BuildRoot: %{_tmppath}/%{polname}-buildroot
BuildArch: noarch
# FIXME Need to ensure these have correct versions
BuildRequires: checkpolicy m4 policycoreutils python make gcc
PreReq: kernel >= 2.6.4-1.300 policycoreutils >= %{POLICYCOREUTILSVER}
Obsoletes: policy 

%description
SELinux Reference Policy - modular.

%prep
%setup -q

%build
make conf
make NAME=%{polname} TYPE=%{type} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} base.pp
make NAME=%{polname} TYPE=%{type} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} modules

%install
rm -fR $RPM_BUILD_ROOT
%{__mkdir} -p $RPM_BUILD_ROOT/%{_usr}/share/selinux/%{polname}/%{type}
%{__cp} *.pp $RPM_BUILD_ROOT/%{_usr}/share/selinux/%{polname}/%{type}

%clean
rm -fR $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/*.pp

%pre

%post

%package base
Summary: SELinux %{polname} base policy
Group: System Environment/Base

%description base
SELinux Reference policy base module.

%files base
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/base.pp

%post base
semodule -b %{_usr}/share/selinux/%{polname}/%{type}/base.pp

%postun base
semodule -r base

%package apache
Summary: SELinux %{polname} apache policy
Group: System Environment/Base

%description apache
SELinux Reference policy apache module.

%files apache
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/apache.pp

%post apache
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/apache.pp

%postun apache
semodule -r apache

%package bind
Summary: SELinux %{polname} bind policy
Group: System Environment/Base

%description bind
SELinux Reference policy bind module.

%files bind
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/bind.pp

%post bind
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/bind.pp

%postun bind
semodule -r bind

%package dhcp
Summary: SELinux %{polname} dhcp policy
Group: System Environment/Base

%description dhcp
SELinux Reference policy dhcp module.

%files dhcp
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/dhcp.pp

%post dhcp
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/dhcp.pp

%postun dhcp
semodule -r dhcp

%package ldap
Summary: SELinux %{polname} ldap policy
Group: System Environment/Base

%description ldap
SELinux Reference policy ldap module.

%files ldap
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/ldap.pp

%post ldap
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/ldap.pp

%postun ldap
semodule -r ldap

%package mailman
Summary: SELinux %{polname} mailman policy
Group: System Environment/Base

%description mailman
SELinux Reference policy mailman module.

%files mailman
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/mailman.pp

%post mailman
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/mailman.pp

%postun mailman
semodule -r mailman

%package mysql
Summary: SELinux %{polname} mysql policy
Group: System Environment/Base

%description mysql
SELinux Reference policy mysql module.

%files mysql
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/mysql.pp

%post mysql
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/mysql.pp

%postun mysql
semodule -r mysql

%package portmap
Summary: SELinux %{polname} portmap policy
Group: System Environment/Base

%description portmap
SELinux Reference policy portmap module.

%files portmap
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/portmap.pp

%post portmap
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/portmap.pp

%postun portmap
semodule -r portmap

%package postgresql
Summary: SELinux %{polname} postgresql policy
Group: System Environment/Base

%description postgresql
SELinux Reference policy postgresql module.

%files postgresql
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/postgresql.pp

%post postgresql
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/postgresql.pp

%postun postgresql
semodule -r postgresql

%package samba
Summary: SELinux %{polname} samba policy
Group: System Environment/Base

%description samba
SELinux Reference policy samba module.

%files samba
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/samba.pp

%post samba
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/samba.pp

%postun samba
semodule -r samba

%package snmp
Summary: SELinux %{polname} snmp policy
Group: System Environment/Base

%description snmp
SELinux Reference policy snmp module.

%files snmp
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/snmp.pp

%post snmp
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/snmp.pp

%postun snmp
semodule -r snmp

%package squid
Summary: SELinux %{polname} squid policy
Group: System Environment/Base

%description squid
SELinux Reference policy squid module.

%files squid
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/squid.pp

%post squid
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/squid.pp

%postun squid
semodule -r squid

%package webalizer
Summary: SELinux %{polname} webalizer policy
Group: System Environment/Base

%description webalizer
SELinux Reference policy webalizer module.

%files webalizer
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname}
%dir %{_usr}/share/selinux/%{polname}/%{type}
%config %{_usr}/share/selinux/%{polname}/%{type}/webalizer.pp

%post webalizer
semodule -i %{_usr}/share/selinux/%{polname}/%{type}/webalizer.pp

%postun webalizer
semodule -r webalizer

%changelog
