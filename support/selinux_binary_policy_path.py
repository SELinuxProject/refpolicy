#!/usr/bin/env python3

try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
        import selinux

    if selinux.is_selinux_enabled():
        print(selinux.selinux_binary_policy_path())
except ImportError:
    exit(0)
