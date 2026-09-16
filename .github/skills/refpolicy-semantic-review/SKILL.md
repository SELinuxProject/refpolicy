---
name: refpolicy-semantic-review
description: >-
  Compare base and changed compiled SELinux Reference Policy behavior. Use for changes that may
  alter permissions, transitions, attributes, roles, labels, booleans, tunables, constraints, or
  other compiled policy behavior.
---

# Reference Policy Semantic Review

Review the actual compiled-policy effect rather than relying only on source inspection.

## Establish Comparable Inputs

1. Read `.github/workflows/tests.yml`, `global-vars.yml`, `build-policy.yml`, `diff-policy.yml`,
   and `validate-policy.yml`.
2. Record the base revision, changed revision, and every build option. For a CI-equivalent
   comparison, note that `tests.yml` diffs the pull request's `github.base_ref` build against the
   changed-branch build, not an arbitrary prior commit.
3. Select configurations that exercise the change. Use the current analysis matrix for a
   CI-equivalent review; `tests.yml` shows this is a reduced subset of the full build matrix.
4. Build base and changed artifacts with identical toolchains and options.
5. Do not alter or discard the user's current worktree to build the baseline. Use existing CI
   artifacts or a separate, specifically named temporary worktree.
6. Remove any temporary worktree and associated temporary artifacts after the comparison unless
   the user asks to retain them.

If equivalent base and changed artifacts cannot be produced, report the review as incomplete and
identify the missing artifact or tool.

## Build Artifacts

Follow the ordering and environment in the current `build-policy.yml`:

1. Remove stale generated configuration with `make bare` when starting from a previous build.
2. Run `make conf`.
3. Build the policy with the selected configuration and `WERROR=y`.
4. Run `make validate`.
5. Locate the resulting binary policy using the Makefile targets used by current CI; do not assume
   a fixed output path.

Keep the base and changed policies under distinct, explicit paths.

## Compare Behavior

Run:

```sh
sediff BASE_POLICY CHANGED_POLICY
```

Review the complete output. Categorize each semantic difference, including:

- Added or removed allow rules and type transitions.
- Attribute membership changes and their indirect effects.
- Role and user changes.
- Boolean, tunable, and conditional-policy changes.
- Labeling and file-context changes.
- Constraint, MLS, and MCS effects.

Trace unexpected differences back to their source. Do not suppress or dismiss differences merely
because the policy compiles.

## Check Security Goals

Run the current `sechecker` command from `validate-policy.yml` against the changed compiled policy.

Evaluate results against `doc/SECURITY_GOALS.md`.

If a necessary permission grant fails a `sechecker` test, any new exemption must have an inline
comment explaining why the domain needs the permission. Do not add unexplained exemptions or
weaken checks to obtain a passing result.

## Report

Report:

- Base and changed revisions.
- Tool versions and complete build configurations.
- Artifact paths or CI artifact names.
- Expected semantic differences and why each is intended.
- Unexpected differences, even if later corrected.
- `sechecker` results and any exemptions.
- Missing tools or artifacts as an incomplete semantic review.
