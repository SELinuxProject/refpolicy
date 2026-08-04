# Files and Directories

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
