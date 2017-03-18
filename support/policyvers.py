#!/usr/bin/env python3

try:
    import selinux

    if selinux.is_selinux_enabled():
        print(selinux.security_policyvers())
except ImportError:
    exit(0)
