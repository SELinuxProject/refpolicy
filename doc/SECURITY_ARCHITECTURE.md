# Reference Policy Security Architecture

## Type Architecture

On an SELinux system, every subject (a process, when acting) and object has an SELinux security
context which identifies the object's security attributes. Policy rules authorize interactions
between a source context and a target context for specific object classes and permissions. Access
is denied unless the loaded policy allows it and all applicable constraints are satisfied.

Type Enforcement (TE) is SELinux's primary access-control mechanism, and TE rules make up most
of Reference Policy. Achieving the security goals depends on assigning and using policy types
carefully. In Reference Policy, types have the `_t` suffix by convention.

### Domains

A domain is a type applied to processes. All domains are also associated with the `domain`
attribute by convention. One or more processes may share a domain, which forms their logical
security boundary. Separate domains allow policy to grant each domain the rules required for its
function and limit the effect of compromise.

When naming domains, it normally corresponds to a service name or process name. For example, the
`sshd` service runs in the `sshd_t` domain.

A typical service has a domain type for its process and an executable type for its entry-point
program. A domain transition changes the process type when an authorized caller executes that
entry point. Interfaces such as `init_daemon_domain()` create the domain, associate its entry
point, authorize it for `system_r`, and establish the expected transition from init.

Reference Policy uses `neverallow` rules to prevent transitions to types that are not domains.

### Object Types

Object types, not to be confused with object classes, label anything other than processes. They
identify security purpose rather than pathname, owner, or discretionary mode. Object classes
distinguish files, directories, symbolic links, sockets, devices, filesystems, ports, nodes,
packets, and IPC objects that have the same type.

Types should separate objects with different readers, writers, trust levels, lifecycles, executers,
or transition behavior. An application/service may have additional types to support its security
goals. A service commonly has distinct types for executable code, configuration, persistent state,
logs, temporary data, and runtime objects. Network, device, filesystem, and IPC types similarly
distinguish resources that Linux discretionary access control may otherwise treat alike.

### Type Attributes

Type attributes are type sets that share a security property. Core examples include `domain`,
`file_type`, `exec_type`, and `port_type`. Rules and interfaces can target an attribute so the
same access applies consistently to all member types. Because a rule targeting an attribute
applies to every member type, broad attribute-based access is privileged and requires careful
review.

Attribute membership is security-relevant. Adding a type to an attribute grants every rule that
targets that attribute and can affect policy in multiple modules. Attributes should represent a
real shared property, and new membership should be reviewed for all resulting access rather than
treated as an organizational convenience.

### Module Ownership

The module that declares a type owns its definition and internal rules. Other modules should not
reference the type directly. They obtain access through public interfaces in the owning module.
This encapsulation lets the owner provide a complete access pattern and change implementation
details without coupling callers to private types.

Templates may declare related types for each caller or instance. The template's module owns the
implementation of these types, while the caller supplies an instance-specific prefix or domain.
Interfaces and templates should expose one security concept and should not add unrelated access
for convenience.

### Derived Types

Reference Policy uses strong naming conventions to aid policy management and understanding. For
objects related to a domain, common type names are derived by adding a suffix to the domain's base
name:

| Generic type       | Derived type                              | Access | Purpose                             |
| ------------------ | ----------------------------------------- | ------ | ----------------------------------- |
| `bin_t`            | `*_exec_t`                                | RO     | Entry-point executable              |
| `etc_t`            | `*_conf_t`, `*_config_t`, or `*_etc_t`    | RO     | Private configuration               |
| `initrc_exec_t`    | `*_initrc_exec_t`                         | RO     | SysV init script                    |
| `var_cache_t`      | `*_cache_t` or `*_var_cache_t`            | RW     | Private cache                       |
| `var_lib_t`        | `*_state_t` or `*_var_lib_t`              | RW     | Private persistent state            |
| `var_lock_t`       | `*_lock_t` or `*_var_lock_t`              | RW     | Private lock data                   |
| `var_log_t`        | `*_log_t` or `*_var_log_t`                | RW     | Private logs                        |
| `var_run_t`        | `*_runtime_t`                             | RW     | Private runtime data                |
| `systemd_unit_t`   | `*_unit_t`                                | RO     | systemd units                       |
| `tmp_t`            | `*_tmp_t`                                 | RW     | Private temporary data              |
| `tmpfs_t`          | `*_tmpfs_t`                               | RW     | Private tmpfs or shared-memory data |

The domain's base name replaces `*`. For example, log files for `sshd_t` would normally use
`sshd_log_t`. The **Access** column describes the domain's typical access: **RO** is read-only and
**RW** is read-write. Actual permissions remain defined by policy and may differ when a service's
function requires it.

## Role Architecture

Reference Policy uses SELinux role-based access control to constrain which process domains an
SELinux user may enter. The process's role limits which domain types are available to that user.

The authorization path is:

1. A Linux account is mapped to an SELinux user and their MLS or MCS range, which can be different,
   but not exceed, the range authorized for the SELinux user.
2. The SELinux user is authorized for a set of roles and an MLS or MCS range.
3. Each role is authorized for a set of domain types.
4. Role and domain transitions determine how a process may enter another authorized role or
   domain.

Authorization at one layer does not bypass the next. A Linux UID, an SELinux user, or a role does
not itself grant access to objects. The process must run in an authorized domain, and that domain
must have the required Type Enforcement permissions and satisfy applicable constraints.

### System Role

`system_r` is the role for system services and non-interactive system processes. Service-domain
interfaces generally authorize their domains for `system_r`. Init and other trusted system domains
perform controlled transitions into those service domains.

The `system_u` SELinux identity is associated with system processes and objects and should not be
mapped to an ordinary Linux user. Although many service domains share `system_r`, their type fields
remain distinct and enforce separation between services.

### Login Roles

Login roles provide interactive user environments. Userdomain templates create each role's base
domain and related types for terminals, home content, temporary files, and application domains.
The principal login-role patterns are:

- `user_r` for ordinary unprivileged users;
- `staff_r` for unprivileged routine activity by users who are be authorized to transition to
  administrative roles;
- `sysadm_r` for broad system administration;
- `guest_r` and `xguest_r` for restricted login environments; and
- `unconfined_r`, when enabled, for an intentionally broad compatibility environment.

Users authorized for administrative roles should perform routine work in an unprivileged role,
normally `staff_r`, and enter an administrative role only through an explicit transition.

### Specialized Administrative Roles

Reference Policy provides narrower roles for selected administrative responsibilities, including
`auditadm_r`, `secadm_r`, `dbadm_r`, `logadm_r`, and `webadm_r`. Their modules authorize the role
for purpose-specific domains and interfaces. Deployments can map an SELinux user only to the roles
needed for that user's responsibilities.

Specialized roles reduce the need to use `sysadm_r` for every administrative task. Their security
value depends on keeping their domain permissions narrower than general system administration and
avoiding transition paths to unrelated administrative domains.

### Role Transitions

A role transition requires all relevant authorization: the SELinux user must be permitted to use
the target role, the target role must be permitted to use the target domain, and policy must allow
the process and entry-point transition, and the source role must be allowed to change to the
target role. Tools and domains for `newrole`, `sudo`, `su`, login, and similar mechanisms provide
controlled transition paths.

Role templates for applications authorize role-specific application domains without making those
domains available to every role. Optional modules and tunables may add transition paths, so each
configured policy must be reviewed as a whole.

Objects normally use `object_r` rather than an interactive or system process role. Object access
is primarily determined by type, while roles constrain process-domain selection. The SELinux user
identity and MLS or MCS ranges can further constrain object access.

## User Architecture

An SELinux user identity is a field of a security context and is distinct from a Linux account.
Login configuration maps Linux accounts to SELinux users. Each SELinux user declaration specifies
the roles it may enter, its default MLS or MCS level, and its authorized range or categories.

The core policy declares a small set of SELinux users. `system_u` is reserved for system processes
and objects and must not be assigned to an ordinary Linux user. `user_u` is the generic identity
for Linux accounts without a specific SELinux user mapping. `staff_u`, `sysadm_u`, and `root`
provide different sets of administrative roles and ranges. Deployments may define additional
SELinux users and map Linux accounts according to local responsibilities. In many cases, the
existing SELinux users are sufficient, and instead, the mapping of Linux user accounts to SELinux
users in a many-to-one pattern is the preferred method for managing a Linux user's SELinux user
and their MLS/MCS range (if enabled).

### User-Based Access Control

User-Based Access Control (UBAC) optionally uses the SELinux user identity as an additional access
control boundary. It is enabled by the `UBAC` build option and supplements type enforcement and
role authorization. UBAC does not use the Linux UID.

UBAC applies when both the source and target are UBAC-constrained types. Consequently, both types
must participate for UBAC to separate two non-system users. A UBAC-constrained type is a member of
the `ubac_constrained_type` attribute. User domain templates mark login domains and user-owned
types as UBAC-constrained, and other modules mark user-specific processes and objects where
appropriate.

UBAC constraints cover file and directory objects, selected process permissions, file
descriptors, sockets, SysV IPC, and other supported classes. Class-specific exemption attributes
permit designated domains to cross the user boundary where a system function requires it. For
example, separate attributes exempt file, process, file-descriptor, socket, and IPC access.

UBAC provides approximate separation between users that share the same roles and domain types.
Its effectiveness depends on complete attribute coverage, while `system_u` and explicit exemption
attributes are trusted to cross that boundary. Changes to UBAC membership or exemptions therefore
require review of the constraints and all rules inherited through the affected attributes.

## Multi-Category Security

Multi-Category Security (MCS) adds category-based separation when the policy is built with
`TYPE=mcs`. An MCS policy has one sensitivity, `s0`, and a configurable number of unordered
categories. A level consists of `s0` and zero or more categories, such as `s0:c0,c3`. A range has
a low and high level; the high level represents the subject's category clearance.

One MCS level dominates another when its category set is a superset of the category set of the
other level. For types in `mcs_constrained_type`, constraints generally require the subject's high
level to dominate the target's high level. The constraints cover relevant file, process, socket,
key, IPC, network, context, and SELinux-aware database permissions. Newly created or relabeled file
and database objects must be single-level and within the subject's clearance.

MCS constraints exempt access when the source type is not a member of `mcs_constrained_type`.
Interfaces mark domains such as containers and virtual machines as constrained and grant narrowly
scoped privilege to trusted domains that assign category sets to new processes. This supports
separation between workloads that otherwise use the same domain type, provided they receive
suitable category sets and all shared resources are labeled consistently.

Type Enforcement must authorize an operation before MCS category constraints are evaluated. MCS
can deny access based on category dominance, but it cannot grant access that Type Enforcement
denies.

## Multi-Level Security

Multi-Level Security (MLS) adds sensitivity and category enforcement when the policy is built with
`TYPE=mls`. Sensitivities are ordered from `s0` upward, while categories are unordered
compartments. An MLS level combines one sensitivity with a category set. A level dominates another
when its sensitivity is at least as high and its category set contains all categories of the other
level. A process or SELinux user range identifies its current or minimum level and its clearance.

MLS constraints supplement Type Enforcement across files, processes, filesystems, sockets,
network objects, IPC, keys, capabilities, and SELinux-aware databases. For ordinary file access,
the policy requires the process level to dominate the object level for read-like operations and
generally requires equal levels for write-like operations. Ordinary file objects are single-level.
Separate transition validation controls upgrades, downgrades, relabeling, and process range
changes.

Trusted attributes provide specific exceptions needed by system services. Interfaces can permit a
domain to read or write all levels, operate up to its clearance, relabel levels, change process
ranges, or treat an object as trusted. These attributes bypass portions of the MLS constraints and
must be limited to domains whose functions require cross-level operation.

MLS policy depends on correct ranges for SELinux users, roles, processes, and objects as well as
correct labeling of local and network resources. Type Enforcement authorization remains necessary:
MLS can reject an access allowed by Type Enforcement, but an MLS relationship cannot grant an
access that Type Enforcement denies. The effective decision is the intersection of both rule sets
and any other applicable constraints.
