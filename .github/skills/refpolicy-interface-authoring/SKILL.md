---
name: refpolicy-interface-authoring
description: >-
  Add, rename, extend, or review SELinux Reference Policy public interfaces and templates in .if
  files. Use for interface naming, placement, documentation, ownership, parameters, and caller
  compatibility.
---

# Reference Policy Interface Authoring

Create interfaces only when they provide a reusable policy abstraction or access pattern.

## Research Existing Policy

Before editing:

1. Read `doc/STYLE_GUIDE.md` and `doc/INTERFACE_NAMING.md`.
2. Read the owning module's `.te`, `.if`, and `.fc` files.
3. Search the repository for interfaces with the same concept, target type or attribute, access
   level, and object class.
4. Search for all callers of an interface before renaming it or changing its behavior.
5. Inspect neighboring interfaces in the same section for documentation, `gen_require`, parameter,
   and ordering conventions.

Prefer an existing interface. Do not add a public interface solely to avoid a simple internal rule
within the owning module.

## Ownership and Boundaries

- Put reusable public interfaces and templates in the `.if` file of the module that owns the
  target type or attribute.
- Prefer calls to owning-module interfaces over direct rules against foreign types.
- Preserve optional-policy, tunable-policy, and build-option boundaries at call sites.
- Keep declarations and local rules in `.te` and path labeling expressions in `.fc`.

## Naming and Placement

Follow the `modulename[_modifier]_verb_predicate()` convention.

Organize `.if` files in this order:

1. Templates.
2. Transform interfaces.
3. Access interfaces.
4. Administrative interfaces.
5. Unconfined interface.

Within access interfaces, sort by primary object type or attribute, then by increasing access:

`getattr`, `setattr`, `read`, `append`, `write`, `rw`, `create`, `rename`, `delete`, `manage`,
`relabelto`, `relabelfrom`, `relabel`.

Place an allow interface before its matching `dontaudit` interface. Put a module-wide
administrative interface after component-specific administrative interfaces.

## Implementation

- Use established policy patterns and permission sets rather than spelling out equivalent raw
  rules.
- Include only required symbols in `gen_require`.
- Keep parameter names, ordering, and documentation consistent with their use.
- Document the access granted and each parameter using the neighboring XML documentation style;
  use `doc/example.if` as the canonical reference when neighboring interfaces are inconsistent or
  under-documented.
- State notable side effects, implied permissions, domain transitions, or incompatibilities in
  the description.
- Avoid granting more access than the interface name and documentation promise.
- When changing an existing interface, inspect every caller for compatibility and unintended
  privilege expansion.

## Validate

Apply the `refpolicy-validation` workflow. Apply the `refpolicy-semantic-review` workflow when the
interface is called by policy or its compiled behavior changes.

Verify:

- Naming and ordering against the authoritative guides.
- Documentation and parameters against the implementation.
- All existing callers after a rename or behavior change.
- Generated policy output, without committing generated artifacts.

Report whether the interface is new or changed, why an existing interface was insufficient, which
callers were reviewed, and the validation results.
