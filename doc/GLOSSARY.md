# Glossary

## Bell-LaPadula Model

A mandatory access control model intended to preserve [confidentiality](#confidentiality) by
controlling information flow between security levels. Its basic rules prevent a
[subject](#subject) from reading information at a higher level and from writing information to a
lower level. Reference Policy can optionally apply a Bell-LaPadula-style model through
[Multi-Level Security](#multi-level-security-mls).

## Confidentiality

The property that information is not disclosed to unauthorized [subjects](#subject). In SELinux,
policy can protect confidentiality by limiting read-like access to [objects](#object) and
receive-side access to communication channels.

## Context

See [Security context](#security-context).

## Derived Type

A Reference Policy naming convention in which the name of an object [type](#type) is formed from a
[domain's](#domain) base name and a suffix that identifies the object's purpose. For example,
`sshd_exec_t` and `sshd_log_t` are types derived from the `sshd` base name. A derived type has no
special meaning to SELinux solely because of its name.

## Domain

A process [type](#type) is an equivalence class or security boundary for one or more processes.
Processes in the same domain are governed by the same
[Type Enforcement](#type-enforcement-te) rules. In Reference Policy, domain types have the
`domain` attribute.

## Domain Transition

A change from one process [domain](#domain) to another when executing a file with an
[executable type](#executable-type). A transition requires policy permissions for the
source-to-target transition, execution of the [entrypoint](#entrypoint-type), and use of the
[executable](#executable-type) as an entrypoint to the target [domain](#domain).

A process may also explicitly request a change to another domain by using the
[setcon(3)](https://www.man7.org/linux/man-pages/man3/setcon.3.html) function. This requires
policy permissions to set the context of the process and the source-to-target dynamic transition.

See [Domain Transition](https://github.com/SELinuxProject/selinux-notebook/blob/main/src/domain_object_transitions.md#domain-transition)
in the SELinux Notebook for more detailed information.

## Entrypoint Type

An [executable type](#executable-type) through which a process may enter a [domain](#domain). See
[domain transition](#domain-transition) for more information.

## Executable Type

The [type](#type) of an executable file. An executable type used to enter another
[domain](#domain) is an [entrypoint type](#entrypoint-type).

## Integrity

The property that data, code, processes, and security state are in a good state and not
modified or controlled by unauthorized [subjects](#subject). SELinux cannot measure the integrity
of [objects](#object), but the policy protects integrity by limiting write accesses, privileged
operations, relabeling, and transitions.

## Label

See [Security context](#security-context).

## Multi-Category Security (MCS)

An optional SELinux policy configuration that uses unordered categories to separate
[subjects](#subject) and [objects](#object). A [subject](#subject) has access to an
[object](#object) if its category set dominates the category set of the object.  In SELinux, MCS
further restricts access that [Type Enforcement](#type-enforcement-te) allows. It cannot allow
access on its own. Reference Policy enables MCS with `TYPE=mcs`.

## Multi-Level Security (MLS)

An optional SELinux policy configuration that implements the
[Bell-LaPadula model](#bell-lapadula-model) with the [strong star property](#strong-star-property).
In SELinux, MLS further restricts access that [Type Enforcement](#type-enforcement-te) allows. It
cannot allow access on its own. Reference Policy enables MLS with `TYPE=mls`.

## Object

A resource accessed by a [subject](#subject) and managed by an SELinux-aware object manager.
Objects are passive entities, such as files, directories, and sockets. Processes are considered
objects when they are acted upon.

## Role

The role component of an SELinux [security context](#security-context). This is used in the
[Role-Based Access Control](#role-based-access-control-rbac) decisions.

## Role-Based Access Control (RBAC)

An access control model in which authorizes [roles](#role) for sets of [domain](#domain) types. It
controls which domains an [SELinux user](#selinux-user-seuser) may enter and controls role changes.
[Objects](#object) normally use the special `object_r` role. In SELinux, RBAC further restricts
access that [Type Enforcement](#type-enforcement-te) allows. It cannot allow access on its own.

## Security Context

The security attribute associated with an SELinux [subject](#subject) or [object](#object). A
security context has the form `user:role:type[:range]`, where the optional range is present in
[MCS](#multi-category-security-mcs) and [MLS](#multi-level-security-mls) policies. A security
context is also called a context or label.

## SELinux User (seuser)

The user-identity component of an SELinux [security context](#security-context). An SELinux user is
distinct from a Linux account; login configuration maps Linux accounts to SELinux users. An
SELinux user is authorized for a set of [roles](#role) and, for
[MCS](#multi-category-security-mcs) or [MLS](#multi-level-security-mls) policy, a range.

## Strong Star Property

A [Bell-LaPadula](#bell-lapadula-model) [confidentiality](#confidentiality) property that permits a
[subject](#subject) to write an [object](#object) only when the subject and object have the same
security level. This is stricter than the basic star property, which permits writing at the same
or a higher level.

## Subject

An active entity that initiates access to an [object](#object): a process.

## Trusted Computing Base (TCB)

The collection of hardware, firmware, software, and security mechanisms whose correct operation is
required to enforce the system's security policy. A failure or compromise of the TCB can violate
the system's [integrity](#integrity) or [confidentiality](#confidentiality), regardless of the
controls applied to components outside the TCB.

## Type

The component of a [security context](#security-context) used by
[Type Enforcement](#type-enforcement-te). A type identifies the security purpose of a
[subject](#subject) or [object](#object). Type names conventionally end in `_t`.

## Type Enforcement (TE)

SELinux's primary mandatory access control mechanism. Type Enforcement rules authorize specified
permissions for interactions between a source [type](#type) and a target type of a particular
object class. Other constraints, including [user](#selinux-user-seuser), [role](#role),
[MCS](#multi-category-security-mcs), and [MLS](#multi-level-security-mls) constraints, may further
restrict authorized access.
