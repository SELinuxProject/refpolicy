# SELinux Reference Policy

## Make Targets

### General Targets

- **`install-src`**: Install policy sources into `/etc/selinux/NAME/src/policy`, where `NAME` is
  defined in the Makefile. If unset, `TYPE` is used. The default `NAME` is `refpolicy`. A
  pre-existing source policy is moved to `/etc/selinux/NAME/src/policy.bak`.
- **`conf`**: Regenerate `policy.xml` and update or create `modules.conf` and `booleans.conf`. Run
  this after adding or removing modules, or after running `bare`. Existing configuration settings
  are preserved. This must be run on policy sources checked out from the CVS repository before
  they can be used.
- **`clean`**: Delete temporary files, compiled policies, and `file_contexts`. Configuration files
  are left intact.
- **`bare`**: Run `clean` and also delete configuration files, web documentation, and `policy.xml`.
- **`html`**: Regenerate `policy.xml` and create web documentation in `doc/html`.

### Modular Policy Targets

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

### Monolithic Policy Targets

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

## Files and Directories

All paths are relative to the root of the Reference Policy source directory.

- **`Makefile`**: General rules for building the policy.
- **`Rules.modular`**: Makefile rules for building loadable module policies.
- **`Rules.monolithic`**: Makefile rules for building monolithic policies.
- **`build.conf`**: Options that influence the policy build, such as policy type and distribution.
- **`config/appconfig-*`**: Application configuration files for all Reference Policy
  configurations, including targeted or strict policy with or without MLS or MCS. SELinux-aware
  programs use these files.
- **`config/local.users`**: File read when loading policy to add SELinux users to the policy.
- **`doc/html/*`**: In-policy XML documentation presented as web pages.
- **`doc/policy.dtd`**: DTD used to validate `doc/policy.xml`.
- **`doc/policy.xml`**: File generated or updated by `conf` and `html`. It contains the complete XML
  documentation included in the policy.
- **`doc/templates/*`**: Templates used for documentation web pages.
- **`policy/booleans.conf`**: File generated or updated by `conf`. It contains policy booleans and
  their default values. If tunables are implemented as booleans, tunables are also included. This
  is installed as `/etc/selinux/NAME/booleans`.
- **`policy/constraints`**: Additional constraints on permissions, expressed as Boolean
  expressions that must be satisfied for permissions to be granted. These constraints further
  refine type-enforcement and role-allow rules and typically restrict user identity or role
  changes to certain domains.
- **`policy/global_booleans`**: Global booleans, their default values, and documentation.
- **`policy/global_tunables`**: Global tunables, their default values, and documentation.
- **`policy/flask/initial_sids`**: Declarations for each initial SID.
- **`policy/flask/security_classes`**: Declarations for each security class.
- **`policy/flask/access_vectors`**: Access-vector definitions. Common prefixes may be defined at
  the beginning of the file, followed by an access vector for each security class.
- **`policy/mcs`**: Multi-category security (MCS) configuration.
- **`policy/mls`**: Multi-level security (MLS) configuration.
- **`policy/modules/*`**: Layer directories containing all Reference Policy modules.
- **`policy/modules.conf`**: Available modules and how they are used when building Reference
  Policy. Set a module to `off` to omit it. For monolithic policies, modules set to `base` or
  `module` are included. For modular policies, modules set to `base` are included in the base
  module and those set to `module` are compiled as individual loadable modules.
- **`policy/support/*`**: Support macros.
- **`policy/users`**: Users included in the policy.
- **`support/*`**: Tools used in the build process.

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
