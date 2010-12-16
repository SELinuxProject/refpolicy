%define distro redhat
%define direct_initrc y
%define monolithic n
%define polname1 targeted
%define type1 targeted-mcs
%define polname2 strict
%define type2 strict-mcs
Summary: SELinux policy configuration
Name: selinux-policy
Version: 20051019
Release: 1
License: GPL
Group: System Environment/Base
Source: refpolicy-%{version}.tar.bz2
Url: http://serefpolicy.sourceforge.net
BuildRoot: %{_tmppath}/refpolicy-buildroot
BuildArch: noarch
# FIXME Need to ensure these have correct versions
BuildRequires: checkpolicy m4 policycoreutils python make gcc
PreReq: kernel >= 2.6.4-1.300 policycoreutils >= %{POLICYCOREUTILSVER}
Obsoletes: policy 

%description
SELinux Reference Policy - modular.

%prep
%setup -q
make conf

%build

%install
%{__rm} -fR $RPM_BUILD_ROOT
make NAME=%{polname1} TYPE=%{type1} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} base.pp
make NAME=%{polname1} TYPE=%{type1} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} modules
%{__mkdir} -p $RPM_BUILD_ROOT/%{_usr}/share/selinux/%{polname1}/%{type1}
%{__cp} *.pp $RPM_BUILD_ROOT/%{_usr}/share/selinux/%{polname1}/%{type1}
%{__mkdir} -p $RPM_BUILD_ROOT/%{_sysconfdir}/selinux/%{polname1}/policy
%{__mkdir} -p $RPM_BUILD_ROOT/%{_sysconfdir}/selinux/%{polname1}/contexts/files
make NAME=%{polname1} TYPE=%{type1} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=y DESTDIR=$RPM_BUILD_ROOT install-appconfig
make NAME=%{polname1} TYPE=%{type1} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} DESTDIR=$RPM_BUILD_ROOT $RPM_BUILD_ROOT%{_sysconfdir}/selinux/%{polname1}/users/local.users
make NAME=%{polname1} TYPE=%{type1} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} DESTDIR=$RPM_BUILD_ROOT $RPM_BUILD_ROOT%{_sysconfdir}/selinux/%{polname1}/users/system.users
make NAME=%{polname2} TYPE=%{type2} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} base.pp
make NAME=%{polname2} TYPE=%{type2} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} modules
%{__mkdir} -p $RPM_BUILD_ROOT/%{_usr}/share/selinux/%{polname2}/%{type2}
%{__cp} *.pp $RPM_BUILD_ROOT/%{_usr}/share/selinux/%{polname2}/%{type2}
%{__mkdir} -p $RPM_BUILD_ROOT/%{_sysconfdir}/selinux/%{polname2}/policy
%{__mkdir} -p $RPM_BUILD_ROOT/%{_sysconfdir}/selinux/%{polname2}/contexts/files
make NAME=%{polname2} TYPE=%{type2} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=y DESTDIR=$RPM_BUILD_ROOT install-appconfig
make NAME=%{polname2} TYPE=%{type2} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} DESTDIR=$RPM_BUILD_ROOT $RPM_BUILD_ROOT%{_sysconfdir}/selinux/%{polname2}/users/local.users
make NAME=%{polname2} TYPE=%{type2} DISTRO=%{distro} DIRECT_INITRC=%{direct_initrc} MONOLITHIC=%{monolithic} DESTDIR=$RPM_BUILD_ROOT $RPM_BUILD_ROOT%{_sysconfdir}/selinux/%{polname2}/users/system.users

%clean
%{__rm} -fR $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_sysconfdir}/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/*.pp
#%ghost %config(noreplace) %{_sysconfdir}/selinux/config
%dir %{_sysconfdir}/selinux/*
%ghost %config %{_sysconfdir}/selinux/*/booleans
%dir %{_sysconfdir}/selinux/*/policy
#%ghost %config %{_sysconfdir}/selinux/*/policy/policy.*
%dir %{_sysconfdir}/selinux/*/contexts
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/customizable_types
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/dbus_contexts
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/default_contexts
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/default_type
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/failsafe_context
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/initrc_context
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/removable_context
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/userhelper_context
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/sepgsql_contexts
%config(noreplace) %{_sysconfdir}/selinux/*/contexts/x_contexts
%dir %{_sysconfdir}/selinux/*/contexts/files
#%ghost %config %{_sysconfdir}/selinux/*/contexts/files/file_contexts
#%ghost %config %{_sysconfdir}/selinux/*/contexts/files/homedir_template
#%ghost %config %{_sysconfdir}/selinux/*/contexts/files/file_contexts.homedirs
%config %{_sysconfdir}/selinux/*/contexts/files/media
%dir %{_sysconfdir}/selinux/*/users
%config %{_sysconfdir}/selinux/*/users/system.users
%config %{_sysconfdir}/selinux/*/users/local.users
#%ghost %dir %{_sysconfdir}/selinux/*/modules

%pre

%post

%package base-targeted
Summary: SELinux %{polname1} base policy
Group: System Environment/Base
Provides: selinux-policy-base

%description base-targeted
SELinux Reference policy targeted base module.

%files base-targeted
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname1}
%dir %{_usr}/share/selinux/%{polname1}/%{type1}
%config %{_usr}/share/selinux/%{polname1}/%{type1}/base.pp
%dir %{_sysconfdir}/selinux
#%ghost %config(noreplace) %{_sysconfdir}/selinux/config
%dir %{_sysconfdir}/selinux/%{polname1}
%ghost %config %{_sysconfdir}/selinux/%{polname1}/booleans
%dir %{_sysconfdir}/selinux/%{polname1}/policy
#%ghost %config %{_sysconfdir}/selinux/%{polname1}/policy/policy.*
%dir %{_sysconfdir}/selinux/%{polname1}/contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/customizable_types
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/dbus_contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/default_contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/default_type
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/failsafe_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/initrc_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/removable_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/userhelper_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/sepgsql_contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname1}/contexts/x_contexts
%dir %{_sysconfdir}/selinux/%{polname1}/contexts/files
#%ghost %config %{_sysconfdir}/selinux/%{polname1}/contexts/files/file_contexts
#%ghost %config %{_sysconfdir}/selinux/%{polname1}/contexts/files/homedir_template
#%ghost %config %{_sysconfdir}/selinux/%{polname1}/contexts/files/file_contexts.homedirs
%config %{_sysconfdir}/selinux/%{polname1}/contexts/files/media
%dir %{_sysconfdir}/selinux/%{polname1}/users
%config %{_sysconfdir}/selinux/%{polname1}/users/system.users
%config %{_sysconfdir}/selinux/%{polname1}/users/local.users
#%ghost %dir %{_sysconfdir}/selinux/%{polname1}/modules

%post base-targeted
semodule -b /usr/share/selinux/%{polname1}/%{type1}/base.pp -s %{_sysconfdir}/selinux/%{polname1}
for file in $(ls /usr/share/selinux/%{polname1}/%{type1} | grep -v base.pp)
do semodule -i /usr/share/selinux/%{polname1}/%{type1}/$file -s %{_sysconfdir}/selinux/%{polname1}
done

%package base-strict
Summary: SELinux %{polname2} base policy
Group: System Environment/Base
Provides: selinux-policy-base

%description base-strict
SELinux Reference policy strict base module.

%files base-strict
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/%{polname2}
%dir %{_usr}/share/selinux/%{polname2}/%{type2}
%config %{_usr}/share/selinux/%{polname2}/%{type2}/base.pp
%dir %{_sysconfdir}/selinux
#%ghost %config(noreplace) %{_sysconfdir}/selinux/config
%dir %{_sysconfdir}/selinux/%{polname2}
%ghost %config %{_sysconfdir}/selinux/%{polname2}/booleans
%dir %{_sysconfdir}/selinux/%{polname2}/policy
#%ghost %config %{_sysconfdir}/selinux/%{polname2}/policy/policy.*
%dir %{_sysconfdir}/selinux/%{polname2}/contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/customizable_types
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/dbus_contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/default_contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/default_type
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/failsafe_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/initrc_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/removable_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/userhelper_context
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/sepgsql_contexts
%config(noreplace) %{_sysconfdir}/selinux/%{polname2}/contexts/x_contexts
%dir %{_sysconfdir}/selinux/%{polname2}/contexts/files
#%ghost %config %{_sysconfdir}/selinux/%{polname2}/contexts/files/file_contexts
#%ghost %config %{_sysconfdir}/selinux/%{polname2}/contexts/files/homedir_template
#%ghost %config %{_sysconfdir}/selinux/%{polname2}/contexts/files/file_contexts.homedirs
%config %{_sysconfdir}/selinux/%{polname2}/contexts/files/media
%dir %{_sysconfdir}/selinux/%{polname2}/users
%config %{_sysconfdir}/selinux/%{polname2}/users/system.users
%config %{_sysconfdir}/selinux/%{polname2}/users/local.users
#%ghost %dir %{_sysconfdir}/selinux/%{polname2}/modules

%post base-strict
semodule -b /usr/share/selinux/%{polname2}/%{type2}/base.pp -s %{_sysconfdir}/selinux/%{polname2}
for file in $(ls /usr/share/selinux/%{polname2}/%{type2} | grep -v base.pp)
do semodule -i /usr/share/selinux/%{polname2}/%{type2}/$file -s %{_sysconfdir}/selinux/%{polname2}
done

%package apache
Summary: SELinux apache policy
Group: System Environment/Base
Requires: selinux-policy-base

%description apache
SELinux Reference policy apache module.

%files apache
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/apache.pp

%post apache
if [ -d %{_sysconfdir}/selinux/%{polname1}/modules ] ; then
semodule -n -i %{_usr}/share/selinux/%{polname1}/%{type1}/apache.pp -s %{_sysconfdir}/selinux/%{polname1}
fi
if [ -d %{_sysconfdir}/selinux/%{polname2}/modules ] ; then
semodule -i %{_usr}/share/selinux/%{polname2}/%{type2}/apache.pp -s %{_sysconfdir}/selinux/%{polname2}
fi

%preun apache
if [ -d %{_sysconfdir}/selinux/%{polname1}/modules ]
then semodule -n -r apache -s %{_sysconfdir}/selinux/%{polname1}
fi
if [ -d %{_sysconfdir}/selinux/%{polname2}/modules ]
then semodule -n -r apache -s %{_sysconfdir}/selinux/%{polname2}
fi

%package bind
Summary: SELinux bind policy
Group: System Environment/Base

%description bind
SELinux Reference policy bind module.

%files bind
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/bind.pp

%post bind
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/bind.pp

%preun bind
semodule -r bind

%package dhcp
Summary: SELinux dhcp policy
Group: System Environment/Base

%description dhcp
SELinux Reference policy dhcp module.

%files dhcp
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/dhcp.pp

%post dhcp
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/dhcp.pp

%preun dhcp
semodule -r dhcp

%package ldap
Summary: SELinux ldap policy
Group: System Environment/Base

%description ldap
SELinux Reference policy ldap module.

%files ldap
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/ldap.pp

%post ldap
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/ldap.pp

%preun ldap
semodule -r ldap

%package mailman
Summary: SELinux mailman policy
Group: System Environment/Base

%description mailman
SELinux Reference policy mailman module.

%files mailman
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/mailman.pp

%post mailman
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/mailman.pp

%preun mailman
semodule -r mailman

%package mysql
Summary: SELinux mysql policy
Group: System Environment/Base

%description mysql
SELinux Reference policy mysql module.

%files mysql
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/mysql.pp

%post mysql
semodule -i %{_usr}/share/selinux/targeted/targeted-mcsmysql.pp

%preun mysql
semodule -r mysql

%package portmap
Summary: SELinux portmap policy
Group: System Environment/Base

%description portmap
SELinux Reference policy portmap module.

%files portmap
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/portmap.pp

%post portmap
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/portmap.pp

%preun portmap
semodule -r portmap

%package postgresql
Summary: SELinux postgresql policy
Group: System Environment/Base

%description postgresql
SELinux Reference policy postgresql module.

%files postgresql
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/postgresql.pp

%post postgresql
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/postgresql.pp

%preun postgresql
semodule -r postgresql

%package samba
Summary: SELinux samba policy
Group: System Environment/Base

%description samba
SELinux Reference policy samba module.

%files samba
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/samba.pp

%post samba
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/samba.pp

%preun samba
semodule -r samba

%package snmp
Summary: SELinux snmp policy
Group: System Environment/Base

%description snmp
SELinux Reference policy snmp module.

%files snmp
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/snmp.pp

%post snmp
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/snmp.pp

%preun snmp
semodule -r snmp

%package squid
Summary: SELinux squid policy
Group: System Environment/Base

%description squid
SELinux Reference policy squid module.

%files squid
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/squid.pp

%post squid
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/squid.pp

%preun squid
semodule -r squid

%package webalizer
Summary: SELinux webalizer policy
Group: System Environment/Base

%description webalizer
SELinux Reference policy webalizer module.

%files webalizer
%defattr(-,root,root)
%dir %{_usr}/share/selinux
%dir %{_usr}/share/selinux/*
%dir %{_usr}/share/selinux/*/*
%config %{_usr}/share/selinux/*/*/webalizer.pp

%post webalizer
semodule -i %{_usr}/share/selinux/targeted/targeted-mcs/webalizer.pp

%preun webalizer
semodule -r webalizer

%changelog
