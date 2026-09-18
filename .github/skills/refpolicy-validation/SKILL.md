---
name: refpolicy-validation
description: >-
  Validate changes to SELinux Reference Policy policy sources, support tools, Python, Markdown,
  file contexts, build configuration, or generated behavior. Use after any repository change and
  before reporting completion.
---

# Reference Policy Validation

Select and run the smallest sufficient validation set, then escalate according to the changed
surface.

## Establish Current Requirements

Before selecting commands:

1. Inspect the changed files and classify them.
2. Read the relevant current files under `.github/workflows/`, especially:
   - `tests.yml` for job ordering, dependencies, and which matrix each job actually uses.
   - `global-vars.yml` for dependency minimums and build matrices.
   - `lint-policy.yml` for lint commands and exclusions.
   - `build-policy.yml` for build ordering, variables, and validation.
   - `validate-policy.yml` for `sechecker`.
   - `diff-policy.yml` for semantic comparison.
3. Consult `doc/BUILD_INSTALL.md` for applicable local build requirements.
4. If CI configuration, repository documentation, this skill, or the requested command disagree,
   report the exact conflict and ask the user which source to follow. Do not silently adapt a
   command.

Do not treat an untested assumption or a missing command on `PATH` as sufficient reason to skip
validation. Attempt the selected check first. If it fails because a dependency is missing, install
or restore that dependency when permitted; otherwise, report the exact blocker. Do not install
tooling before a selected validation command demonstrates that it is missing.

## Classify the Change

Treat these as policy source:

- `.te`, `.if`, and `.fc` files.
- Policy support macros.
- Global booleans and tunables.
- Users, constraints, MCS, and MLS policy.
- Security classes, access vectors, and common permission sets.
- Policy build configuration.

Also identify changes to Python support tools, tests, Markdown, workflows, and build machinery.

## Validation Levels

Apply all levels whose conditions match:

1. **Targeted check:** always run the narrowest command that exercises the changed source.
2. **Policy validation:** required for policy-source changes when the SELinux toolchain is
   available.
3. **Semantic review:** apply the `refpolicy-semantic-review` workflow whenever compiled behavior
   may change.

## Targeted Checks

Generate prerequisites before policy linting:

```sh
make conf
make generate
```

For `.fc` changes, run:

```sh
python3 -t -t -E -W error testing/check_fc_files.py
```

For policy-source changes, run the current SELint command and exclusions from `lint-policy.yml`.

For Python changes, run the narrowest relevant script or test with warnings treated as errors
before broader validation.

For Markdown changes, run:

```sh
npx --yes markdownlint-cli2 --config testing/refpolicy.markdownlint.json "**/*.md"
```

Also verify that referenced repository paths exist and links resolve.

For spelling-sensitive source or documentation changes, run the current `codespell` command from
`lint-policy.yml`.

## Policy Validation

Build configuration is controlled by `build.conf` and Make variables. `make bare` removes
generated configuration, so run `make conf` afterward.

For targeted policy validation, derive the build ordering, options, and `WERROR` setting from the
current `build-policy.yml` and applicable repository documentation. Select an MCS/systemd
configuration unless the change requires another configuration. When changes affect confinement
assumptions, also validate a configuration without unconfined applications. Do not rely on build
commands copied into this skill.

Use the current CI matrix rather than copying stale matrix values into commands. A complete CI
equivalent includes all non-excluded combinations defined by `global-vars.yml` and the build,
lint, validation, documentation, and installation steps wired by `tests.yml`. Note that `tests.yml`
builds every configuration in the full `build-matrix`, but only validates and diffs the reduced
`analysis-matrix`; do not conflate the two when claiming CI-equivalent coverage.

## Generated Output

Use repository Make targets to generate output:

- `make generate` creates generated corenetwork policy sources.
- `make conf` updates generated policy configuration.
- `make xml` and `make html` generate policy documentation.

Inspect generated behavior where relevant, but do not commit ignored generated artifacts.

## Report

Report:

- Changed-file classification.
- Each command run and its pass or fail result.
- The highest completed validation level.
- Checks that could not run and the exact reason.
- Whether failures are caused by the change, pre-existing state, or the environment.
- Missing SETools or comparable policy artifacts as an incomplete semantic review.
