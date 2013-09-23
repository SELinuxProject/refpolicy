#!/usr/bin/python
import selinux
if selinux.is_selinux_enabled():
	print selinux.security_policyvers()
