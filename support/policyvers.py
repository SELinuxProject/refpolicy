#!/usr/bin/env python3

try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
        import selinux

    if selinux.is_selinux_enabled():
        print(selinux.security_policyvers())
except ImportError:
    exit(0)
