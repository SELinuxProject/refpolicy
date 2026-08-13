# Reference Policy Security Goals

## Purpose and Scope

This document defines the overall security goals of Reference Policy. These goals guide policy
architecture, module design, review, and validation. Individual deployments select modules, build
options, tunables, SELinux user mappings, and local policy; therefore, the goals must be evaluated
against each resulting policy configuration.

Reference Policy uses SELinux mandatory access control to complement, rather than replace, Linux
discretionary access control and application security. The policy seeks to limit the privilege and
impact of a compromised process. It does not guarantee that applications are free of defects or
that every supported configuration provides the same security properties.

## Integrity

Reference Policy aims to preserve the integrity of the processes and their data across the system.

- Domains should access only the objects required by their intended function.
- Security-relevant executables, configuration, libraries, credentials, logs, and state should be
  writable only by specifically authorized domains.
- Executable files and libraries should not be writable except by expected software-management or
  administrative domains. File types that are both writable and executable, especially from the
  same domain, are exceptional and explicitly reviewed.
- Domain transitions should occur only through intended entry points.
- File labels and other security contexts should be assigned and changed only through authorized
  paths.
- A compromise in one domain should not permit modification of unrelated domains or their objects.
- Policy extensions should preserve existing integrity boundaries and avoid granting access to
  unrelated domains for convenience.

The policy should apply least privilege to write, create, delete, relabel, transition, and
privilege-bearing permissions. Read access should also be limited when disclosure could enable an
integrity violation, such as access to credentials or security configuration.

### Data Separation

Reference Policy aims to separate each domain's files and other filesystem objects from data owned
by unrelated domains. A domain should access only the data required for its intended function,
even when discretionary permissions or a shared parent directory would otherwise permit access.

This separation is especially important in shared or generic locations such as `/tmp` and
`/var/lib`, where many domains create or discover objects. Policy should:

- assign application-specific types to temporary, persistent state, cache, spool, lock, and
  runtime objects;
- use type transitions, including name-based transitions where appropriate, so newly created
  objects receive the intended private type rather than a generic shared type;
- grant read, write, create, delete, rename, relabel, link, and directory-search permissions only
  to domains that need the data or administer its lifecycle;
- avoid broad access to generic shared-directory types when a purpose-specific type can express
  the requirement.

These boundaries protect integrity and limit cross-contamination between applications. They also
reduce opportunities for one domain to replace, redirect, pre-create, or remove another domain's
objects. For example, a domain should not be able to exploit a symbolic link or other substituted
object in a shared directory to cause a more privileged domain to read, write, relabel, or delete
an unintended target.

Shared cleanup, package-management, backup, and administrative domains may require access across
multiple data types. Such access should be limited to the operation being performed and should not
treat application data as generally shared.

### IPC Separation

Reference Policy aims to protect processes from unauthorized communication and to separate IPC
channels owned by unrelated domains. A domain should send data or control messages only through
mechanisms required for its intended function and only to expected domains or labeled endpoints.

Protected IPC mechanisms include:

- network sockets and associated ports, nodes, interfaces, packets, and labeled peers;
- Unix stream and datagram sockets, including their filesystem socket objects;
- D-Bus and other userspace object-manager communications;
- System V and POSIX message queues, shared memory, and semaphores;
- named and anonymous pipes; and
- process-to-process signaling, file-descriptor use, and other channels that transfer data or
  control between domains.

Policy should constrain both establishment and use of a channel. This includes permissions to
bind, connect, send, write, signal, and use or inherit communication objects. Creating or owning an
IPC object should not imply access to communicate with every domain that can access the
underlying system facility.

Where SELinux identifies both local peers, communication should be limited to the expected source
and target domain pair. Network communication should likewise be restricted using the labels
available for the connection, such as socket, port, node, interface, packet, and peer labels.
Broad access to generic ports, unlabeled traffic, all domains, or shared IPC types should be
avoided when a purpose-specific type and interface can express the required flow.

These boundaries protect receiving processes from malformed, unexpected, or malicious data
injected by unrelated domains.

### System Self-Protection

Reference Policy aims to protect the mechanisms and services on which policy enforcement depends.
Untrusted and ordinary application domains should not be able to disable, bypass, or redefine
SELinux enforcement. Binary executables, including shared libraries, kernel
image, and kernel modules should not be writable except by specified update
programs or package managers.

Protected state includes, but is not limited to:

- the SELinux policy, configuration, labeling rules, and policy sources installed on the system;
- kernel interfaces that control enforcement or expose security-sensitive state;
- authentication, authorization, audit, logging, and system initialization services;
- kernel image, kernel modules, executables, libraries, devices, and persistent state required by
  the trusted computing base; and
- highly privileged capabilities, such as `CAP_SYS_MODULE`, `CAP_SYS_ADMIN`, `CAP_SYS_RAWIO`, and
  `CAP_NET_ADMIN`.

Domains with this access should document the document the need in the policy.

## Confidentiality

Reference Policy aims to prevent domains from disclosing data to unauthorized processes, users,
or network endpoints. Domains should read only the objects required for their intended function,
and sensitive data should be available only to specifically authorized domains. This includes
credentials, keys, private user data, security configuration, audit records, application state,
and other data whose disclosure could harm the system or its users.

Confidentiality depends on purpose-specific types and narrowly scoped read, search, map, execute,
and metadata permissions. Access to generic or shared types should not provide an unintended path
to sensitive data. Administrative, backup, indexing, logging, and diagnostic domains that require
broad read access should receive only the access needed for their defined function.

### IPC Confidentiality

A domain should read or receive data over IPC only from the domains and labeled endpoints required
for its intended function. Policy should limit permissions to listen, accept, receive, read, and
use or inherit communication objects. This applies to the IPC mechanisms identified under IPC
separation, including sockets, D-Bus, message queues, shared memory, pipes, file descriptors,
signals that disclose process state, and labeled network traffic.

Where SELinux identifies both peers, receive-side access should be limited to the expected domain
pair. Network access should similarly use available socket, port, node, interface, packet, and peer
labels. Broad access to generic IPC types, unlabeled traffic, or all domains should be avoided when
a purpose-specific type and interface can express the required flow.

These controls should prevent a compromised process from reading another domain's communications
and from sending sensitive data to an unauthorized process or network endpoint. Authorization to
send data does not imply authorization to receive a reply. Bidirectional access should be granted
only when both directions are required.

### Multi-Level Security

Reference Policy optionally supports Multi-Level Security when built with `TYPE=mls`. MLS applies
mandatory confidentiality constraints in addition to Type Enforcement. Its sensitivity levels and
categories implement the Bell-LaPadula model with the strong star property for ordinary
information flows: a subject may read at its level or lower, but may write only at the same level.
This prevents reading information from a higher level and writing information to a different
level.

MLS constraints apply to files, processes, IPC, networking, and other supported object classes.
Explicitly trusted domains and objects may receive narrowly scoped exceptions for cross-level
operations such as logging, relabeling, administration, or trusted data transfer. These exceptions
are part of the confidentiality boundary and should be limited to functions that require them.

## Role and Privilege Separation

Reference Policy aims to separate ordinary user activity, administrative activity, and system
service activity. Possession of a Linux account or discretionary-access-control privilege should
not by itself grant unrestricted SELinux privilege.

- Ordinary users should operate in unprivileged roles and domains by default.
- Administrative privilege should be entered through explicit, authorized role and domain
  transitions.
- Users authorized for administrative roles should use an unprivileged role for routine activity.
- Administrative functions should be divided among purpose-specific domains and, where supported,
  roles rather than concentrated in a single general-purpose domain.
- Services should receive individual domains whose privileges are limited to their defined
  responsibilities.
- Capabilities, privileged device access, process control, relabeling, and policy administration
  should be granted independently and only where required.
- A process should change its own security context only when the transition is expected and
  constrained.
- Transitions must not provide a path for a less-privileged role or domain to acquire unauthorized
  privilege.

Role and privilege separation is strongest when unconfined domains are disabled and SELinux user
and role mappings are configured for the deployment. Configurations that enable unconfined access
or broad compatibility tunables intentionally weaken or remove separation goals and must be
considered accordingly.

## Automated Validation

The checks in `testing/sechecker.ini` enforce selected, repository-wide invariants against a
compiled policy containing all Reference Policy modules.

These checks use exemption lists to identify intentional privilege holders and policy patterns
that cannot satisfy a general assertion. An exemption is part of the security architecture, not
merely a way to silence a failure. If a policy change reasonably requires a permission that fails a
sechecker test, adding the domain or type to the applicable exemption list must include an inline
comment explaining why or how the permission is needed. Uncommented exemptions are not
acceptable. Obsolete exemptions should be removed. Prefer exempting individual types rather than
attributes so newly added types do not acquire an exemption unexpectedly.

The configuration is designed for the complete Reference Policy. When checking a policy built
from a subset of modules, absent exempt types do not cause failure. Review each exemption list and
remove entries not present in that policy to confirm a tighter baseline. Configurations without
unconfined domains should also remove exemptions that exist solely to accommodate unconfined
execution.

The automated checks cover only selected integrity and privilege-separation properties. Passing
them does not establish all goals in this document or correctness of every allowed access.

## Review Criteria

Policy changes should be reviewed against these questions:

1. Does the change grant a domain privilege beyond its documented function?
2. Can the change modify policy, enforcement state, trusted code, security configuration, labels,
   credentials, audit data, or another domain's state?
3. Does the change create a new privilege transition, and are its source, entry point, and target
   sufficiently constrained?
4. Does the change add new privilege to the domain? If so, can a domain transition provide a
   narrower use of this privilege?
5. Could an unprivileged user, role, or compromised service use the change to gain administrative
   or unrelated service privilege?
6. Is an existing interface available that expresses the intended access? If not, does it add a
   new interface without exposing a module's implementation details?
7. Are optional features, tunables, and distribution-specific rules bounded so configurations that
   do not select them retain their existing protections?
8. Do policy build, analysis, and semantic-difference results match the intended security effect?
9. Does the change grant a checked permission or capability to a new domain, or require a new
   sechecker exemption? If so, is the privilege necessary and narrowly justified by an inline
   comment on the exemption that explains why or how the permission is needed?
10. Does the change make executable content writable, make writable content executable, or broaden
    an existing executable-integrity exemption?
11. Does the change allow a domain to access another domain's data or generic objects in a shared
    directory? If so, can a private type, type transition, or narrower interface prevent
    cross-domain access or object-substitution attacks?
12. Does the change create or broaden an IPC path? Are the source, target, direction, mechanism,
    and labeled network endpoints limited to those required, and could the path permit data
    injection or exfiltration involving an unrelated domain?

When functionality conflicts with these goals, the required security tradeoff should be explicit,
limited to the affected configuration, and documented close to the policy decision.
