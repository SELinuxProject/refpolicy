# AGENTS.md

Guidance for automated coding agents working in the SELinux Reference Policy repository.

## Repository Layout

See `doc/REPO_LAYOUT.md` for repository paths and generated-file descriptions.

## Documentation

- Use the [SELinux Notebook](https://github.com/SELinuxProject/selinux-notebook/tree/main/src) as
  the most authoritative reference for general SELinux concepts, behavior, policy languages, object
  classes and permissions, tools, and configuration.
- For Reference Policy, treat this repository and its documentation as authoritative. Use the
  SELinux Notebook as the next reference when this repository does not answer the question.
- If the SELinux Notebook does not answer the question, consult the upstream SELinux userspace
  man pages under `https://github.com/SELinuxProject/selinux/*/man/**` for further information.
- Read `README.md` for the project overview and goals.
- Read `doc/WHITEPAPER.md` for the original Reference Policy design concepts and historical
  context.
- Use `doc/SECURITY_GOALS.md` when evaluating the intended security effects of policy changes.
- Read `doc/BUILD_INSTALL.md` for make targets, build options, and header-based module builds.
- Read `doc/GETTING_STARTED.md` for the module structure and development workflow.
- Follow `doc/STYLE_GUIDE.md` for ordering declarations, local rules, interfaces, and
  file-context entries.
- Follow `doc/INTERFACE_NAMING.md` when adding or renaming public interfaces and templates.
- See `doc/HOW_TO_CONTRIBUTE.md` for contribution, patch submission, and sign-off requirements.
- Read `doc/USE_REFPOLICY.md` when changing installation or migration workflows.
- Format Markdown documentation with a maximum line length of 100 columns. Preformatted code
  blocks and Markdown tables may exceed this limit.
- Align Markdown table cells and delimiters so tables are readable in the source text.
- Use spaces for indentation in Markdown documentation; do not use tabs.
- Avoid using the term `authorize` and its variants when `permission`, `access`, or `privilege`
  (or their variants) will work.
- Do not edit generated documentation such as `doc/policy.xml` or files under `doc/tmp/` and
  `doc/html/` directly.

## Evidence and Uncertainty

- Inspect the relevant current code before answering questions or making changes.
- Read the applicable specifications and authoritative documentation; do not infer requirements
  from code alone when a specification governs the behavior.
- Fetch web references directly from their authoritative source. Do not rely on cached web search
  results, summaries, or snippets.
- Do not make unsupported assumptions or speculate when evidence is unavailable. If the code and
  authoritative references do not determine the answer, or if they conflict, state the uncertainty
  and ask the user a clarifying question before proceeding.

## Working Practices

- Keep changes focused on the requested policy module or build tool. Do not reformat unrelated
  policy.
- Follow `doc/STYLE_GUIDE.md` and the ordering of neighboring modules in the same layer.
- Prefer existing interfaces over direct `allow` rules against types owned by another module. Add
  or extend an interface in the owning module when necessary.
- Name new interfaces and templates according to `doc/INTERFACE_NAMING.md`.
- Keep type declarations and local rules in `.te`, reusable public interfaces in `.if`, and path
  labeling expressions in `.fc`.
- Preserve optional-policy and tunable boundaries used by nearby rules.
- Do not edit generated files such as `policy.conf`, `file_contexts`, `homedir_template`,
  `policy.xml`, or files under `tmp/`. Change their source and regenerate them.
- Change `policy/modules/kernel/corenetwork.te.in`, `corenetwork.if.in`, or `corenetwork.if.m4`
  instead of the generated `corenetwork.te` and `corenetwork.if` files.
- New Python code requires Python 3.10 or newer and should match the existing support-tool style.
- If any constraints files are modified, revalidate the entire file, including revalidating
  if explicit perimssion exemptions are still valid. The following are constraints files:
  `policy/constraints`, `policy/mls`, and `policy/mcs`.
- Any time an object class is added or modified, either permissions changed, or a change
  to the common permission set it inherits, update the constraints files accordingly.

## Building and Validation

Build configuration is controlled by `build.conf` and make variables. `make bare` removes
generated configuration; run `make conf` before validation after using it.

Before running a validation command, re-read the relevant current files under
`.github/workflows/`. Confirm the command, flags, ordering, environment variables, and reusable
workflow inputs still match the form documented here. If CI, this guide, other repository
documentation, or the requested command are inconsistent, do not choose one or adapt the command
without evidence. State the inconsistency and ask the user how to proceed.

The CI minimums are Python 3.10, SELinux userspace 3.9, SETools/sechecker 4.5, and SELint 1.5.0.
CI sets `WERROR=y` and builds combinations of Red Hat, Debian, and Gentoo configuration; standard,
MCS, and MLS policy; modular and monolithic policy; systemd and direct-init configurations; and
policy with and without unconfined applications. See `.github/workflows/global-vars.yml` for the
current matrix and exclusions.

For a targeted MCS/systemd policy build:

```sh
make bare && make conf && make MONOLITHIC=y TYPE=mcs SYSTEMD=y WERROR=y validate
```

For the stricter profile without unconfined domains:

```sh
make bare && make conf && make MONOLITHIC=y TYPE=mcs APPS_OFF=unconfined SYSTEMD=y WERROR=y validate
```

Run the narrowest relevant check first when changing a support tool or test. A full `validate`
build is expected for policy changes when the required SELinux toolchain is available. Build
requirements and CI dependency versions are defined in `.github/workflows/global-vars.yml`.

### Change-Specific Checks

- Before policy linting, generate required sources and configuration with `make conf` followed by
  `make generate`.
- For `.fc` changes, run the file-context checker after generation:

  ```sh
  python3 -t -t -E -W error testing/check_fc_files.py
  ```

- For policy source changes, run SELint after generation with the same exclusions as CI:

  ```sh
  selint --source --recursive --summary --fail --disable C-005 --disable C-008 --disable W-005 policy
  ```

- For spelling-sensitive source or documentation changes, run the CI codespell command:

  ```sh
  codespell --skip Changelog,Changelog.contrib,Changelog.old --ignore-words-list busses,chage,doesnt,lik,msdos,nd,racoon,shouldnt,startd,te,thats,xwindows --context 1 .
  ```

- For Python changes, run the narrowest relevant script or test with warnings treated as errors
  before broader policy validation.
- For Markdown changes, run the repository configuration and resolve all diagnostics:

  ```sh
  npx --yes markdownlint-cli2 --config testing/refpolicy.markdownlint.json "**/*.md"
  ```

  The configuration enforces the 100-column prose limit, aligned tables, and prohibition on hard
  tabs. Also verify that referenced local paths exist and links resolve.

### Generated Outputs

- `make generate` creates the generated corenetwork policy sources.
- `make conf` updates `policy/modules.conf` and `policy/booleans.conf` and depends on generated
  `doc/policy.xml` data.
- `make xml` regenerates `doc/policy.xml`; `make html` regenerates `doc/html/`.
- Generated policy, configuration, XML, HTML, and `tmp/` outputs are ignored build artifacts. Do
  not commit them.

### Semantic Review

- SETools is required for semantic review of policy changes.
- Build base and changed policy artifacts and review `sediff` output for policy behavior changes.
- Run `sechecker testing/sechecker.ini` against the changed compiled policy.
- If a reasonable permission grant fails a sechecker test, a new exemption must include an inline
  comment explaining why or how the domain needs the permission.
- Treat semantic differences and security-goal failures as results to explain, not output to
  suppress.

## Change Hygiene

- Review generated policy differences when a policy build changes behavior.
- Include related `.te`, `.if`, and `.fc` updates in the same change when they form one policy
  feature.
- Keep each commit to one logical change and ensure the tree builds after each commit.
- Include a `Signed-off-by` line using the contributor's real name in every commit.
- Do not commit generated build artifacts.
- Submit changes through a GitHub pull request as described in `doc/HOW_TO_CONTRIBUTE.md`.

## Reporting Results

- Report the validation commands run and whether each passed or failed.
- State which checks were skipped and why, including missing tools or unavailable policy
  artifacts. For policy changes, report missing SETools or policy artifacts as an incomplete
  semantic review rather than a skipped optional check.
- Distinguish failures caused by the change from unrelated failures already present in the
  worktree or environment.
