---
name: refpolicy-constraints-change
description: >-
  Review and validate SELinux Reference Policy class, permission, common permission set,
  constraint, MLS, and MCS changes. Use for direct or inherited permission changes and any edit to
  policy/constraints, policy/mls, policy/mcs, or policy/flask security class or access-vector
  definitions.
---

# Reference Policy Constraints Change

Constraint and permission changes can affect policy globally. Review the complete affected
surface, including inherited permissions and existing exemptions.

## Triggering Files and Changes

Use this workflow for changes to:

- `policy/constraints`
- `policy/mls`
- `policy/mcs`
- `policy/flask/security_classes`
- `policy/flask/access_vectors`
- Any common permission set or class inheritance relationship.
- Any object-class permission, including a change made indirectly through a common set.

## Determine the Impact

1. Read the relevant security-class and access-vector definitions.
2. Identify every changed class, permission, common permission set, and inheritance relationship.
3. Expand common permission changes to every inheriting object class.
4. Search all three constraint files for affected classes and permissions.
5. Read `doc/SECURITY_GOALS.md`, `doc/SECURITY_ARCHITECTURE.md`, and applicable SELinux Notebook
   material before deciding the intended constraint behavior. Consult `doc/GLOSSARY.md` for term
   definitions (e.g., subject, object, domain) when the intended semantics are ambiguous.
6. Inspect policy sources and tests that rely on explicit permission exemptions.

Do not assume an existing constraint remains correct because its text did not change.

## Update Constraints

For every affected class and permission:

1. Determine whether existing constraints cover the new semantics.
2. Update all applicable constraint expressions.
3. Preserve distinctions among standard, MCS, and MLS policy.
4. Reassess every explicit permission exemption in each modified constraint file.
5. Remove exemptions that are no longer needed.
6. Explain any new exemption inline, including why the domain requires it.

Do not broaden a constraint merely to make a build or `sechecker` result pass.

## Validate

Apply the `refpolicy-validation` and `refpolicy-semantic-review` workflows.

At minimum:

- Revalidate each complete modified constraint file, not just edited expressions.
- Build standard, MCS, and MLS policy where the change can affect them.
- Exercise every inheriting class when a common permission set changes.
- Run the current CI-equivalent matrix for class, permission, common-set, or shared constraint
  changes.
- Review `sediff` for direct and indirect permission changes.
- Run `sechecker testing/sechecker.ini` against each applicable changed policy artifact.

## Report

List:

- Changed and transitively affected classes and permissions.
- Constraint files and expressions reviewed.
- Exemptions retained, added, or removed, with reasons.
- Configurations built.
- Semantic differences and security-goal results.
- Any incomplete validation caused by unavailable tools or artifacts.
