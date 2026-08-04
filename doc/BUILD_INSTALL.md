# Build and Install Targets

Building Reference Policy requires:

- SELinux userspace 3.9 or later
- Python 3.10 or later
- make
- m4
- sed
- awk
- grep

Running an installed policy requires a Linux kernel with SELinux support and
the SELinux userspace tools used to install, load, manage, and label the policy.

## General Make Targets

- **`conf`**: Generate `policy.xml` and update or create `modules.conf` and `booleans.conf`. Run
  this after adding or removing modules, or after running `bare`. Existing configuration settings
  are preserved. This must be run on policy sources checked out from the CVS repository before
  they can be used.
- **`install-src`**: Install policy sources into `/etc/selinux/NAME/src/policy`, where `NAME` is
  defined in the Makefile. If unset, `TYPE` is used. The default `NAME` is `refpolicy`. A
  pre-existing source policy is moved to `/etc/selinux/NAME/src/policy.bak`.
- **`clean`**: Delete temporary files, compiled policies, and `file_contexts`. Configuration files
  are left intact.
- **`bare`**: Run `clean` and also delete all remaining generated files, including `modules.conf`,
  and `booleans.conf`.
- **`html`**: Generate `policy.xml` and create web documentation in `doc/html`.

## Modular Policy Make Targets

- **`base`**: Compile and package the base module. This is the default modular policy target.
- **`modules`**: Compile and package all Reference Policy modules configured as loadable modules.
- **`MODULENAME.pp`**: Compile and package the `MODULENAME` Reference Policy module.
- **`all`**: Compile and package the base module and all modules configured as loadable modules.
- **`install`**: Compile, package, and install the base module and modules configured as loadable
  modules.
- **`load`**: Compile, package, and install the base module and loadable modules, then insert them
  into the module store.
- **`validate`**: Validate that the configured modules can successfully link and expand.
- **`install-headers`**: Install policy headers into `/usr/share/selinux/NAME`. The headers are
  sufficient for building a policy module locally without the complete Reference Policy sources.
  Set the `build.conf` options for this policy configuration before using this target.
- **`build-interface-db`**: Build the policy interface database with `sepolgen-ifgen`. This is
  required for reference-style policy generation by `audit2allow --reference`.

## Monolithic Policy Make Targets

- **`policy`**: Compile a policy locally for development and testing. This is the default
  monolithic policy target.
- **`install`**: Compile and install the policy and file contexts.
- **`load`**: Compile and install the policy and file contexts, then load the policy.
- **`enableaudit`**: Remove all `dontaudit` rules from `policy.conf`.
- **`relabel`**: Relabel the filesystem.
- **`checklabels`**: Check filesystem labels and report when a file would be relabeled without
  changing its label.
- **`restorelabels`**: Relabel the filesystem and report each file that is relabeled.

## Build Options

The following options are set in `build.conf`.

- **`TYPE`** (`String`): Available options are `standard`, `mls`, and `mcs`. For a
  type-enforcement-only system, use `standard`. This optionally enables multi-level security
  (MLS) or multi-category security (MCS) features and controls `enable_mls` and `enable_mcs`
  policy blocks.
- **`NAME`** (`String`, optional): Set the policy name used when installing files under paths such
  as `/etc/selinux/NAME` and `/usr/share/selinux/NAME`. If unset, the policy `TYPE` is used.
- **`DISTRO`** (`String`, optional): Enable distribution-specific policy. Available options are
  `redhat`, `gentoo`, and `debian`. This controls the `distro_redhat`, `distro_gentoo`, and
  `distro_debian` build-option policy blocks.
- **`MONOLITHIC`** (`Boolean`): Build a monolithic policy when set; otherwise, build a modular
  policy.
- **`DIRECT_INITRC`** (`Boolean`): Allow `sysadm` to run init scripts directly instead of using
  `run_init`. This is a build option rather than a tunable because role transitions do not work in
  conditional policy. It controls `direct_sysadm_daemon` policy blocks.
- **`OUTPUT_POLICY`** (`Integer`): Set the policy version created by a monolithic build. This has
  no effect on modular policy.
- **`OUTPUT_MODULE`** (`Integer`): Set the module policy version created by a modular build. This
  has no effect on monolithic policy.
- **`UNK_PERMS`** (`String`): Set kernel behavior for permissions defined in the kernel but missing
  from the policy. Permissions can be allowed (`allow`), denied (`deny`), or cause policy loading
  to be rejected (`reject`).
- **`UBAC`** (`Boolean`): Also use the SELinux user for approximate role separation.
- **`SYSTEMD`** (`Boolean`): Assume systemd is the init process provider.
- **`MLS_SENS`** (`Integer`): Set the number of MLS sensitivities. Ignored for standard and MCS
  policies.
- **`MLS_CATS`** (`Integer`): Set the number of MLS categories. Ignored for standard and MCS
  policies.
- **`MCS_CATS`** (`Integer`): Set the number of MCS categories. Ignored for standard and MLS
  policies.
- **`QUIET`** (`Boolean`): Display only status and error messages. This has no effect on policy.
- **`WERROR`** (`Boolean`): Treat warnings as errors. The build fails if warnings are encountered.

## Building Modules Using Reference Policy Headers

The system must first have the Reference Policy headers installed, typically by the distribution.
Otherwise, install the headers from the complete Reference Policy sources with the
`install-headers` target.

To build a local module, place a `.te` file in a directory. Use `doc/Makefile.example` as the
Makefile. It may be installed under `/usr/share/doc` in the directory for the distribution's
policy. Alternatively, call the primary Makefile in the headers directory, typically
`/usr/share/selinux/NAME/Makefile`, directly with `make -f`.

Larger projects can use layers like Reference Policy by creating `policy/modules/LAYERNAME`
directories. Each layer must have a `metadata.xml` file containing a `summary` tag and an optional
`desc` tag for a longer description. The metadata should describe the layer's purpose.

Example `metadata.xml`:

```xml
<summary>ABC modules for the XYZ components.</summary>
```

### Header-Based Module Targets

- **`MODULENAME.pp`**: Compile and package the `MODULENAME` local module.
- **`all`**: Compile and package the modules in the current directory.
- **`load`**: Compile and package the modules in the current directory, then insert them into the
  module store.
- **`refresh`**: Attempt to reinsert all modules currently in the module store from local and
  system module packages.
- **`xml`**: Build a `policy.xml` from the XML included with the base policy headers and any XML in
  the modules in the current directory.
