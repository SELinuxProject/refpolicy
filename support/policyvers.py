#!/usr/bin/python
from __future__ import print_function
import selinux
if selinux.is_selinux_enabled():
	print(selinux.security_policyvers())
