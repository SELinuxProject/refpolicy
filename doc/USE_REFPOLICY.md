# Switching to Reference Policy

Reference Policy is used as the basis of Red Hat Enterprise Linux,
Fedora, Gentoo, Debian, and Ubuntu distribution policies. If you are
using one of these distributions, it would likely be best to continue
using the distribution's policy as those policies have
distribution-specific configurations. This guide will walk you through
switching to the Reference Policy on a generic Red Hat/Fedora system.

## Download and unpack the policy

The policy is available from the
[releases](https://github.com/SELinuxProject/refpolicy/releases) page.
Download the policy, and unpack it to a temporary directory. Then use
the install-src make target to install the policy sources.

```bash
$ tar -jxvf refpolicy-20071214.tar.bz2 -C /tmp

$ cd /tmp/refpolicy
$ sudo make install-src
```

## Configure the policy

The policy source is found in the /etc/selinux/refpolicy/src/policy/
directory.

```bash
$ cd /etc/selinux/refpolicy/src/policy
```

Edit the policy build.conf file
(/etc/selinux/refpolicy/src/policy/build.conf). Near the top of the
file, the policy has a few build options. The DISTRO option needs to be
uncommented and set to redhat, and DIRECT\_INITRC should be set to y.

```make
########################################
#
# Policy build options
#

# Policy version
# By default, checkpolicy will create the highest
# version policy it supports.  Setting this will
# override the version.  This only has an
# effect for monolithic policies.
#OUTPUT_POLICY = 18

# Policy Type
# standard, mls, mcs
TYPE = standard

# Policy Name
# If set, this will be used as the policy
# name.  Otherwise the policy type will be
# used for the name.
NAME = refpolicy

# Distribution
# Some distributions have portions of policy
# for programs or configurations specific to the
# distribution.  Setting this will enable options
# for the distribution.
# redhat, gentoo, debian, suse, and rhel4 are current options.
# Fedora users should enable redhat.
DISTRO = redhat

# Unknown Permissions Handling
# The behavior for handling permissions defined in the
# kernel but missing from the policy.  The permissions
# can either be allowed, denied, or the policy loading
# can be rejected.
# allow, deny, and reject are current options.
#UNK_PERMS = deny

# Direct admin init
# Setting this will allow sysadm to directly
# run init scripts, instead of requiring run_init.
# This is a build option, as role transitions do
# not work in conditional policy.
DIRECT_INITRC=y

# Build monolithic policy.  Putting n here
# will build a loadable module policy.
MONOLITHIC=y

# Number of MLS Sensitivities
# The sensitivities will be s0 to s(MLS_SENS-1).
# Dominance will be in increasing numerical order
# with s0 being lowest.
MLS_SENS=16

# Number of MLS Categories
# The categories will be c0 to c(MLS_CATS-1).
MLS_CATS=256

# Number of MCS Categories
# The categories will be c0 to c(MLS_CATS-1).
MCS_CATS=256

# Set this to y to only display status messages
# during build.
QUIET=n
```

## Install the policy

Next, install the policy, application configuration files, and file
contexts.

```bash
$ sudo make install
```

## Change SELinux Configuration

Modify the /etc/selinux/config file, and set SELINUXTYPE to refpolicy.
It should look similar to this:

```make
# This file controls the state of SELinux on the system.
# SELINUX= can take one of these three values:
#       enforcing - SELinux security policy is enforced.
#       permissive - SELinux prints warnings instead of enforcing.
#       disabled - No SELinux policy is loaded.
SELINUX=enforcing
# SELINUXTYPE= can take one of these two values:
#       targeted - Only targeted network daemons are protected.
#       strict - Full SELinux protection.
SELINUXTYPE=refpolicy
```

## Restart and Relabel

The system needs to be restarted with the new policy, and relabeled on
booting, to finalize the switch.

```bash
$ sudo touch /.autorelabel
$ sudo shutdown -r now
```
