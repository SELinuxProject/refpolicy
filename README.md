SELinux Reference Policy
===============================================================================
https://github.com/SELinuxProject/refpolicy

## Reference Policy Make Commands

### General Make Commands

* `make install-src`

Install the policy sources into *"/etc/selinux/NAME/src/policy"*, where NAME is
defined in the Makefile.  If not defined, the TYPE, as defined in the Makefile,
is used.  The default NAME is refpolicy.  A pre-existing source policy will be
moved to *"/etc/selinux/NAME/src/policy.bak"*.

* `make conf`

Regenerate policy.xml, and update/create modules.conf and booleans.conf.  This
should be done after adding or removing modules, or after running the bare
target.  If the configuration files exist, their settings will be preserved.
This must be ran on policy sources that are checked out from the source
repository before they can be used.

* `make clean`

Delete all temporary files, compiled policies, and file_contexts.
Configuration files are left intact.

* `make bare`

Do the clean make target and also delete configuration files, web page
documentation, and policy.xml.

* `make html`

Regenerate policy.xml and create web page documentation in the doc/html
directory.

### Modular (Loadable Modules) Policy Make Commands

* `make base`

Compile and package the base module.  This is the default target for modular
policies.

* `make modules`

Compile and package all Reference Policy modules configured to be built as
loadable modules.

* `make MODULENAME.pp`

Compile and package the MODULENAME Reference Policy module.

* `make all`

Compile and package the base module and all Reference Policy modules configured
to be built as loadable modules.

* `make install`

Compile, package, and install the base module and Reference Policy modules
configured to be built as loadable modules.

* `make load`

Compile, package, and install the base module and Reference Policy modules
configured to be built as loadable modules, then insert them into the module
store.

* `make validate`

Validate if the configured modules can successfully link and expand.

* `make install-headers`

Install the policy headers into *"/usr/share/selinux/NAME"*. The headers are
sufficient for building a policy module locally, without requiring the complete
Reference Policy sources.  The build.conf settings for this policy
configuration should be set before using this target.

* `make build-interface-db`

Build the policy interface database with 'sepolgen-ifgen'.  This database is
required for reference style policy generation by 'audit2allow --reference'.

### Monolithic Policy Make Commands

* `make policy`

Compile a policy locally for development and testing. This is the default
target for monolithic policies.

* `make install`

Compile and install the policy and file contexts.

* `make load`

Compile and install the policy and file contexts, then load the policy.

* `make enableaudit`

Remove all dontaudit rules from policy.conf.

* `make relabel`

Relabel the filesystem.

* `make checklabels`

Check the labels on the filesystem, and report when a file would be relabeled,
but do not change its label.

* `make restorelabels`

Relabel the filesystem and report each file that is relabeled.

## Reference Policy Build Options (build.conf)

* **TYPE** (string)

Available options are standard, mls, and mcs. For a type enforcement only
system, set standard.  This optionally enables multi-level security (MLS) or
multi-category security (MCS) features.  This option controls enable_mls, and
enable_mcs policy blocks.

* **NAME** (string, optional)

Sets the name of the policy; the NAME is used when installing files to
e.g., *"/etc/selinux/NAME"* and *"/usr/share/selinux/NAME"*.  If not set, the
policy type (TYPE) is used.

* **DISTRO** (string, optional)

Enable distribution-specific policy.  Available options are redhat, gentoo,
and debian. This option controls distro_redhat, distro_gentoo,
and distro_debian build option policy blocks.

* **MONOLITHIC** (boolean)

If set, a monolithic policy is built, otherwise a modular policy is built.

* **DIRECT_INITRC** (boolean)

If set, sysadm will be allowed to directly run init scripts, instead of
requiring the run_init tool.  This is a build option instead of a tunable since
role transitions do not work in conditional policy.  This option controls
direct_sysadm_daemon policy blocks.

* **OUTPUT_POLICY** (integer)

Set the version of the policy created when building a monolithic policy.  This
option has no effect on modular policy.

* **UNK_PERMS** (string)

Set the kernel behavior for handling of permissions defined in the kernel but
missing from the policy.  The permissions can either be allowed (allow),
denied (deny), or the policy loading can be rejected (reject).

* **UBAC** (boolean)

If set, the SELinux user will be used additionally for approximate role
separation.

* **SYSTEMD** (boolean)

If set, systemd will be assumed to be the init process provider.

* **MLS_SENS** (integer)

Set the number of sensitivities in the MLS policy.  Ignored on standard and MCS
policies.

* **MLS_CATS** (integer)

Set the number of categories in the MLS policy.  Ignored on standard and MCS
policies.

* **MCS_CATS** (integer)

Set the number of categories in the MCS policy.  Ignored on standard and MLS
policies.

* **QUIET** (boolean)

If set, the build system will only display status messages and error messages.
This option has no effect on policy.

* **WERROR** (boolean)

If set, the build system will treat warnings as errors.  If any warnings are
encountered, the build will fail.

## Reference Policy Files and Directories

All directories relative to the root of the Reference Policy sources directory.

* *Makefile*

General rules for building the policy.

* *Rules.modular*

Makefile rules specific to building loadable module policies.

* *Rules.monolithic*

Makefile rules specific to building monolithic policies.

* *build.conf*

Options which influence the building of the policy, such as the policy type and
distribution.

* *config/appconfig-\**

Application configuration files for all configurations of the Reference Policy
(targeted/strict with or without MLS or MCS).  These are used by SELinux-aware
programs.

* *config/local.users*

The file read by load policy for adding SELinux users to the policy on the fly.

* *doc/html/\**

This contains the contents of the in-policy XML documentation, presented in web
page form.

* *doc/policy.dtd*

The doc/policy.xml file is validated against this DTD.

* *doc/policy.xml*

This file is generated/updated by the conf and html make targets.  It contains
the complete XML documentation included in the policy.

* *doc/templates/\**

Templates used for documentation web pages.

* *policy/booleans.conf*

This file is generated/updated by the conf make target. It contains the
booleans in the policy, and their default values.  If tunables are implemented
as booleans, tunables will also be included.  This file will be installed as
the *"/etc/selinux/NAME/booleans"* file.

* *policy/constraints*

This file defines additional constraints on permissions in the form of boolean
expressions that must be satisfied in order for specified permissions to be
granted.  These constraints are used to further refine the type enforcement
rules and the role allow rules.  Typically, these constraints are used to
restrict changes in user identity or role to certain domains.

* *policy/global_booleans*

This file defines all booleans that have a global scope, their default value,
and documentation.

* *policy/global_tunables*

This file defines all tunables that have a global scope, their default value,
and documentation.

* *policy/flask/initial_sids*

This file has declarations for each initial SID.

* *policy/flask/security_classes*

This file has declarations for each security class.

* *policy/flask/access_vectors*

This file defines the access vectors.  Common prefixes for access vectors may
be defined at the beginning of the file.  After the common prefixes are
defined, an access vector may be defined for each security class.

* *policy/mcs*

The multi-category security (MCS) configuration.

* *policy/mls*

The multi-level security (MLS) configuration.

* *policy/modules/\**

Each directory represents a layer in Reference Policy all of the modules are
contained in one of these layers.

* *policy/modules.conf*

This file contains a listing of available modules, and how they will be used
when building Reference Policy. To prevent a module from  being used, set the
module to "off".  For monolithic policies, modules set to "base" and "module"
will be included in the policy.  For modular policies, modules set to "base"
will be included in the base module; those set to "module" will be compiled as
individual loadable modules.

* *policy/support/\**

Support macros.

* *policy/users*

This file defines the users included in the policy.

* *support/\**

Tools used in the build process.

## Building Policy Modules using Reference Policy Headers

The system must first have the Reference Policy headers installed, typically
by the distribution.  Otherwise, the headers can be installed using the
install-headers target from the full Reference Policy sources.

To set up a directory to build a local module, one must simply place a .te
file in a directory.  A sample Makefile to use in the directory is the
Makefile.example in the doc directory.  This may be installed in
*"/usr/share/doc"*, under the directory for the distribution's policy.
Alternatively, the primary Makefile in the headers directory (typically
*"/usr/share/selinux/NAME/Makefile"*) can be called directly, using make's -f
option.

Larger projects can set up a structure of layers, just as in Reference
Policy, by creating policy/modules/LAYERNAME directories.  Each layer also
must have a metadata.xml file which is an XML file with a summary tag and
optional desc (long description) tag.  This should describe the purpose of
the layer.

Metadata.xml example:
```xml
<summary>ABC modules for the XYZ components.</summary>
```

### Make Command for Modules Built from Headers

* `make MODULENAME.pp`

Compile and package the MODULENAME local module.

* `make all`

Compile and package the modules in the current directory.

* `make load`

Compile and package the modules in the current directory, then insert them into
the module store.

* `make refresh`

Attempts to reinsert all modules that are currently in the module store from
the local and system module packages.

* `make xml`

Build a policy.xml from the XML included with the base policy headers and any
XML in the modules in the current directory.
